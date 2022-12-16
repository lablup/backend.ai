import sys

from alembic.config import Config
from alembic.script import ScriptDirectory

cfg = Config()
cfg.set_main_option("script_location", "ai.backend.manager.models:alembic")
script = ScriptDirectory.from_config(cfg)
heads = script.get_revisions("heads")
if len(heads) > 1:
    print('multiple alembic heads detected!')
    sys.exit(1)