"""
Common definitions/constants used throughout the manager.
"""

import enum
import platform
import re
from typing import Final

from ai.backend.common.docker import arch_name_aliases
from ai.backend.common.types import SlotName, SlotTypes

INTRINSIC_SLOTS: Final = {
    SlotName('cpu'): SlotTypes('count'),
    SlotName('mem'): SlotTypes('bytes'),
}

MANAGER_ARCH = platform.machine().lower().strip()


DEFAULT_IMAGE_ARCH = arch_name_aliases.get(MANAGER_ARCH, MANAGER_ARCH)
# DEFAULT_IMAGE_ARCH = 'x86_64'

# The default container role name for multi-container sessions
DEFAULT_ROLE: Final = "main"

_RESERVED_VFOLDER_PATTERNS = [r'^\.[a-z0-9]+rc$', r'^\.[a-z0-9]+_profile$']
RESERVED_DOTFILES = ['.terminfo', '.jupyter', '.ssh', '.ssh/authorized_keys', '.local', '.config']
RESERVED_VFOLDERS = ['.terminfo', '.jupyter', '.tmux.conf', '.ssh', '/bin', '/boot', '/dev', '/etc',
                     '/lib', '/lib64', '/media', '/mnt', '/opt', '/proc', '/root', '/run', '/sbin',
                     '/srv', '/sys', '/tmp', '/usr', '/var', '/home']
RESERVED_VFOLDER_PATTERNS = [re.compile(x) for x in _RESERVED_VFOLDER_PATTERNS]

# Redis database IDs depending on purposes
REDIS_STAT_DB: Final = 0
REDIS_RLIM_DB: Final = 1
REDIS_LIVE_DB: Final = 2
REDIS_IMAGE_DB: Final = 3
REDIS_STREAM_DB: Final = 4


# The unique identifiers for distributed locks.
# To be used with PostgreSQL advisory locks, the values are defined as integers.
class LockID(enum.IntEnum):
    LOCKID_TEST = 42
    LOCKID_SCHEDULE = 91
    LOCKID_PREPARE = 92
    LOCKID_SCHEDULE_TIMER = 191
    LOCKID_PREPARE_TIMER = 192
    LOCKID_LOG_CLEANUP_TIMER = 195
    LOCKID_IDLE_CHECK_TIMER = 196
