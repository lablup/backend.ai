from __future__ import annotations

import logging
import socket
import ssl
from typing import Any, Mapping, Optional

import graypy


class GELFTLSHandler(graypy.GELFTLSHandler):
    ssl_ctx: ssl.SSLContext

    def __init__(self, host, port=12204, validate=False, ca_certs=None, **kwargs) -> None:
        """Initialize the GELFTLSHandler

        :param host: GELF TLS input host.
        :type host: str

        :param port: GELF TLS input port.
        :type port: int

        :param validate: If :obj:`True`, validate the Graylog server's
            certificate. In this case specifying ``ca_certs`` is also
            required.
        :type validate: bool

        :param ca_certs: Path to CA bundle file.
        :type ca_certs: str
        """

        super().__init__(host, port=port, validate=validate, **kwargs)
        self.ssl_ctx = ssl.create_default_context(capath=ca_certs)
        if not validate:
            self.ssl_ctx.check_hostname = False
            self.ssl_ctx.verify_mode = ssl.CERT_NONE

    def makeSocket(self, timeout: float = 1):
        """Create a TLS wrapped socket"""
        plain_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        if hasattr(plain_socket, "settimeout"):
            plain_socket.settimeout(timeout)

        wrapped_socket = self.ssl_ctx.wrap_socket(
            plain_socket,
            server_hostname=self.host,
        )
        wrapped_socket.connect((self.host, self.port))

        return wrapped_socket


def setup_graylog_handler(config: Mapping[str, Any]) -> Optional[logging.Handler]:
    drv_config = config["graylog"]
    graylog_params = {
        "host": drv_config["host"],
        "port": drv_config["port"],
        "validate": drv_config["ssl-verify"],
        "ca_certs": drv_config["ca-certs"],
        "keyfile": drv_config["keyfile"],
        "certfile": drv_config["certfile"],
    }
    if drv_config["localname"]:
        graylog_params["localname"] = drv_config["localname"]
    else:
        graylog_params["fqdn"] = drv_config["fqdn"]

    graylog_handler = GELFTLSHandler(**graylog_params)
    graylog_handler.setLevel(config["level"])
    return graylog_handler
