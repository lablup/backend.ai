from collections.abc import Iterable

import jwt
from pydantic import ValidationError

from ..exception import AuthorizationFailed
from ..types import AccessTokenPayload, IDTokenPayload

DEFAULT_ALGORITHM = "HS256"


def encode_id_token(
    payload: IDTokenPayload,
    *,
    secret: str,
    algorithm: str | None = None,
) -> str:
    _algorithm = algorithm if algorithm is not None else DEFAULT_ALGORITHM
    return jwt.encode(payload.model_dump(mode="json"), secret, algorithm=_algorithm)


def decode_id_token(
    token: str,
    *,
    secret: str,
    algorithms: Iterable[str] | None = None,
) -> IDTokenPayload:
    _algorithms = [*algorithms] if algorithms is not None else [DEFAULT_ALGORITHM]
    try:
        raw_data = jwt.decode(token, secret, algorithms=_algorithms)
        return IDTokenPayload(**raw_data)
    except (jwt.exceptions.InvalidSignatureError, ValidationError) as e:
        raise AuthorizationFailed(e)


def encode_access_token(
    payload: AccessTokenPayload,
    *,
    secret: str,
    algorithm: str | None = None,
) -> str:
    _algorithm = algorithm if algorithm is not None else DEFAULT_ALGORITHM
    return jwt.encode(payload.model_dump(mode="json"), secret, algorithm=_algorithm)


def decode_access_token(
    token: str,
    *,
    secret: str,
    algorithms: Iterable[str] | None = None,
) -> AccessTokenPayload:
    _algorithms = [*algorithms] if algorithms is not None else [DEFAULT_ALGORITHM]
    try:
        raw_data = jwt.decode(token, secret, algorithms=_algorithms)
        return AccessTokenPayload(**raw_data)
    except (jwt.exceptions.InvalidSignatureError, ValidationError) as e:
        raise AuthorizationFailed(e)


def get_id_token_from_hdrs(
    auth_hdr: str,
    secret: str,
) -> IDTokenPayload:
    # "Authorization: Bearer <TOKEN>"
    _, _, token = auth_hdr.partition(" ")
    return decode_id_token(token, secret=secret)


def get_access_token_from_hdrs(
    auth_hdr: str,
    secret: str,
) -> AccessTokenPayload:
    # "Authorization: Bearer <TOKEN>"
    _, _, token = auth_hdr.partition(" ")
    return decode_access_token(token, secret=secret)


def is_auth_by_token(auth_hdr: str | None) -> bool:
    if auth_hdr is None:
        return False
    return auth_hdr.startswith("Bearer ")
