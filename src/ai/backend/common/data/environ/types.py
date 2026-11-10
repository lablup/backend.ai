"""The shape of an environment variable name shared by every environ table."""

from typing import Final

__all__ = ("ENVIRON_KEY_PATTERN",)

# A POSIX shell variable name (IEEE Std 1003.1 "Name"): a letter or underscore followed
# by letters, digits and underscores. Also the SQL regex of each environ table's CHECK.
ENVIRON_KEY_PATTERN: Final = r"^[A-Za-z_][A-Za-z0-9_]*$"
