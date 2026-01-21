from typing import Final

DEFAULT_CHUNK_SIZE: Final = 256 * 1024  # 256 KiB
DEFAULT_INFLIGHT_CHUNKS: Final = 8


MANAGER_LOCAL_CFG_OVERRIDE_ENVS: list[tuple[tuple[str, ...], str]] = [
    (("etcd", "namespace"), "BACKEND_NAMESPACE"),
    (("etcd", "addr"), "BACKEND_ETCD_ADDR"),
    (("etcd", "user"), "BACKEND_ETCD_USER"),
    (("etcd", "password"), "BACKEND_ETCD_PASSWORD"),
    (("db", "addr"), "BACKEND_DB_ADDR"),
    (("db", "name"), "BACKEND_DB_NAME"),
    (("db", "user"), "BACKEND_DB_USER"),
    (("db", "password"), "BACKEND_DB_PASSWORD"),
    (("manager", "num-proc"), "BACKEND_MANAGER_NPROC"),
    (("manager", "ssl-cert"), "BACKEND_SSL_CERT"),
    (("manager", "ssl-privkey"), "BACKEND_SSL_KEY"),
    (("manager", "pid-file"), "BACKEND_PID_FILE"),
    (("manager", "api-listen-addr", "host"), "BACKEND_SERVICE_IP"),
    (("manager", "api-listen-addr", "port"), "BACKEND_SERVICE_PORT"),
    (("manager", "event-listen-addr", "host"), "BACKEND_ADVERTISED_MANAGER_HOST"),
    (("manager", "event-listen-addr", "port"), "BACKEND_EVENTS_PORT"),
    (("docker-registry", "ssl-verify"), "BACKEND_SKIP_SSLCERT_VALIDATION"),
]
