from pathlib import Path

from . import exceptions, session

__all__: tuple[str, ...] = (
    *exceptions.__all__,
    *session.__all__,
)

__version__ = (Path(__file__).parent / "VERSION").read_text().strip()


def get_user_agent() -> str:
    return f"Backend.AI Client for Python {__version__}"
