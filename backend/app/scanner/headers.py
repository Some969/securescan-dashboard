from typing import Dict, List

import requests

from app.scanner.recommendations import HEADER_GUIDANCE
from app.utils import REQUEST_TIMEOUT, safe_get

REQUIRED_HEADERS = [
    "Content-Security-Policy",
    "Strict-Transport-Security",
    "X-Frame-Options",
    "X-Content-Type-Options",
    "Referrer-Policy",
    "Permissions-Policy",
]

HEADER_SEVERITY = {
    "Content-Security-Policy": "medium",
    "Strict-Transport-Security": "medium",
    "X-Frame-Options": "low",
    "X-Content-Type-Options": "low",
    "Referrer-Policy": "low",
    "Permissions-Policy": "low",
}


def check_security_headers(target_url: str) -> Dict:
    findings: List[dict] = []
    present = []
    missing = []

    try:
        response = safe_get(target_url, timeout=REQUEST_TIMEOUT)
        headers = response.headers
    except requests.RequestException as exc:
        return {
            "ok": False,
            "error": f"Could not fetch headers: {exc}",
            "present": present,
            "missing": REQUIRED_HEADERS,
            "findings": findings,
        }

    normalized_headers = {key.lower(): value for key, value in headers.items()}

    for header in REQUIRED_HEADERS:
        info = HEADER_GUIDANCE[header]
        value = normalized_headers.get(header.lower())
        if value:
            present.append({
                "name": header,
                "value": value,
                "explanation": info["explanation"],
            })
        else:
            missing.append({
                "name": header,
                "explanation": info["explanation"],
                "recommendation": info["recommendation"],
            })
            findings.append({
                "title": f"Missing {header}",
                "description": f"The website does not define the {header} security header. {info['explanation']}",
                "severity": HEADER_SEVERITY[header],
                "affected_component": "HTTP Headers",
                "recommendation": info["recommendation"],
            })

    return {
        "ok": True,
        "status_code": response.status_code,
        "present": present,
        "missing": missing,
        "findings": findings,
    }
