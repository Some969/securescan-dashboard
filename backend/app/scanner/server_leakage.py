from typing import Dict, List

import requests

from app.utils import REQUEST_TIMEOUT, safe_get

EXPOSED_HEADERS = ["Server", "X-Powered-By", "X-AspNet-Version", "X-Generator"]


def check_server_leakage(target_url: str) -> Dict:
    findings: List[dict] = []
    exposed = []

    try:
        response = safe_get(target_url, timeout=REQUEST_TIMEOUT)
        headers = response.headers
    except requests.RequestException as exc:
        return {
            "ok": False,
            "error": f"Could not fetch server headers: {exc}",
            "exposed_headers": exposed,
            "findings": findings,
        }

    normalized_headers = {key.lower(): value for key, value in headers.items()}

    for header in EXPOSED_HEADERS:
        value = normalized_headers.get(header.lower())
        if not value:
            continue

        severity = _risk_for_header(header, value)
        exposed.append({"name": header, "value": value, "severity": severity})
        findings.append({
            "title": f"Exposed {header} header",
            "description": f"The response exposes '{header}: {value}'. This may reveal server or framework details to attackers.",
            "severity": severity,
            "affected_component": "Information Disclosure",
            "recommendation": "Hide unnecessary server/framework version headers at the web server, reverse proxy, or application layer.",
        })

    return {
        "ok": True,
        "exposed_headers": exposed,
        "findings": findings,
    }


def _risk_for_header(header: str, value: str) -> str:
    value_has_version = any(char.isdigit() for char in value)
    if header.lower() in {"x-powered-by", "x-aspnet-version"}:
        return "medium"
    if header.lower() == "server" and value_has_version:
        return "medium"
    return "low"
