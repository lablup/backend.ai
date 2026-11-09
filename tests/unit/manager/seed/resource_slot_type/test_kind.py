"""The `resource_slot_type` kind reads one item per slot type, and `mgr seed check`
reports what it skips."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml
from click.testing import CliRunner

from ai.backend.common.types import SlotTypes
from ai.backend.manager.cli.seed import cli
from ai.backend.manager.errors.seed import InvalidSeedDocument
from ai.backend.manager.models.resource_slot.types import NumberFormat
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.resource_slot_type.seed import ResourceSlotTypeSeed
from ai.backend.manager.seed.runner import SeedPlanner

_UUID = "eff6619c-a85c-40f4-ae59-608b0f683b4f"


def _write(path: Path, *items: dict[str, Any]) -> Path:
    path.write_text(
        yaml.safe_dump({"kind": "resource_slot_type", "version": 1, "items": list(items)})
    )
    return path


class TestResourceSlotTypeSeed:
    def test_the_key_is_the_uuid(self) -> None:
        seed = ResourceSlotTypeSeed.model_validate({
            "uuid": _UUID,
            "slot_name": "cpu",
            "slot_type": "count",
        })
        assert seed.key() == _UUID

    def test_a_field_left_out_takes_the_column_default(self) -> None:
        seed = ResourceSlotTypeSeed.model_validate({
            "uuid": _UUID,
            "slot_name": "cpu",
            "slot_type": "count",
        })
        assert seed.slot_type == SlotTypes.COUNT
        assert (seed.required, seed.enabled, seed.rank) == (False, True, 0)
        assert (seed.display_name, seed.description) == ("", "")
        assert (seed.display_unit, seed.display_icon) == ("", "")
        assert seed.number_format == NumberFormat()
        assert (seed.sealed_launch, seed.max_per_session, seed.single_node_only) == (
            False,
            None,
            False,
        )

    @pytest.mark.parametrize(
        "item",
        [
            {"slot_name": "cpu", "slot_type": "count"},
            {"uuid": _UUID, "slot_type": "count"},
            {"uuid": _UUID, "slot_name": "", "slot_type": "count"},
            {"uuid": _UUID, "slot_name": "x" * 65, "slot_type": "count"},
            {"uuid": _UUID, "slot_name": "cpu", "slot_type": "pieces"},
            {"uuid": _UUID, "slot_name": "cpu", "slot_type": "count", "display_name": "x" * 129},
            {"uuid": _UUID, "slot_name": "cpu", "slot_type": "count", "description": "x" * 257},
            {"uuid": _UUID, "slot_name": "cpu", "slot_type": "count", "display_unit": "x" * 33},
            {"uuid": _UUID, "slot_name": "cpu", "slot_type": "count", "display_icon": "x" * 65},
            {"uuid": _UUID, "slot_name": "cpu", "slot_type": "count", "rank": 2**31},
            {"uuid": _UUID, "slot_name": "cpu", "slot_type": "count", "color": "red"},
        ],
        ids=[
            "missing-uuid",
            "missing-slot-name",
            "empty-slot-name",
            "too-long-slot-name",
            "unknown-slot-type",
            "too-long-display-name",
            "too-long-description",
            "too-long-display-unit",
            "too-long-display-icon",
            "rank-out-of-int4",
            "unknown-field",
        ],
    )
    def test_an_invalid_item_is_refused(self, item: dict[str, Any]) -> None:
        with pytest.raises(InvalidSeedDocument):
            ResourceSlotTypeSeed.model_validate(item)


class TestResourceSlotTypeKind:
    def test_the_files_are_planned_whole(self, resource_slot_type_seed_dir: Path) -> None:
        plan = SeedPlanner(create_seed_kind_registry()).plan([resource_slot_type_seed_dir])
        assert plan.rejections == []
        [batch] = plan.batches
        assert batch.kind.name == "resource_slot_type"
        assert [item.key() for item in batch.items()] == [
            "eff6619c-a85c-40f4-ae59-608b0f683b4f",
            "9d1a589e-2a78-491e-97d0-32d2a0079564",
        ]

    def test_a_uuid_stated_in_two_files_skips_both(self, tmp_path: Path) -> None:
        item = {"uuid": _UUID, "slot_name": "cpu", "slot_type": "count"}
        first = _write(tmp_path / "first.yaml", item)
        second = _write(tmp_path / "second.yaml", item)
        plan = SeedPlanner(create_seed_kind_registry()).plan([first, second])
        assert sorted(rejection.source for rejection in plan.rejections) == [
            str(first),
            str(second),
        ]
        assert plan.batches == []


class TestCheckCommand:
    def test_the_files_pass(self, resource_slot_type_seed_dir: Path) -> None:
        result = CliRunner().invoke(cli, ["check", str(resource_slot_type_seed_dir)])
        assert result.exit_code == 0, result.output
        assert "resource_slot_type: 1 files, 2 items" in result.output

    def test_an_invalid_item_fails_the_command(self, tmp_path: Path) -> None:
        path = _write(tmp_path / "bad.yaml", {"uuid": _UUID, "slot_name": "", "slot_type": "count"})
        result = CliRunner().invoke(cli, ["check", str(path)])
        assert result.exit_code != 0
