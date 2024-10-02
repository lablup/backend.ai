from pathlib import Path

__version__ = (Path(__file__).parent / "VERSION").read_text().strip()

user_agent = f"Backend.AI Gateway Server {__version__}"
