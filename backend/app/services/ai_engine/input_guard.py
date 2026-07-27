import re

_MAX_INPUT_LENGTH = 4000

_INJECTION_PATTERNS = [
    r"ignore\s+(?:all\s+|the\s+|your\s+|previous\s+|above\s+|below\s+)*(?:instructions|prompt|context|system|rules)",
    r"disregard\s+(?:all\s+|the\s+|your\s+)*(?:instructions|prompt|context|system|rules)",
    r"forget\s+(?:all\s+|the\s+|your\s+)*(?:instructions|prompt|context|system|rules)",
    r"you\s+are\s+now\s+(?:a|an)",
    r"act\s+as\s+(?:if\s+you\s+are|a|an)",
    r"new\s+role\s*:",
    r"(?:override|bypass|disable)\s+(?:safety|security|restrictions|guidelines)",
    r"developer\s+mode",
    r"DAN\s*mode",
    r"jailbreak",
    r"system\s*:\s*",
    r"<\|im(?:_)?start\|>",
    r"<\|system\|>",
    r"\[\s*system\s*\]",
]

_INJECTION_RE = re.compile("|".join(f"({p})" for p in _INJECTION_PATTERNS), re.IGNORECASE)


def sanitize_input(text: str) -> str:
    """Normalize and strip user input for AI prompts."""
    if not isinstance(text, str):
        raise ValueError("Input must be a string")
    text = text.strip()
    if len(text) == 0:
        raise ValueError("Input cannot be empty")
    if len(text) > _MAX_INPUT_LENGTH:
        raise ValueError(f"Input exceeds maximum length of {_MAX_INPUT_LENGTH} characters")
    return text


def validate_input(text: str) -> str:
    """Validate input and raise a clear error if injection markers are found."""
    text = sanitize_input(text)
    match = _INJECTION_RE.search(text)
    if match:
        raise ValueError(
            f"Potentially unsafe input detected near: '{match.group(0)}'. "
            "Please rephrase without system-prompt or instruction-override language."
        )
    return text
