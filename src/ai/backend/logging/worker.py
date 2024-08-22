from __future__ import annotations

import logging
import os
import threading
from typing import Any, Mapping

import yarl
import zmq

from .formatter import SerializedExceptionFormatter


def log_worker(
    logging_config: Mapping[str, Any],
    parent_pid: int,
    log_endpoint: str,
    ready_event: threading.Event,
) -> None:
    console_handler = None
    file_handler = None
    logstash_handler = None
    graylog_handler = None

    # For future references: when implementing new kind of logging adapters,
    # make sure to adapt our custom `Formatter.formatException()` approach;
    # Otherwise it won't print out EXCEPTION level log (along with the traceback).
    if "console" in logging_config["drivers"]:
        console_handler = setup_console_log_handler(logging_config)

    if "file" in logging_config["drivers"]:
        file_handler = setup_file_log_handler(logging_config)

    if "logstash" in logging_config["drivers"]:
        drv_config = logging_config["logstash"]
        logstash_handler = LogstashHandler(
            endpoint=drv_config["endpoint"],
            protocol=drv_config["protocol"],
            ssl_enabled=drv_config["ssl-enabled"],
            ssl_verify=drv_config["ssl-verify"],
            myhost="hostname",  # TODO: implement
        )
        logstash_handler.setLevel(logging_config["level"])
        logstash_handler.setFormatter(SerializedExceptionFormatter())
    if "graylog" in logging_config["drivers"]:
        graylog_handler = setup_graylog_handler(logging_config)
        assert graylog_handler is not None
        graylog_handler.setFormatter(SerializedExceptionFormatter())

    zctx = zmq.Context()
    agg_sock = zctx.socket(zmq.PULL)
    agg_sock.bind(log_endpoint)
    ep_url = yarl.URL(log_endpoint)
    if ep_url.scheme.lower() == "ipc":
        os.chmod(ep_url.path, 0o777)
    try:
        ready_event.set()
        while True:
            data = agg_sock.recv()
            if not data:
                return
            unpacked_data = msgpack.unpackb(data)
            if not unpacked_data:
                break
            rec = logging.makeLogRecord(unpacked_data)
            if rec is None:
                break
            if console_handler:
                console_handler.emit(rec)
            try:
                if file_handler:
                    file_handler.emit(rec)
                if logstash_handler:
                    logstash_handler.emit(rec)
                    print("logstash")
                if graylog_handler:
                    graylog_handler.emit(rec)
            except OSError:
                # don't terminate the log worker.
                continue
    finally:
        if logstash_handler:
            logstash_handler.cleanup()
        if graylog_handler:
            graylog_handler.close()
        agg_sock.close()
        zctx.term()
