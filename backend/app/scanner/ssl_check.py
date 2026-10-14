import socket
import ssl
from datetime import datetime, timezone
from typing import Dict, List
from urllib.parse import urlparse

from fastapi import HTTPException

from app.utils import REQUEST_TIMEOUT, hostname_from_url, resolve_public_addresses, scheme_from_url


def _format_issuer(cert: dict) -> str:
    issuer_parts = []
    for item in cert.get("issuer", []):
        for key, value in item:
            issuer_parts.append(f"{key}={value}")
    return ", ".join(issuer_parts) if issuer_parts else "Unknown"


def check_ssl(target_url: str) -> Dict:
    findings: List[dict] = []
    parsed = urlparse(target_url)
    hostname = hostname_from_url(target_url)
    scheme = scheme_from_url(target_url)
    port = parsed.port or (443 if scheme == "https" else 80)

    result = {
        "ok": False,
        "https_enabled": scheme == "https",
        "certificate_valid": False,
        "issuer": None,
        "expires_at": None,
        "days_left": None,
        "port": port,
        "error": None,
        "findings": findings,
    }

    if scheme != "https":
        findings.append({
            "title": "HTTPS is not enabled on the submitted URL",
            "description": "The URL was scanned using HTTP instead of HTTPS.",
            "severity": "high",
            "affected_component": "SSL/TLS",
            "recommendation": "Serve the site over HTTPS and redirect all HTTP traffic to HTTPS.",
        })
        return result

    try:
        destination_ip = resolve_public_addresses(hostname)[0]
    except HTTPException:
        result["error"] = "TLS destination failed public-network validation."
        return result

    try:
        context = ssl.create_default_context()
        with socket.create_connection((destination_ip, port), timeout=REQUEST_TIMEOUT) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as secure_sock:
                cert = secure_sock.getpeercert()

        if not cert:
            raise ssl.SSLError("No certificate returned by the server.")

        not_after = cert.get("notAfter")
        if not_after:
            expiry_ts = ssl.cert_time_to_seconds(not_after)
            expiry_date = datetime.fromtimestamp(expiry_ts, tz=timezone.utc)
            now = datetime.now(timezone.utc)
            days_left = (expiry_date - now).days

            result["expires_at"] = expiry_date.isoformat()
            result["days_left"] = days_left

            if days_left < 0:
                findings.append({
                    "title": "SSL/TLS certificate has expired",
                    "description": "The certificate expiry date is in the past.",
                    "severity": "critical",
                    "affected_component": "SSL/TLS",
                    "recommendation": "Renew and install a valid TLS certificate immediately.",
                })
            elif days_left <= 14:
                findings.append({
                    "title": "SSL/TLS certificate expires soon",
                    "description": f"The certificate expires in {days_left} day(s).",
                    "severity": "medium",
                    "affected_component": "SSL/TLS",
                    "recommendation": "Renew the TLS certificate before it expires to avoid browser warnings.",
                })

        result["issuer"] = _format_issuer(cert)
        result["certificate_valid"] = True
        result["ok"] = True
        return result

    except ssl.SSLError as exc:
        result["error"] = f"SSL validation failed: {exc}"
        findings.append({
            "title": "SSL/TLS validation failed",
            "description": "The TLS certificate could not be validated by the scanner.",
            "severity": "high",
            "affected_component": "SSL/TLS",
            "recommendation": "Install a valid certificate from a trusted certificate authority and check the certificate chain.",
        })
    except (socket.timeout, OSError) as exc:
        result["error"] = f"Could not connect to HTTPS service: {exc}"
        findings.append({
            "title": "HTTPS service could not be reached",
            "description": f"The scanner could not connect to port {port} for TLS validation.",
            "severity": "high",
            "affected_component": "SSL/TLS",
            "recommendation": "Confirm that HTTPS is enabled, reachable, and correctly configured.",
        })

    return result
