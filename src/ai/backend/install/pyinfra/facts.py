"""
Custom PyInfra facts for Backend.AI deployment.

This module contains reusable custom facts that can be used across
different deployment modules to gather information from remote hosts.
"""

from pyinfra.api import FactBase


class FileContent(FactBase):
    """
    Custom PyInfra fact to read file content from remote host.

    This fact executes a cat command on the remote host and returns
    the file content as a string. Returns None if the file doesn't exist
    or is empty.

    Example:
        content = host.get_fact(FileContent, path="/etc/myfile.conf")
    """

    def command(self, path: str) -> str:
        return f"cat {path} 2>/dev/null || echo ''"

    def process(self, output: list[str]) -> str | None:
        # Return the raw file content as string
        return "\n".join(output) if output else None
