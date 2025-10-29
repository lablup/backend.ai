import enum


class FsType(enum.StrEnum):
    XFS = "XFS"
    LINUX_LVM = "LINUX_LVM"
    EXT4 = "EXT4"
    THIRD_PARTY = "THIRD_PARTY"
