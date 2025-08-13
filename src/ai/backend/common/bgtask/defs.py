# Default constants
DEFAULT_MAX_RETRIES = 3
DEFAULT_TTL_SECONDS = 86400  # 24 hours
DEFAULT_HEARTBEAT_INTERVAL = 600  # 10 minutes
DEFAULT_HEARTBEAT_THRESHOLD = 1800  # 30 minutes
DEFAULT_HEARTBEAT_TTL = 3600  # 1 hour


# Key prefixes for key-value storage
KEY_PREFIX = "bgtask"
TASK_KEY_PREFIX = f"{KEY_PREFIX}:task"  # bgtask:task:{task_id}
SERVER_GROUP_KEY_PREFIX = f"{KEY_PREFIX}:server_group"  # bgtask:server_group:{group}
SERVER_KEY_PREFIX = f"{KEY_PREFIX}:server"  # bgtask:server:{server_id}
HEARTBEAT_KEY_PREFIX = f"{KEY_PREFIX}:heartbeat"  # bgtask:heartbeat:{task_id}
