from pathlib import Path

__version__ = (Path(__file__).parent.parent / "VERSION").read_text().strip()
