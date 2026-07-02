from typing import Dict, List
from urllib.parse import urlparse, urlunparse

import requests

from app.utils import REQUEST_TIMEOUT, safe_get


def check_https_redirect(target_url: str) -> Dict:
    findings: List[dict] = []
    parsed = urlparse(target_url)
    hostname = parsed.hostname or ""
    netloc = hostname
    if parsed.port and parsed.port not in {80, 443}:
        netloc = f"{hostname}:{parsed.port}"

    http_url = urlunparse(("http", netloc, parsed.path or "/", "", parsed.query, ""))

    try:
        response = safe_get(http_url, timeout=REQUEST_TIMEOUT)
        final_url = response.url
        redirects_to_https = final_url.lower().startswith("https://")
        history = [
            {"status_code": item.status_code, "url": item.url}
            for item in response.history
        ]

        if not redirects_to_https:
            findings.append({
                "title": "HTTP does not redirect to HTTPS",
                "description": "The HTTP version of the site did not end on a secure HTTPS URL.",
                "severity": "medium",
                "affected_component": "HTTP Redirects",
                "recommendation": "Configure a permanent 301/308 redirect from HTTP to HTTPS.",
            })

        return {
            "ok": True,
            "checked_url": http_url,
            "redirects_to_https": redirects_to_https,
            "final_url": final_url,
            "final_status_code": response.status_code,
            "redirect_chain": history,
            "findings": findings,
        }

    except requests.RequestException as exc:
        return {
            "ok": False,
            "checked_url": http_url,
            "redirects_to_https": False,
            "final_url": None,
            "error": f"Could not check HTTP redirect: {exc}",
            "findings": findings,
        }
