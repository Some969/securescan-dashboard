from typing import Dict, List


HEADER_GUIDANCE: Dict[str, Dict[str, str]] = {
    "Content-Security-Policy": {
        "explanation": "Controls which sources are allowed to load scripts, styles, images, and other resources.",
        "recommendation": "Add a strict Content-Security-Policy header to reduce cross-site scripting and content injection risk.",
    },
    "Strict-Transport-Security": {
        "explanation": "Tells browsers to always use HTTPS for the domain after the first secure visit.",
        "recommendation": "Enable HSTS after confirming HTTPS works correctly across the whole site.",
    },
    "X-Frame-Options": {
        "explanation": "Helps prevent clickjacking by controlling whether the site can be framed.",
        "recommendation": "Use X-Frame-Options: DENY or SAMEORIGIN unless framing is required.",
    },
    "X-Content-Type-Options": {
        "explanation": "Prevents browsers from MIME-sniffing responses away from the declared content type.",
        "recommendation": "Set X-Content-Type-Options: nosniff on HTTP responses.",
    },
    "Referrer-Policy": {
        "explanation": "Controls how much referrer information is sent when users navigate away from the site.",
        "recommendation": "Use a privacy-aware policy such as strict-origin-when-cross-origin.",
    },
    "Permissions-Policy": {
        "explanation": "Restricts browser features such as camera, microphone, geolocation, and payment APIs.",
        "recommendation": "Add a Permissions-Policy header that disables features your site does not use.",
    },
}


def unique_recommendations(findings: List[dict]) -> List[str]:
    seen = set()
    output = []
    for finding in findings:
        recommendation = finding.get("recommendation")
        if recommendation and recommendation not in seen:
            seen.add(recommendation)
            output.append(recommendation)
    return output
