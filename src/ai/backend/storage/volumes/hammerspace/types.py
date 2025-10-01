from dataclasses import dataclass


@dataclass
class ConnectionInfo:
    address: str
    username: str
    password: str
