"""Unit tests for ``_merge_resolved_legacy_mounts`` in the session REST handler.

The function takes a ``name -> UUID`` resolution and merges it into the
UUID-keyed ``mount_ids`` / ``mount_id_map`` / ``mount_options`` buckets of
``creation_config``, dropping the now-resolved name-keyed legacy keys.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

import pytest

from ai.backend.manager.api.rest.session.handler import _merge_resolved_legacy_mounts

_UUID_A = UUID("11111111-1111-1111-1111-111111111111")
_UUID_B = UUID("22222222-2222-2222-2222-222222222222")
_UUID_PRESET = UUID("33333333-3333-3333-3333-333333333333")


class TestMergeResolvedLegacyMounts:
    def test_empty_resolution_returns_config_unchanged(self) -> None:
        config = {"mounts": ["foo"], "mount_map": {"foo": "/data"}}
        result = _merge_resolved_legacy_mounts(config, {})
        assert result is config

    def test_resolved_uuid_appended_to_mount_ids(self) -> None:
        config = {"mounts": ["vf-a"]}
        result = _merge_resolved_legacy_mounts(config, {"vf-a": _UUID_A})
        assert result["mount_ids"] == [_UUID_A]
        assert "mounts" not in result

    def test_mount_map_rekeyed_onto_uuid(self) -> None:
        config = {
            "mounts": ["vf-a"],
            "mount_map": {"vf-a": "/work/data"},
        }
        result = _merge_resolved_legacy_mounts(config, {"vf-a": _UUID_A})
        assert result["mount_id_map"] == {_UUID_A: "/work/data"}
        assert "mount_map" not in result

    def test_mount_options_rekeyed_onto_uuid(self) -> None:
        config = {
            "mounts": ["vf-a"],
            "mount_options": {"vf-a": {"permission": "ro"}},
        }
        result = _merge_resolved_legacy_mounts(config, {"vf-a": _UUID_A})
        assert result["mount_options"][_UUID_A] == {"permission": "ro"}

    def test_all_three_surfaces_rekeyed_together(self) -> None:
        config = {
            "mounts": ["vf-a"],
            "mount_map": {"vf-a": "/data"},
            "mount_options": {"vf-a": {"type": "bind"}},
        }
        result = _merge_resolved_legacy_mounts(config, {"vf-a": _UUID_A})
        assert result["mount_ids"] == [_UUID_A]
        assert result["mount_id_map"] == {_UUID_A: "/data"}
        assert result["mount_options"][_UUID_A] == {"type": "bind"}
        assert "mounts" not in result
        assert "mount_map" not in result

    def test_existing_uuid_in_mount_ids_is_not_duplicated(self) -> None:
        # Caller already supplied vf-a's UUID via the modern surface;
        # the resolver also returns it (because the name was in the legacy
        # ``mounts`` list). The merge must not append a duplicate.
        config = {"mount_ids": [str(_UUID_A)], "mounts": ["vf-a"]}
        result = _merge_resolved_legacy_mounts(config, {"vf-a": _UUID_A})
        assert result["mount_ids"] == [str(_UUID_A)]

    def test_existing_uuid_keyed_mount_id_map_is_not_overwritten(self) -> None:
        # Modern caller supplied an explicit UUID-keyed path for vf-a;
        # the legacy ``mount_map`` entry must NOT clobber it.
        config = {
            "mount_id_map": {_UUID_A: "/explicit"},
            "mounts": ["vf-a"],
            "mount_map": {"vf-a": "/legacy"},
        }
        result = _merge_resolved_legacy_mounts(config, {"vf-a": _UUID_A})
        assert result["mount_id_map"][_UUID_A] == "/explicit"

    def test_unrelated_uuid_keyed_mount_ids_preserved(self) -> None:
        # An unrelated pre-existing UUID stays in mount_ids alongside the
        # newly resolved one; ordering is original-first, resolved-after.
        config = {"mount_ids": [_UUID_PRESET], "mounts": ["vf-a"]}
        result = _merge_resolved_legacy_mounts(config, {"vf-a": _UUID_A})
        assert result["mount_ids"] == [_UUID_PRESET, _UUID_A]

    def test_multiple_names_resolved_in_one_pass(self) -> None:
        config = {
            "mounts": ["vf-a", "vf-b"],
            "mount_map": {"vf-a": "/a", "vf-b": "/b"},
        }
        result = _merge_resolved_legacy_mounts(config, {"vf-a": _UUID_A, "vf-b": _UUID_B})
        assert set(result["mount_ids"]) == {_UUID_A, _UUID_B}
        assert result["mount_id_map"] == {_UUID_A: "/a", _UUID_B: "/b"}

    def test_name_only_in_mount_map_is_handled(self) -> None:
        # vf-b appears only in mount_map (not in mounts). The caller is
        # expected to pass its name to the resolver too; this test
        # confirms the merge re-keys that path entry once a UUID is given.
        config = {
            "mounts": ["vf-a"],
            "mount_map": {"vf-a": "/a", "vf-b": "/b"},
        }
        result = _merge_resolved_legacy_mounts(config, {"vf-a": _UUID_A, "vf-b": _UUID_B})
        assert result["mount_id_map"] == {_UUID_A: "/a", _UUID_B: "/b"}
        # mount_ids picks up both UUIDs (no original mount_ids in input)
        assert set(result["mount_ids"]) == {_UUID_A, _UUID_B}


@pytest.mark.parametrize(
    "config,expected_dropped",
    [
        ({"mounts": ["vf-a"]}, ["mounts"]),
        ({"mount_map": {"vf-a": "/x"}}, ["mount_map"]),
        ({"mounts": ["vf-a"], "mount_map": {"vf-a": "/x"}}, ["mounts", "mount_map"]),
    ],
)
def test_legacy_keys_are_dropped_from_output(
    config: dict[str, Any], expected_dropped: list[str]
) -> None:
    result = _merge_resolved_legacy_mounts(config, {"vf-a": _UUID_A})
    for key in expected_dropped:
        assert key not in result
