"""
Temporenc, a comprehensive binary encoding format for dates and times
"""

__version__ = '0.1.0'
__version_info__ = tuple(map(int, __version__.split('.')))


# Export public API
from .temporenc import (  # noqa
    pack,
    packb,
    unpack,
    unpackb,
    Moment,
)
