from unittest import mock
import sys

from alembic.config import Config
from alembic.script import ScriptDirectory

import_mock = mock.MagicMock()
import_mock.return_value = import_mock

with mock.patch('builtins.__import__', side_effect=import_mock):
    cfg = Config()
    cfg.set_main_option("script_location", "src/ai/backend/manager/models/alembic")
    script = ScriptDirectory.from_config(cfg)

    heads = script.get_revisions("heads")
    if len(heads) > 1:
        print('multiple alembic heads detected!')
        sys.exit(1)
