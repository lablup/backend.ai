"""The ``mgr image`` commands configure the ORM mappers from a minimal set of models."""

from __future__ import annotations

import os
import subprocess
import sys

from ai.backend.manager.cli import image_impl

_CONFIGURE_MAPPERS = f"""
from sqlalchemy.orm import configure_mappers

from {image_impl.__name__} import _register_image_cli_orm_cluster

_register_image_cli_orm_cluster()
configure_mappers()
"""


def test_the_registered_models_let_every_mapper_configure() -> None:
    # A fresh interpreter: other tests import every model, which hides a missing registration.
    result = subprocess.run(
        [sys.executable, "-c", _CONFIGURE_MAPPERS],
        env={**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
