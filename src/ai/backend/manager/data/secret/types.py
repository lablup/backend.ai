"""
Secret encryption identifiers.

The provider type says which provider reads a stored secret; the key id selects one
key within that provider.
"""

import enum
from typing import NewType

# The id of one key encryption key within a provider. Provider-defined, so it may carry
# whatever shape that provider names its keys with.
SecretKeyId = NewType("SecretKeyId", str)

# A key encryption key as configured: base64-encoded raw bytes.
SecretKeyMaterial = NewType("SecretKeyMaterial", str)


class KeyProviderType(enum.StrEnum):
    """
    The key providers this build knows.

    ``PLAIN`` is a write target rather than a reader: it stores secrets unencrypted, and
    a stored value never names it because plaintext carries no marker.
    """

    PLAIN = "plain"
    CONFIG = "config"
