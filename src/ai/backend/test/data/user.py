from dataclasses import dataclass


@dataclass
class CreatedUserMeta:
    username: str
    password: str
    email: str
    access_key: str
    secret_key: str
