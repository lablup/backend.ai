from pathlib import Path


def shorten_path(p: Path) -> Path:
    return "~" / p.relative_to(Path.home())
