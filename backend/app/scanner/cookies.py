import re
from typing import Dict, List

import requests

from app.utils import REQUEST_TIMEOUT, safe_get


def check_cookies(target_url: str) -> Dict:
    try:
        response = safe_get(target_url, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as exc:
        return {
            "ok": False,
            "error": f"Could not inspect cookies: {exc}",
            "findings": [],
        }

    try:
        return {
            "ok": True,
            **inspect_cookies_from_response(response),
            "findings": build_cookie_findings(inspect_cookies_from_response(response)),
        }
    except Exception as exc:  # pragma: no cover - defensive fallback
        return {
            "ok": False,
            "error": f"Cookie parsing failed: {exc}",
            "findings": [],
        }


def inspect_cookies_from_response(response) -> Dict:
    cookie_headers = _extract_cookie_headers(response)
    if not cookie_headers:
        return {
            "cookies_found": 0,
            "status": "No cookies detected.",
        }

    results: List[dict] = []
    for header in cookie_headers:
        parsed = _parse_cookie_header(header)
        results.append(parsed)

    summary = {
        "missing_secure": sum(1 for item in results if not item.get("secure", False)),
        "missing_httponly": sum(1 for item in results if not item.get("httponly", False)),
        "missing_samesite": sum(1 for item in results if not item.get("samesite")),
    }

    return {
        "cookies_found": len(results),
        "results": results,
        "summary": summary,
    }


def build_cookie_findings(cookie_payload: Dict) -> List[dict]:
    if cookie_payload.get("error"):
        return []
    if cookie_payload.get("cookies_found", 0) == 0:
        return []

    findings: List[dict] = []
    for item in cookie_payload.get("results", []):
        if not item.get("secure", False):
            findings.append({
                "title": "Missing Secure flag",
                "description": f"The cookie {item.get('name', 'unknown')} does not set the Secure attribute.",
                "severity": "medium",
                "affected_component": "Cookie Security",
                "recommendation": "Enable Secure cookie flag.",
            })

        if not item.get("httponly", False):
            findings.append({
                "title": "Missing HttpOnly",
                "description": f"The cookie {item.get('name', 'unknown')} is accessible to JavaScript.",
                "severity": "medium",
                "affected_component": "Cookie Security",
                "recommendation": "Enable HttpOnly.",
            })

        if not item.get("samesite"):
            findings.append({
                "title": "Missing SameSite",
                "description": f"The cookie {item.get('name', 'unknown')} does not declare a SameSite policy.",
                "severity": "low",
                "affected_component": "Cookie Security",
                "recommendation": "Configure SameSite=Lax or Strict.",
            })

        if not item.get("expires"):
            findings.append({
                "title": "Cookie without expiration",
                "description": f"The cookie {item.get('name', 'unknown')} does not define an expiration date.",
                "severity": "info",
                "affected_component": "Cookie Security",
                "recommendation": "Review session lifetime.",
            })

    return findings


def _extract_cookie_headers(response) -> List[str]:
    headers = getattr(response, "headers", None)
    raw_headers = getattr(response, "raw", None)

    extracted: List[str] = []

    if raw_headers is not None:
        try:
            values = raw_headers.headers.getlist("Set-Cookie")
            if values:
                extracted.extend(values)
        except Exception:  # pragma: no cover - defensive fallback
            pass

    if headers is not None:
        try:
            values = headers.get("Set-Cookie") or headers.get("set-cookie")
            if values:
                if isinstance(values, list):
                    extracted.extend(values)
                else:
                    extracted.append(values)
        except Exception:  # pragma: no cover - defensive fallback
            pass

    return extracted


def _parse_cookie_header(header: str) -> Dict:
    parts = [part.strip() for part in header.split(";") if part.strip()]
    if not parts:
        return {
            "name": "",
            "secure": False,
            "httponly": False,
            "samesite": None,
            "expires": "",
            "domain": "",
            "path": "/",
        }

    name_value = parts[0].split("=", 1)
    name = name_value[0].strip() if name_value else ""
    value = name_value[1].strip() if len(name_value) > 1 else ""
    if not name and not value:
        return {
            "name": "",
            "secure": False,
            "httponly": False,
            "samesite": None,
            "expires": "",
            "domain": "",
            "path": "/",
        }

    secure = any(part.lower() == "secure" for part in parts[1:])
    httponly = any(part.lower() == "httponly" for part in parts[1:])
    samesite = None
    expires = ""
    domain = ""
    path = "/"

    for part in parts[1:]:
        lower_part = part.lower()
        if lower_part.startswith("samesite="):
            samesite = part.split("=", 1)[1].strip()
        elif lower_part.startswith("expires="):
            expires = part.split("=", 1)[1].strip()
        elif lower_part.startswith("domain="):
            domain = part.split("=", 1)[1].strip()
        elif lower_part.startswith("path="):
            path = part.split("=", 1)[1].strip()

    return {
        "name": name,
        "secure": secure,
        "httponly": httponly,
        "samesite": samesite,
        "expires": expires,
        "domain": domain,
        "path": path,
    }
