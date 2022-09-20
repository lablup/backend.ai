from pathlib import Path

import pkg_resources
import trafaret as t
import yarl

from ai.backend.common import validators as tx

default_static_path = Path(pkg_resources.resource_filename("ai.backend.web", "static")).resolve()

license_defs = {
    "edition": "Open Source",
    "valid_since": "",
    "valid_until": "",
}

config_iv = t.Dict(
    {
        t.Key("service"): t.Dict(
            {
                t.Key("ip", default="0.0.0.0"): tx.IPAddress,
                t.Key("port"): t.ToInt[1:65535],
                t.Key("wsproxy"): t.Dict(
                    {
                        t.Key("url", default=""): t.String(allow_blank=True),
                    }
                ),
                tx.AliasedKey(["ssl_enabled", "ssl-enabled"], default=False): t.ToBool,
                tx.AliasedKey(["ssl_cert", "ssl-cert"], default=None): t.Null
                | tx.Path(type="file"),
                tx.AliasedKey(["ssl_privkey", "ssl-privkey"], default=None): t.Null
                | tx.Path(type="file"),
                t.Key("static_path", default=default_static_path): tx.Path(type="dir"),
                tx.AliasedKey(
                    ["force_endpoint_protocol", "force-endpoint-protocol"],
                    default=None,
                ): t.Null
                | t.Enum("https", "http"),
                t.Key("mode"): t.Enum("webui", "static"),
                t.Key("enable_signup", default=False): t.ToBool,
                t.Key("allow_anonymous_change_password", default=False): t.ToBool,
                t.Key("allow_project_resource_monitor", default=False): t.ToBool,
                t.Key("allow_change_signin_mode", default=False): t.ToBool,
                t.Key("allow_manual_image_name_for_session", default=False): t.ToBool,
                t.Key("allow_signup_without_confirmation", default=False): t.ToBool,
                t.Key("always_enqueue_compute_session", default=False): t.ToBool,
                t.Key("webui_debug", default=False): t.ToBool,
                t.Key("mask_user_info", default=False): t.ToBool,
                t.Key("single_sign_on_vendors", default=None): t.Null
                | tx.StringList(empty_str_as_empty_list=True),
                t.Key("enable_container_commit", default=False): t.ToBool,
                t.Key("hide_agents", default=True): t.ToBool,
            }
        ).allow_extra("*"),
        t.Key("resources"): t.Dict(
            {
                t.Key("open_port_to_public", default=False): t.ToBool,
                t.Key("max_cpu_cores_per_container", default=64): t.ToInt,
                t.Key("max_memory_per_container", default=64): t.ToInt,
                t.Key("max_cuda_devices_per_container", default=16): t.ToInt,
                t.Key("max_cuda_shares_per_container", default=16): t.ToInt,
                t.Key("max_shm_per_container", default=2): t.ToFloat,
                t.Key("max_file_upload_size", default=4294967296): t.ToInt,
            }
        ).allow_extra("*"),
        t.Key("environments"): t.Dict(
            {
                t.Key("allowlist", default=None): t.Null
                | tx.StringList(empty_str_as_empty_list=True),
            }
        ).allow_extra("*"),
        t.Key("plugin"): t.Dict(
            {
                t.Key("page", default=None): t.Null | t.String(allow_blank=True),
            }
        ).allow_extra("*"),
        t.Key("pipeline"): t.Dict(
            {
                t.Key("endpoint", default=None): t.Null | tx.URL,
            }
        ).allow_extra("*"),
        t.Key("ui"): t.Dict(
            {
                t.Key("brand"): t.String,
                t.Key("default_environment", default=None): t.Null | t.String,
                t.Key("default_import_environment", default=None): t.Null | t.String,
                t.Key("menu_blocklist", default=None): t.Null
                | tx.StringList(empty_str_as_empty_list=True),
            }
        ).allow_extra("*"),
        t.Key("api"): t.Dict(
            {
                t.Key("domain"): t.String,
                t.Key("endpoint"): tx.DelimiterSeperatedList[yarl.URL](tx.URL, min_length=1),
                t.Key("text"): t.String,
                tx.AliasedKey(["ssl_verify", "ssl-verify"], default=True): t.ToBool,
                t.Key("auth_token_name", default="sToken"): t.String,
            }
        ).allow_extra("*"),
        t.Key("session"): t.Dict(
            {
                t.Key("redis"): t.Dict(
                    {
                        t.Key("host", default="localhost"): t.String,
                        t.Key("port", default=6379): t.ToInt[1:65535],
                        t.Key("db", default=0): t.ToInt,
                        t.Key("password", default=None): t.Null | t.String,
                    }
                ),
                t.Key("max_age", default=604800): t.ToInt,  # seconds (default: 1 week)
                t.Key("flush_on_startup", default=False): t.ToBool,
                t.Key("login_block_time", default=1200): t.ToInt,  # seconds (default: 20 min)
                t.Key("login_allowed_fail_count", default=10): t.ToInt,
                t.Key("auto_logout", default=False): t.ToBool,
            }
        ).allow_extra("*"),
        t.Key("license", default=license_defs): t.Dict(
            {
                t.Key("edition", default=license_defs["edition"]): t.String,
                t.Key("valid_since", default=license_defs["valid_since"]): t.String(
                    allow_blank=True
                ),
                t.Key("valid_until", default=license_defs["valid_until"]): t.String(
                    allow_blank=True
                ),
            }
        ).allow_extra("*"),
    }
).allow_extra("*")
