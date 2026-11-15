import logging

from ai.backend.common.configs.wheelhouse import WheelhouseConfig
from ai.backend.logging.structured import StructuredLogger
from ai.backend.plugin.entrypoint import prepare_wheelhouse

log = StructuredLogger(logging.getLogger(__spec__.name))


def load_configured_wheelhouse(wheelhouse_config: WheelhouseConfig) -> None:
    """
    Called by ``start-server`` before its workers start, which inherit ``sys.path``.
    """
    if wheelhouse_config.allow:
        wheelhouse_path = wheelhouse_config.path.resolve()
        prepare_wheelhouse(wheelhouse_path)
        log.info("wheelhouse loaded", wheelhouse_path=str(wheelhouse_path))
