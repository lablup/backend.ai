from pathlib import Path

__version__ = (Path(__file__).parent / "VERSION").read_text().strip()

user_agent = f"Backend.AI Web Server {__version__}"
