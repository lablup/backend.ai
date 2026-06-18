import re
import unicodedata
import uuid
from collections.abc import Container

from ai.backend.common.types import Subdomain

__all__ = [
    "SubdomainGenerator",
]

# RFC 1123 DNS label: only [a-z0-9-], at most 63 characters, no leading or
# trailing hyphen. A wildcard certificate (``*.example.com``) only covers a
# single label, so a subdomain must never contain a dot.
_DNS_LABEL_MAX_LENGTH = 63
_LETTER_DIGIT_HYPHEN_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789-")
_HYPHEN_RUN = re.compile(r"-{2,}")
# Length reserved for a "-<8 hex>" uniqueness suffix so the suffixed form still
# fits within the DNS label limit.
_UNIQUE_SUFFIX_LENGTH = 9
_FALLBACK_PREFIX = "app"


class SubdomainGenerator:
    """Generate a DNS-label-safe, collision-free wildcard subdomain from an
    arbitrary deployment/app name.

    Subdomain allocation is solely the coordinator's responsibility; workers
    consume the resulting string verbatim for routing.
    """

    def generate_subdomain(
        self, preferred: Subdomain | None, taken: Container[Subdomain]
    ) -> Subdomain:
        if preferred is None:
            candidate = self._fallback_subdomain()
        else:
            candidate = self._normalize(preferred)
        if not candidate:
            candidate = self._fallback_subdomain()
        if candidate not in taken:
            return candidate
        trimmed = candidate[: _DNS_LABEL_MAX_LENGTH - _UNIQUE_SUFFIX_LENGTH].strip("-")
        prefix = trimmed or _FALLBACK_PREFIX
        while True:
            candidate = Subdomain(f"{prefix}{self._unique_suffix()}")
            if candidate not in taken:
                return candidate

    def _normalize(self, raw: Subdomain) -> Subdomain:
        """Convert ``raw`` into a single DNS label usable as a wildcard subdomain.

        - Lowercased and Unicode-normalized (NFC).
        - ``.`` and any other character invalid in a DNS label are replaced with
          ``-`` so they cannot introduce extra domain levels and fall outside
          the wildcard certificate.
        - Non-ASCII characters (e.g. Korean) are Punycode-encoded (the IDNA
          ``xn--`` form) so the result stays within a single ASCII label.
        - Trimmed to 63 characters with no leading or trailing hyphen.

        Returns an empty string when nothing usable remains; in that case
        :meth:`generate_subdomain` falls back to a generated label.
        """
        text = unicodedata.normalize("NFC", raw).strip().lower().replace(".", "-")
        # Replace ASCII characters that are invalid in a DNS label with "-",
        # while keeping non-ASCII characters so they can be Punycode-encoded.
        text = "".join(
            ch if (ch in _LETTER_DIGIT_HYPHEN_CHARS or ord(ch) >= 0x80) else "-" for ch in text
        )
        if text.isascii():
            final = _HYPHEN_RUN.sub("-", text)
        else:
            # Punycode keeps every character within one ASCII label.
            final = "xn--" + text.encode("punycode").decode("ascii")
        return Subdomain(final[:_DNS_LABEL_MAX_LENGTH].strip("-"))

    def _fallback_subdomain(self) -> Subdomain:
        """Generate a fallback subdomain when the preferred value is unusable."""
        return Subdomain(f"{_FALLBACK_PREFIX}{self._unique_suffix()}")

    def _unique_suffix(self) -> str:
        """Return a short unique suffix for a subdomain."""
        return f"-{uuid.uuid4().hex}"[:_UNIQUE_SUFFIX_LENGTH]
