from enum import StrEnum
from typing import Final

import trafaret as t

from ai.backend.common import validators as tx

DEFAULT_CLUSTER_ID: Final = 1


class APIVersion(StrEnum):
    V1 = "v1"
    V2 = "v2"
    LATEST = "latest"


config_iv = t.Dict({
    t.Key("vast_endpoint"): t.String(),
    t.Key("vast_username"): t.String(),
    t.Key("vast_password"): t.String(),
    t.Key("vast_verify_ssl", default=False): t.Bool(),
    t.Key("vast_api_version", default=APIVersion.V2): tx.Enum(APIVersion),
    t.Key("vast_cluster_id", default=DEFAULT_CLUSTER_ID): t.Int,
    t.Key("vast_storage_base_dir", default="/"): t.String(),
}).allow_extra("*")
