from enum import StrEnum

import trafaret as t

from ai.backend.common import validators as tx


class APIVersion(StrEnum):
    V1 = "v1"
    V2 = "v2"
    LATEST = "latest"


config_iv = t.Dict(
    {
        t.Key("vast_endpoint"): t.String(),
        t.Key("vast_username"): t.String(),
        t.Key("vast_password"): t.String(),
        t.Key("vast_api_version", default=APIVersion.V2): tx.Enum(APIVersion),
    }
)
