"""Prompt Injection and Adversarial Content Guardrails for Aegis Squad."""

import re
from typing import List, Tuple

# Common prompt injection signatures and attack vectors
INJECTION_SIGNATURES = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior)\s+rules",
    r"system\s+(prompt|override|message)\s*:",
    r"do\s+not\s+file\s+(a\s+)?sar",
    r"close\s+(this\s+)?(case|alert)\s+as\s+(benign|false\s+positive|clean)",
    r"you\s+are\s+now\s+(an?\s+)?unrestricted",
    r"bypass\s+(all\s+)?compliance",
    r"mark\s+(this\s+)?account\s+as\s+(low\s+risk|whitelisted|trusted)",
]


class GuardrailViolationError(Exception):
    """Raised when an adversarial injection attempt is detected."""
    pass


def scan_for_prompt_injection(text: str) -> Tuple[bool, List[str]]:
    """Scan untrusted input for prompt injection attack patterns.
    
    Returns:
        (is_hostile, list_of_detected_patterns)
    """
    detected: List[str] = []
    lower_text = text.lower()

    for pattern in INJECTION_SIGNATURES:
        match = re.search(pattern, lower_text)
        if match:
            detected.append(match.group(0))

    is_hostile = len(detected) > 0
    return is_hostile, detected


def sanitize_input(text: str) -> str:
    """Neutralize and sanitize untrusted transaction memo text."""
    is_hostile, detected = scan_for_prompt_injection(text)
    if is_hostile:
        sanitized = text
        for d in detected:
            sanitized = re.sub(re.escape(d), "[NEUTRALIZED_PROMPT_INJECTION_ATTEMPT]", sanitized, flags=re.IGNORECASE)
        return sanitized
    return text
