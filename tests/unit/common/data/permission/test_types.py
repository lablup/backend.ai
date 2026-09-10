"""Tests for the RBAC permission bitmask."""

from __future__ import annotations

from ai.backend.common.data.permission.types import Permission

_ATOMIC_PERMISSIONS = [
    Permission.READ,
    Permission.UPDATE,
    Permission.CREATE,
    Permission.SOFT_DELETE,
    Permission.HARD_DELETE,
]


class TestPermission:
    """Tests for the Permission IntFlag bitmask and cap semantics."""

    def test_atomic_bits_are_disjoint_powers_of_two(self) -> None:
        """Each atomic permission occupies its own bit so flags never collide."""
        combined = Permission.NONE
        for perm in _ATOMIC_PERMISSIONS:
            assert perm.value & (perm.value - 1) == 0  # power of two
            assert not (combined & perm)  # bit not yet used
            combined |= perm
        # The OR of all atomic bits equals the full cap with no overlap lost.
        assert combined == Permission.full()
        assert int(combined) == sum(int(p) for p in _ATOMIC_PERMISSIONS)

    def test_cap_membership_is_bitwise(self) -> None:
        """A cap contains exactly the operations whose bit is set."""
        cap = Permission.READ | Permission.UPDATE | Permission.CREATE
        assert cap & Permission.READ
        assert cap & Permission.UPDATE
        assert cap & Permission.CREATE
        assert not (cap & Permission.SOFT_DELETE)
        assert not (cap & Permission.HARD_DELETE)

    def test_granted_within_cap_check(self) -> None:
        """``(granted & ~cap) == NONE`` holds iff granted is within the cap."""
        cap = Permission.READ | Permission.UPDATE
        within = Permission.READ
        exceeding = Permission.READ | Permission.HARD_DELETE
        assert (within & ~cap) == Permission.NONE
        assert (exceeding & ~cap) != Permission.NONE

    def test_covers_requires_every_required_bit(self) -> None:
        """``covers`` is ALL-bits, not ANY-bit: a partial hold is not enough."""
        required = Permission.CREATE | Permission.UPDATE
        assert not Permission.CREATE.covers(required)
        assert not Permission.UPDATE.covers(required)
        assert not Permission.NONE.covers(required)
        assert (Permission.CREATE | Permission.UPDATE).covers(required)
        assert Permission.full().covers(required)

    def test_covers_matches_any_bit_for_a_single_bit_requirement(self) -> None:
        """Single-bit requirements keep the pre-mask behavior unchanged."""
        for effective in (Permission.NONE, Permission.READ | Permission.UPDATE, Permission.full()):
            for required in _ATOMIC_PERMISSIONS:
                assert effective.covers(required) is bool(effective & required)

    def test_covers_nothing_is_always_true(self) -> None:
        assert Permission.NONE.covers(Permission.NONE)

    def test_cap_superset_check_is_not_magnitude(self) -> None:
        """Cap membership is a bitwise superset test, never an int >= comparison."""
        cap = Permission.HARD_DELETE
        op = Permission.READ
        # Magnitude would wrongly allow (16 >= 1); the superset test correctly rejects.
        assert int(cap) >= int(op)
        assert (cap & op) != op
