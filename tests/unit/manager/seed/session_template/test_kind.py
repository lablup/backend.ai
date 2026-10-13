"""The session template files are a `session_template` seed, and `mgr seed check` reports
what it skips."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner

from ai.backend.manager.cli.seed import cli
from ai.backend.manager.data.session_template.types import TemplateType
from ai.backend.manager.errors.seed import InvalidSeedDocument
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedPlanner
from ai.backend.manager.seed.session_template.seed import SessionTemplateSeed

_ID = "0198a5a0-0000-7000-8000-000000001001"
_USER_ID = "0198a5a0-0000-7000-8000-000000001002"


def _template(**fields: Any) -> dict[str, Any]:
    return {"id": _ID, "user_id": _USER_ID, "template": {"spec": {}}} | fields


class TestSessionTemplateSeed:
    def test_the_optional_fields_take_the_column_defaults(self) -> None:
        seed = SessionTemplateSeed.model_validate(_template())
        assert seed.project_id is None
        assert seed.type == TemplateType.TASK
        assert seed.name is None
        assert seed.is_active is True

    def test_an_unknown_field_is_refused(self) -> None:
        with pytest.raises(InvalidSeedDocument):
            SessionTemplateSeed.model_validate(_template(domain_name="default"))

    def test_a_name_beyond_the_column_length_is_refused(self) -> None:
        with pytest.raises(InvalidSeedDocument):
            SessionTemplateSeed.model_validate(_template(name="x" * 129))

    def test_an_unknown_type_is_refused(self) -> None:
        with pytest.raises(InvalidSeedDocument):
            SessionTemplateSeed.model_validate(_template(type="batch"))

    def test_a_template_is_required(self) -> None:
        with pytest.raises(InvalidSeedDocument):
            SessionTemplateSeed.model_validate({"id": _ID, "user_id": _USER_ID})


class TestSessionTemplateKind:
    def test_the_files_are_planned_whole(self, session_template_files: Path) -> None:
        plan = SeedPlanner(create_seed_kind_registry()).plan([session_template_files])
        assert plan.rejections == []
        [batch] = plan.batches
        assert batch.kind.name == "session_template"
        assert len(batch.items()) == 2


class TestCheckCommand:
    def test_the_files_pass(self, session_template_files: Path) -> None:
        result = CliRunner().invoke(cli, ["check", str(session_template_files)])
        assert result.exit_code == 0, result.output
        assert "session_template: 2 files, 2 items" in result.output
