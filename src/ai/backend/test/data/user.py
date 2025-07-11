from dataclasses import dataclass


@dataclass
class CreatedUserMeta:
    email: str
    password: str
    access_key: str
    secret_key: str
