from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import override

import pytest

from ai.backend.agent.containerd.profile.loader import select_profile
from ai.backend.agent.errors.containerd import ProfileNotApplicable
from ai.backend.common.types import SlotName

from .conftest import FakeProfile

TDX = SlotName("confidential.tdx")
SEV = SlotName("confidential.sev")


class TestSelectProfileSuccess:
    def test_no_profiles_returns_builtin(self, builtin: FakeProfile) -> None:
        slots = {SlotName("cpu"): Decimal(1)}

        assert select_profile([], frozenset(), slots, builtin=builtin) is builtin

    def test_first_of_two_accepting_wins(self, builtin: FakeProfile) -> None:
        first = FakeProfile("a", accepts=True)
        second = FakeProfile("b", accepts=True)

        result = select_profile([first, second], frozenset(), {}, builtin=builtin)

        assert result is first

    def test_first_refuses_second_accepts(self, builtin: FakeProfile) -> None:
        first = FakeProfile("a", accepts=False)
        second = FakeProfile("b", accepts=True)

        result = select_profile([first, second], frozenset(), {}, builtin=builtin)

        assert result is second

    def test_held_required_slot_and_a_profile_accepts(self, builtin: FakeProfile) -> None:
        profile = FakeProfile("coco-tdx", accepts=True)

        result = select_profile([profile], frozenset({TDX}), {TDX: Decimal(1)}, builtin=builtin)

        assert result is profile

    def test_required_slot_listed_with_zero_falls_back_to_builtin(
        self, builtin: FakeProfile
    ) -> None:
        profile = FakeProfile("coco-tdx", accepts=False)

        result = select_profile([profile], frozenset({TDX}), {TDX: Decimal(0)}, builtin=builtin)

        assert result is builtin

    def test_required_slot_absent_falls_back_to_builtin(self, builtin: FakeProfile) -> None:
        profile = FakeProfile("coco-tdx", accepts=False)

        result = select_profile(
            [profile], frozenset({TDX}), {SlotName("cpu"): Decimal(1)}, builtin=builtin
        )

        assert result is builtin


class TestSelectProfileException:
    def test_held_required_slot_and_no_profile_accepts(self, builtin: FakeProfile) -> None:
        profile = FakeProfile("coco-tdx", accepts=False)

        with pytest.raises(ProfileNotApplicable, match=str(TDX)):
            select_profile([profile], frozenset({TDX}), {TDX: Decimal(1)}, builtin=builtin)

    def test_held_required_slot_without_configured_profiles(self, builtin: FakeProfile) -> None:
        with pytest.raises(ProfileNotApplicable, match=str(TDX)):
            select_profile([], frozenset({TDX}), {TDX: Decimal(1)}, builtin=builtin)

    def test_accepts_error_propagates_unwrapped(self, builtin: FakeProfile) -> None:
        class BrokenProfile(FakeProfile):
            @override
            def accepts(self, slots: Mapping[SlotName, Decimal]) -> bool:
                raise ValueError("accepts failed")

        with pytest.raises(ValueError, match="accepts failed"):
            select_profile([BrokenProfile("a", accepts=True)], frozenset(), {}, builtin=builtin)


class TestSelectProfileEdge:
    def test_stops_at_the_first_accepting_profile(self, builtin: FakeProfile) -> None:
        first = FakeProfile("a", accepts=True)
        second = FakeProfile("b", accepts=True)

        select_profile([first, second], frozenset(), {}, builtin=builtin)

        assert len(first.accepts_calls) == 1
        assert second.accepts_calls == []

    def test_every_profile_receives_the_same_slots_mapping(self, builtin: FakeProfile) -> None:
        first = FakeProfile("a", accepts=False)
        second = FakeProfile("b", accepts=False)
        slots = {SlotName("cpu"): Decimal(1)}

        select_profile([first, second], frozenset(), slots, builtin=builtin)

        assert first.accepts_calls[0] is slots
        assert second.accepts_calls[0] is slots

    def test_message_lists_both_held_slots_sorted(self, builtin: FakeProfile) -> None:
        slots = {TDX: Decimal(1), SEV: Decimal(2)}

        with pytest.raises(ProfileNotApplicable) as exc_info:
            select_profile([], frozenset({TDX, SEV}), slots, builtin=builtin)

        assert f"{SEV}, {TDX}" in str(exc_info.value)
