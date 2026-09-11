def normalize_newlines(text: str) -> str:
    """Convert CRLF to LF, preserving standalone CR and trailing whitespace."""
    return text.replace("\r\n", "\n")
