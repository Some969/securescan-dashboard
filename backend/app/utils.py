import ipaddress
import os
import socket
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from fastapi import HTTPException

REQUEST_TIMEOUT = int(os.getenv("SECURESCAN_REQUEST_TIMEOUT", "8"))

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

    hostname = parsed.hostname.strip().lower()
    ensure_public_hostname(hostname)

    # Keep path/query if provided, but remove fragments because they are never sent to servers.
    cleaned = parsed._replace(fragment="")
    if cleaned.path == "":
        cleaned = cleaned._replace(path="/")
    return urlunparse(cleaned)


def ensure_public_hostname(hostname: str) -> None:
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
        resolved = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        raise HTTPException(status_code=400, detail="Could not resolve the target hostname.")

    for result in resolved:
        ip_text = result[4][0]
        try:
            ip_obj = ipaddress.ip_address(ip_text)
        except ValueError:
            raise HTTPException(status_code=400, detail="Hostname resolved to an invalid IP address.")
        if _is_blocked_ip(ip_obj):
            raise HTTPException(status_code=400, detail="Target resolves to a private, local, or metadata IP address.")


def _is_blocked_ip(ip_obj: ipaddress._BaseAddress) -> bool:
    return (
        ip_obj.is_private
        or ip_obj.is_loopback
        or ip_obj.is_link_local
        or ip_obj.is_multicast
        or ip_obj.is_reserved
        or ip_obj.is_unspecified
        or str(ip_obj) in BLOCKED_METADATA_IPS
    )



def safe_get(url: str, *, timeout: int = REQUEST_TIMEOUT, max_redirects: int = 5) -> requests.Response:
    """GET a URL while validating each redirect target to reduce SSRF risk."""
    current_url = normalize_url(url)
    history = []

    for _ in range(max_redirects + 1):
        response = requests.get(current_url, timeout=timeout, allow_redirects=False)

        if response.is_redirect or response.is_permanent_redirect:
            location = response.headers.get("Location")
            if not location:
                response.history = history
                return response

            next_url = urljoin(current_url, location)
            try:
                current_url = normalize_url(next_url)
            except HTTPException as exc:
                raise requests.RequestException(f"Blocked unsafe redirect target: {exc.detail}") from exc

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
