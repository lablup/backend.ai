from dataclasses import dataclass
from pathlib import Path


@dataclass
class CGroupInfo:
    cgroup_path: Path
    version: str
