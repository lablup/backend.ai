import enum


class AllocationModes(str, enum.Enum):
    DISCRETE = "discrete"
    FRACTIONAL = "fractional"
