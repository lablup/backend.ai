import trafaret as t

from ai.backend.common import validators as tx

config_iv = t.Dict({
    t.Key("dell_endpoint"): t.String(),
    tx.AliasedKey(["dell_username", "dell_admin"]): t.String(),
    t.Key("dell_password"): t.String(),
    t.Key("dell_api_version"): t.String(),
    t.Key("dell_ifs_path"): tx.Path(type="dir", allow_nonexisting=True),
    t.Key("dell_system_name", default=None): t.Null | t.String(),
}).allow_extra("*")
