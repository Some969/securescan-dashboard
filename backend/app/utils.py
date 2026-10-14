import ipaddress
import os
import re
import socket
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from fastapi import HTTPException
from requests.adapters import HTTPAdapter
from urllib3 import PoolManager
from urllib3.connection import HTTPConnection, HTTPSConnection
from urllib3.connectionpool import HTTPConnectionPool, HTTPSConnectionPool
from urllib3.util.connection import create_connection

REQUEST_TIMEOUT = int(os.getenv("SECURESCAN_REQUEST_TIMEOUT", "8"))
MAX_RESPONSE_BYTES = 1_000_000
ALLOWED_PORTS = {"http": {80, 8080}, "https": {443, 8443}}

BLOCKED_HOSTNAMES = {"localhost", "localdomain"}
BLOCKED_METADATA_IPS = {"169.254.169.254"}


def normalize_url(raw_url: str) -> str:
    """Normalize user input into a safe public HTTP/HTTPS URL."""
    value = raw_url.strip()
    if not value:
        raise HTTPException(status_code=400, detail="Target URL is required.")

    if "://" not in value:
        value = f"https://{value}"

    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(status_code=400, detail="Only http and https URLs are supported.")
    if not parsed.hostname:
        raise HTTPException(status_code=400, detail="A valid hostname is required.")
    if parsed.username is not None or parsed.password is not None:
        raise HTTPException(status_code=400, detail="Credentials in target URLs are not allowed.")

    try:
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Target URL contains an invalid port.") from exc
    if port not in ALLOWED_PORTS[parsed.scheme]:
        raise HTTPException(status_code=400, detail="The target port is not allowed.")

    hostname = _normalize_hostname(parsed.hostname)
    ensure_public_hostname(hostname)

    netloc = f"[{hostname}]" if ":" in hostname else hostname
    if parsed.port is not None:
        netloc = f"{netloc}:{port}"
    cleaned = parsed._replace(netloc=netloc, path=parsed.path or "/", fragment="")
    return urlunparse(cleaned)


def ensure_public_hostname(hostname: str) -> None:
    if "%" in hostname:
        raise HTTPException(status_code=400, detail="Scoped IP addresses are not allowed.")
    if hostname in BLOCKED_HOSTNAMES or hostname.endswith(".localhost"):
        raise HTTPException(status_code=400, detail="Localhost and internal hosts are blocked.")

    try:
        ip_obj = ipaddress.ip_address(hostname)
        if _is_blocked_ip(ip_obj):
            raise HTTPException(status_code=400, detail="Private, local, and metadata IP ranges are blocked.")
        return
    except ValueError:
        pass

    try:
        resolve_public_addresses(hostname)
    except HTTPException:
        raise


def _is_blocked_ip(ip_obj: ipaddress._BaseAddress) -> bool:
    mapped_ipv4 = getattr(ip_obj, "ipv4_mapped", None)
    if mapped_ipv4 is not None:
        return _is_blocked_ip(mapped_ipv4)
    return not ip_obj.is_global or str(ip_obj) in BLOCKED_METADATA_IPS


def _normalize_hostname(hostname: str) -> str:
    value = hostname.strip().rstrip(".")
    if "%" in value:
        raise HTTPException(status_code=400, detail="Scoped IP addresses are not allowed.")
    try:
        return str(ipaddress.ip_address(value))
    except ValueError:
        pass

    try:
        ascii_hostname = value.encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise HTTPException(status_code=400, detail="A valid hostname is required.") from exc
    if not ascii_hostname or len(ascii_hostname) > 253:
        raise HTTPException(status_code=400, detail="A valid hostname is required.")
    labels = ascii_hostname.split(".")
    if any(
        not label
        or len(label) > 63
        or not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", label)
        for label in labels
    ):
        raise HTTPException(status_code=400, detail="A valid hostname is required.")
    return ascii_hostname


def resolve_public_addresses(hostname: str) -> list[str]:
    """Resolve a host once and reject the entire answer if any address is not public."""
    try:
        literal_ip = ipaddress.ip_address(hostname)
    except ValueError:
        try:
            answers = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
        except socket.gaierror as exc:
            raise HTTPException(status_code=400, detail="Could not resolve the target hostname.") from exc
        addresses = []
        for answer in answers:
            try:
                address_text = answer[4][0]
                if "%" in address_text:
                    raise ValueError("Scoped IP address.")
                addresses.append(str(ipaddress.ip_address(address_text)))
            except (IndexError, ValueError) as exc:
                raise HTTPException(status_code=400, detail="Hostname resolved to an invalid address.") from exc
    else:
        addresses = [str(literal_ip)]

    unique_addresses = list(dict.fromkeys(addresses))
    if not unique_addresses:
        raise HTTPException(status_code=400, detail="Could not resolve the target hostname.")
    if any(_is_blocked_ip(ipaddress.ip_address(address)) for address in unique_addresses):
        raise HTTPException(status_code=400, detail="Target must resolve only to public IP addresses.")
    return unique_addresses


class _PinnedConnectionMixin:
    def __init__(self, *args, pinned_ip: str, **kwargs):
        self._pinned_ip = pinned_ip
        super().__init__(*args, **kwargs)

    def _new_conn(self):
        return create_connection(
            (self._pinned_ip, self.port),
            self.timeout,
            source_address=self.source_address,
            socket_options=self.socket_options,
        )


class _PinnedHTTPConnection(_PinnedConnectionMixin, HTTPConnection):
    pass


class _PinnedHTTPSConnection(_PinnedConnectionMixin, HTTPSConnection):
    pass


class _PinnedHTTPConnectionPool(HTTPConnectionPool):
    ConnectionCls = _PinnedHTTPConnection


class _PinnedHTTPSConnectionPool(HTTPSConnectionPool):
    ConnectionCls = _PinnedHTTPSConnection


class _PinnedPoolManager(PoolManager):
    pool_classes_by_scheme = {
        "http": _PinnedHTTPConnectionPool,
        "https": _PinnedHTTPSConnectionPool,
    }

    def __init__(self, pinned_ip: str, **kwargs):
        self._pinned_ip = pinned_ip
        super().__init__(pinned_ip=pinned_ip, **kwargs)
        self.pool_classes_by_scheme = type(self).pool_classes_by_scheme

    def connection_from_context(self, request_context):
        context = request_context.copy()
        context.pop("pinned_ip", None)
        return super().connection_from_context(context)

    def _new_pool(self, scheme, host, port, request_context=None):
        context = dict(request_context or {})
        context["pinned_ip"] = self._pinned_ip
        return super()._new_pool(scheme, host, port, context)


class _PinnedHTTPAdapter(HTTPAdapter):
    def __init__(self, pinned_ip: str):
        self._pinned_ip = pinned_ip
        super().__init__(max_retries=0)

    def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):
        self.poolmanager = _PinnedPoolManager(
            pinned_ip=self._pinned_ip,
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            **pool_kwargs,
        )


def _request_pinned(url: str, pinned_ip: str, timeout: int) -> requests.Response:
    with requests.Session() as session:
        session.trust_env = False
        adapter = _PinnedHTTPAdapter(pinned_ip)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        response = session.get(
            url,
            timeout=(timeout, timeout),
            allow_redirects=False,
            stream=True,
        )

        if not (response.is_redirect or response.is_permanent_redirect):
            content = bytearray()
            try:
                for chunk in response.iter_content(chunk_size=64 * 1024):
                    content.extend(chunk)
                    if len(content) > MAX_RESPONSE_BYTES:
                        raise requests.RequestException("Target response exceeded the allowed size.")
            except requests.RequestException:
                response.close()
                raise
            response._content = bytes(content)
            response._content_consumed = True
        return response


def safe_get(url: str, *, timeout: int = REQUEST_TIMEOUT, max_redirects: int = 5) -> requests.Response:
    """GET a URL using a validated, pinned destination and revalidate each redirect."""
    current_url = normalize_url(url)
    history = []

    for _ in range(max_redirects + 1):
        parsed = urlparse(current_url)
        hostname = parsed.hostname
        if not hostname:
            raise requests.RequestException("Target URL has no hostname.")
        try:
            pinned_ip = resolve_public_addresses(hostname)[0]
        except HTTPException as exc:
            raise requests.RequestException("Target address failed public-network validation.") from exc

        response = _request_pinned(current_url, pinned_ip, timeout)

        if response.is_redirect or response.is_permanent_redirect:
            location = response.headers.get("Location")
            if not location:
                response.history = history
                return response

            next_url = urljoin(current_url, location)
            try:
                current_url = normalize_url(next_url)
            except HTTPException as exc:
                response.close()
                raise requests.RequestException("Blocked unsafe redirect target.") from exc

            response.close()
            history.append(response)
            continue

        response.history = history
        return response

    raise requests.RequestException("Too many redirects while fetching target.")


def hostname_from_url(target_url: str) -> str:
    parsed = urlparse(target_url)
    if not parsed.hostname:
        raise ValueError("Target URL does not contain a hostname.")
    return parsed.hostname.lower()


def scheme_from_url(target_url: str) -> str:
    return urlparse(target_url).scheme
