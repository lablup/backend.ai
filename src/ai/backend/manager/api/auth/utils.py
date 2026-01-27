"""
Auth utility functions and timezone data for authentication.

This module provides:
- WHOIS timezone information for date parsing
- HMAC signature utilities
- IP validation utilities
- Auth parameter extraction
"""

from __future__ import annotations

import hashlib
import hmac
from collections.abc import Mapping
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Final
from urllib.parse import urlparse

from aiohttp import web
from dateutil.parser import parse as dtparse
from dateutil.tz import tzutc

from ai.backend.common.exception import InvalidIpAddressValue
from ai.backend.common.types import ReadableCIDR
from ai.backend.manager.errors.auth import (
    AuthorizationFailed,
    InvalidAuthParameters,
    InvalidClientIPConfig,
)

if TYPE_CHECKING:
    pass

__all__ = (
    "whois_timezone_info",
    "check_date",
    "sign_request",
    "validate_ip",
    "_extract_auth_params",
)

_whois_timezone_info: Final = {
    "A": 1 * 3600,
    "ACDT": 10.5 * 3600,
    "ACST": 9.5 * 3600,
    "ACT": -5 * 3600,
    "ACWST": 8.75 * 3600,
    "ADT": 4 * 3600,
    "AEDT": 11 * 3600,
    "AEST": 10 * 3600,
    "AET": 10 * 3600,
    "AFT": 4.5 * 3600,
    "AKDT": -8 * 3600,
    "AKST": -9 * 3600,
    "ALMT": 6 * 3600,
    "AMST": -3 * 3600,
    "AMT": -4 * 3600,
    "ANAST": 12 * 3600,
    "ANAT": 12 * 3600,
    "AQTT": 5 * 3600,
    "ART": -3 * 3600,
    "AST": 3 * 3600,
    "AT": -4 * 3600,
    "AWDT": 9 * 3600,
    "AWST": 8 * 3600,
    "AZOST": 0 * 3600,
    "AZOT": -1 * 3600,
    "AZST": 5 * 3600,
    "AZT": 4 * 3600,
    "AoE": -12 * 3600,
    "B": 2 * 3600,
    "BNT": 8 * 3600,
    "BOT": -4 * 3600,
    "BRST": -2 * 3600,
    "BRT": -3 * 3600,
    "BST": 6 * 3600,
    "BTT": 6 * 3600,
    "C": 3 * 3600,
    "CAST": 8 * 3600,
    "CAT": 2 * 3600,
    "CCT": 6.5 * 3600,
    "CDT": -5 * 3600,
    "CEST": 2 * 3600,
    "CET": 1 * 3600,
    "CHADT": 13.75 * 3600,
    "CHAST": 12.75 * 3600,
    "CHOST": 9 * 3600,
    "CHOT": 8 * 3600,
    "CHUT": 10 * 3600,
    "CIDST": -4 * 3600,
    "CIST": -5 * 3600,
    "CKT": -10 * 3600,
    "CLST": -3 * 3600,
    "CLT": -4 * 3600,
    "COT": -5 * 3600,
    "CST": -6 * 3600,
    "CT": -6 * 3600,
    "CVT": -1 * 3600,
    "CXT": 7 * 3600,
    "ChST": 10 * 3600,
    "D": 4 * 3600,
    "DAVT": 7 * 3600,
    "DDUT": 10 * 3600,
    "E": 5 * 3600,
    "EASST": -5 * 3600,
    "EAST": -6 * 3600,
    "EAT": 3 * 3600,
    "ECT": -5 * 3600,
    "EDT": -4 * 3600,
    "EEST": 3 * 3600,
    "EET": 2 * 3600,
    "EGST": 0 * 3600,
    "EGT": -1 * 3600,
    "EST": -5 * 3600,
    "ET": -5 * 3600,
    "F": 6 * 3600,
    "FET": 3 * 3600,
    "FJST": 13 * 3600,
    "FJT": 12 * 3600,
    "FKST": -3 * 3600,
    "FKT": -4 * 3600,
    "FNT": -2 * 3600,
    "G": 7 * 3600,
    "GALT": -6 * 3600,
    "GAMT": -9 * 3600,
    "GET": 4 * 3600,
    "GFT": -3 * 3600,
    "GILT": 12 * 3600,
    "GMT": 0 * 3600,
    "GST": 4 * 3600,
    "GYT": -4 * 3600,
    "H": 8 * 3600,
    "HDT": -9 * 3600,
    "HKT": 8 * 3600,
    "HOVST": 8 * 3600,
    "HOVT": 7 * 3600,
    "HST": -10 * 3600,
    "I": 9 * 3600,
    "ICT": 7 * 3600,
    "IDT": 3 * 3600,
    "IOT": 6 * 3600,
    "IRDT": 4.5 * 3600,
    "IRKST": 9 * 3600,
    "IRKT": 8 * 3600,
    "IRST": 3.5 * 3600,
    "IST": 5.5 * 3600,
    "JST": 9 * 3600,
    "K": 10 * 3600,
    "KGT": 6 * 3600,
    "KOST": 11 * 3600,
    "KRAST": 8 * 3600,
    "KRAT": 7 * 3600,
    "KST": 9 * 3600,
    "KUYT": 4 * 3600,
    "L": 11 * 3600,
    "LHDT": 11 * 3600,
    "LHST": 10.5 * 3600,
    "LINT": 14 * 3600,
    "M": 12 * 3600,
    "MAGST": 12 * 3600,
    "MAGT": 11 * 3600,
    "MART": 9.5 * 3600,
    "MAWT": 5 * 3600,
    "MDT": -6 * 3600,
    "MHT": 12 * 3600,
    "MMT": 6.5 * 3600,
    "MSD": 4 * 3600,
    "MSK": 3 * 3600,
    "MST": -7 * 3600,
    "MT": -7 * 3600,
    "MUT": 4 * 3600,
    "MVT": 5 * 3600,
    "MYT": 8 * 3600,
    "N": -1 * 3600,
    "NCT": 11 * 3600,
    "NDT": 2.5 * 3600,
    "NFT": 11 * 3600,
    "NOVST": 7 * 3600,
    "NOVT": 7 * 3600,
    "NPT": 5.5 * 3600,
    "NRT": 12 * 3600,
    "NST": 3.5 * 3600,
    "NUT": -11 * 3600,
    "NZDT": 13 * 3600,
    "NZST": 12 * 3600,
    "O": -2 * 3600,
    "OMSST": 7 * 3600,
    "OMST": 6 * 3600,
    "ORAT": 5 * 3600,
    "P": -3 * 3600,
    "PDT": -7 * 3600,
    "PET": -5 * 3600,
    "PETST": 12 * 3600,
    "PETT": 12 * 3600,
    "PGT": 10 * 3600,
    "PHOT": 13 * 3600,
    "PHT": 8 * 3600,
    "PKT": 5 * 3600,
    "PMDT": -2 * 3600,
    "PMST": -3 * 3600,
    "PONT": 11 * 3600,
    "PST": -8 * 3600,
    "PT": -8 * 3600,
    "PWT": 9 * 3600,
    "PYST": -3 * 3600,
    "PYT": -4 * 3600,
    "Q": -4 * 3600,
    "QYZT": 6 * 3600,
    "R": -5 * 3600,
    "RET": 4 * 3600,
    "ROTT": -3 * 3600,
    "S": -6 * 3600,
    "SAKT": 11 * 3600,
    "SAMT": 4 * 3600,
    "SAST": 2 * 3600,
    "SBT": 11 * 3600,
    "SCT": 4 * 3600,
    "SGT": 8 * 3600,
    "SRET": 11 * 3600,
    "SRT": -3 * 3600,
    "SST": -11 * 3600,
    "SYOT": 3 * 3600,
    "T": -7 * 3600,
    "TAHT": -10 * 3600,
    "TFT": 5 * 3600,
    "TJT": 5 * 3600,
    "TKT": 13 * 3600,
    "TLT": 9 * 3600,
    "TMT": 5 * 3600,
    "TOST": 14 * 3600,
    "TOT": 13 * 3600,
    "TRT": 3 * 3600,
    "TVT": 12 * 3600,
    "U": -8 * 3600,
    "ULAST": 9 * 3600,
    "ULAT": 8 * 3600,
    "UTC": 0 * 3600,
    "UYST": -2 * 3600,
    "UYT": -3 * 3600,
    "UZT": 5 * 3600,
    "V": -9 * 3600,
    "VET": -4 * 3600,
    "VLAST": 11 * 3600,
    "VLAT": 10 * 3600,
    "VOST": 6 * 3600,
    "VUT": 11 * 3600,
    "W": -10 * 3600,
    "WAKT": 12 * 3600,
    "WARST": -3 * 3600,
    "WAST": 2 * 3600,
    "WAT": 1 * 3600,
    "WEST": 1 * 3600,
    "WET": 0 * 3600,
    "WFT": 12 * 3600,
    "WGST": -2 * 3600,
    "WGT": -3 * 3600,
    "WIB": 7 * 3600,
    "WIT": 9 * 3600,
    "WITA": 8 * 3600,
    "WST": 14 * 3600,
    "WT": 0 * 3600,
    "X": -11 * 3600,
    "Y": -12 * 3600,
    "YAKST": 10 * 3600,
    "YAKT": 9 * 3600,
    "YAPT": 10 * 3600,
    "YEKST": 6 * 3600,
    "YEKT": 5 * 3600,
    "Z": 0 * 3600,
}
whois_timezone_info: Final[Mapping[str, int]] = {k: int(v) for k, v in _whois_timezone_info.items()}


def _extract_auth_params(request: web.Request) -> tuple[str, str, str] | None:
    """
    HTTP Authorization header must be formatted as:
    "Authorization: BackendAI signMethod=HMAC-SHA256,
                    credential=<ACCESS_KEY>:<SIGNATURE>"
    """
    auth_hdr = request.headers.get("Authorization")
    if not auth_hdr:
        return None
    pieces = auth_hdr.split(" ", 1)
    if len(pieces) != 2:
        raise InvalidAuthParameters("Malformed authorization header")
    auth_type, auth_str = pieces
    if auth_type not in ("BackendAI", "Sorna"):
        raise InvalidAuthParameters("Invalid authorization type name")

    raw_params = map(lambda s: s.strip(), auth_str.split(","))
    params = {}
    for param in raw_params:
        key, value = param.split("=", 1)
        params[key.strip()] = value.strip()

    try:
        access_key, signature = params["credential"].split(":", 1)
        return params["signMethod"], access_key, signature
    except (KeyError, ValueError):
        raise InvalidAuthParameters("Missing or malformed authorization parameters")


def check_date(request: web.Request) -> bool:
    raw_date = request.headers.get("Date")
    if not raw_date:
        raw_date = request.headers.get("X-BackendAI-Date", request.headers.get("X-Sorna-Date"))
    if not raw_date:
        return False
    try:
        # HTTP standard says "Date" header must be in GMT only.
        # However, dateutil.parser can recognize other commonly used
        # timezone names and offsets.
        date = dtparse(raw_date, tzinfos=whois_timezone_info)
        if date.tzinfo is None:
            date = date.replace(tzinfo=tzutc())  # assume as UTC
        now = datetime.now(tzutc())
        min_date = now - timedelta(minutes=15)
        max_date = now + timedelta(minutes=15)
        request["date"] = date
        request["raw_date"] = raw_date
        if not (min_date < date < max_date):
            return False
    except ValueError:
        return False
    return True


async def sign_request(sign_method: str, request: web.Request, secret_key: str) -> str:
    try:
        mac_type, hash_type = map(lambda s: s.lower(), sign_method.split("-"))
        if mac_type != "hmac":
            raise InvalidAuthParameters("Unsupported request signing method (MAC type)")
        if hash_type not in hashlib.algorithms_guaranteed:
            raise InvalidAuthParameters("Unsupported request signing method (hash type)")

        new_api_version = request.headers.get("X-BackendAI-Version")
        legacy_api_version = request.headers.get("X-Sorna-Version")
        api_version = new_api_version or legacy_api_version
        if api_version is None:
            raise InvalidAuthParameters("API version missing in request headers")
        body = b""
        if api_version < "v4.20181215":
            if request.can_read_body and request.content_type != "multipart/form-data":
                # read the whole body if neither streaming nor bodyless
                body = await request.read()
        body_hash = hashlib.new(hash_type, body).hexdigest()
        path = request.raw_path
        host = request.host
        if upstream_url := request.headers.get("X-Forwarded-URL", None):
            parsed_url = urlparse(upstream_url)
            path = parsed_url.path
            host = parsed_url.netloc

        sign_bytes = "{0}\n{1}\n{2}\nhost:{3}\ncontent-type:{4}\nx-{name}-version:{5}\n{6}".format(
            request.method,
            str(path),
            request["raw_date"],
            host,
            request.content_type,
            api_version,
            body_hash,
            name="backendai" if new_api_version is not None else "sorna",
        ).encode()
        sign_key = hmac.new(
            secret_key.encode(), request["date"].strftime("%Y%m%d").encode(), hash_type
        ).digest()
        sign_key = hmac.new(sign_key, host.encode(), hash_type).digest()
        return hmac.new(sign_key, sign_bytes, hash_type).hexdigest()
    except ValueError:
        raise AuthorizationFailed("Invalid signature")


def validate_ip(request: web.Request, user: Mapping[str, Any]) -> None:
    allowed_client_ip = user.get("allowed_client_ip", None)
    if not allowed_client_ip or allowed_client_ip is None:
        # allowed_client_ip is None or [] - empty list
        return
    if not isinstance(allowed_client_ip, list):
        raise InvalidClientIPConfig("allowed_client_ip must be a list")
    raw_client_addr: str | None = request.headers.get("X-Forwarded-For") or request.remote
    if raw_client_addr is None:
        raise AuthorizationFailed("Not allowed IP address")
    try:
        client_addr: ReadableCIDR = ReadableCIDR(raw_client_addr, is_network=False)
    except InvalidIpAddressValue:
        raise InvalidAuthParameters(f"{raw_client_addr} is invalid IP address value")
    if any(client_addr.address in allowed_ip_cand.address for allowed_ip_cand in allowed_client_ip):
        return
    raise AuthorizationFailed(f"'{client_addr}' is not allowed IP address")
