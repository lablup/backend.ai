from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Self

import jwt


class InvalidTokenError(Exception):
    pass


class TokenExpired(Exception):
    pass


@dataclass
class Token:
    sub: str  # user_id
    exp: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "sub": self.sub,
            "exp": self.exp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            sub=data["sub"],
            exp=data["exp"],
        )


class TokenParser:
    def __init__(self, secret: str, lifetime: int = 300) -> None:
        self._secret = secret
        self._algorithm = "HS256"
        self._lifetime = lifetime

    def set_secret(self, secret: str) -> None:
        self._secret = secret

    def set_lifetime(self, lifetime: int) -> None:
        self._lifetime = lifetime

    def serialize(self, user_id: str) -> str:
        now = datetime.now(UTC)
        expiration = now + timedelta(seconds=self._lifetime)
        return jwt.encode(
            Token(user_id, int(expiration.timestamp())).to_dict(),
            self._secret,
            algorithm=self._algorithm,
        )

    def deserialize(self, value: str) -> Token:
        try:
            val = jwt.decode(value, self._secret, algorithms=[self._algorithm])
        except jwt.ExpiredSignatureError:
            raise TokenExpired from None
        except (jwt.PyJWTError, jwt.exceptions.InvalidSignatureError):
            raise InvalidTokenError from None
        try:
            token = Token.from_dict(val)
        except KeyError:
            raise InvalidTokenError("Invalid token format") from None

        if token.exp < datetime.now(UTC).timestamp():
            raise TokenExpired
        return token
