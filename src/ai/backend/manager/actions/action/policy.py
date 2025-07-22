import enum


class MultiEntityFailureHandlingPolicy(enum.StrEnum):
    ALL_OR_NONE = "all_or_none"
    PARTIAL_SUCCESS = "partial_success"
