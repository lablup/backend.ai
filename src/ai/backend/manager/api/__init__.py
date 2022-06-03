import enum


class ManagerStatus(str, enum.Enum):
    TERMINATED = 'terminated'  # deprecated
    PREPARING = 'preparing'    # deprecated
    RUNNING = 'running'
    FROZEN = 'frozen'
