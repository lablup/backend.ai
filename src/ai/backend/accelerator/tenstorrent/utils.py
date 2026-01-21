from pathlib import Path
from typing import Optional


def resolve_pci_sysfs_path(bus_id: str) -> Optional[str]:
    """
    Recursively searches /sys/devices for a directory whose basename
    matches the given PCI bus ID, returning the full path if found.

    Args:
        bus_id: PCI bus ID (e.g. '0000:01:00.0') to locate.

    Returns:
        Absolute path as a string if found, otherwise ``None``.
    """
    root = Path("/sys/devices")
    try:
        return str(next(root.glob(f"**/{bus_id}")))
    except StopIteration:
        return None
