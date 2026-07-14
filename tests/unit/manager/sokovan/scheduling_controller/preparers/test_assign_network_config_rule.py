"""Tests for ``AssignNetworkConfigRule``.

Verifies that the legacy priority (``PERSISTENT`` > ``HOST`` > ``VOLATILE``)
is preserved end-to-end:

  * caller-supplied ``network_id`` forces ``PERSISTENT``
  * scaling-group ``use_host_network`` true picks ``HOST`` and flips
    ``SessionNetworkDraft.use_host_network`` on the draft
  * absence of both falls back to ``VOLATILE``
  * an already-assigned ``network_type`` short-circuits the rule
"""

from __future__ import annotations

import pytest

from ai.backend.manager.data.session.creation import (
    ScalingGroupNetworkInfo,
)
from ai.backend.manager.data.session.draft import (
    SessionNetworkDraft,
    SessionResourceSpecDraft,
)
from ai.backend.manager.data.session.options import DefaultSessionOptions
from ai.backend.manager.models.network import NetworkType
from ai.backend.manager.sokovan.scheduling_controller.preparers.assign_network_config_rule import (
    AssignNetworkConfigRule,
)
from ai.backend.manager.sokovan.scheduling_controller.preparers.draft_rule import (
    SessionSpecPreparationContext,
)


@pytest.fixture
def rule() -> AssignNetworkConfigRule:
    return AssignNetworkConfigRule()


def _context(
    *, use_host_network: bool = False, scaling_group: bool = True
) -> SessionSpecPreparationContext:
    return SessionSpecPreparationContext(
        resource_group_defaults=DefaultSessionOptions(),
        resource_group_network=(
            ScalingGroupNetworkInfo(use_host_network=use_host_network) if scaling_group else None
        ),
    )


class TestAssignNetworkConfigRule:
    async def test_persistent_when_network_id_set(self, rule: AssignNetworkConfigRule) -> None:
        """A caller-supplied ``network_id`` resolves to PERSISTENT."""
        draft = SessionResourceSpecDraft(
            network=SessionNetworkDraft(network_id="net-123"),
        )
        result = await rule.prepare(draft, _context(use_host_network=True))
        # PERSISTENT wins over host_network.
        assert result.network.network_type == NetworkType.PERSISTENT
        assert result.network.network_id == "net-123"
        assert result.network.use_host_network is False

    async def test_host_when_scaling_group_uses_host_network(
        self, rule: AssignNetworkConfigRule
    ) -> None:
        """An empty network + RG host_network flag selects HOST."""
        draft = SessionResourceSpecDraft()
        result = await rule.prepare(draft, _context(use_host_network=True))
        assert result.network.network_type == NetworkType.HOST
        assert result.network.use_host_network is True
        assert result.network.network_id is None

    async def test_volatile_default(self, rule: AssignNetworkConfigRule) -> None:
        """No network id and no host flag falls back to VOLATILE."""
        draft = SessionResourceSpecDraft()
        result = await rule.prepare(draft, _context(use_host_network=False))
        assert result.network.network_type == NetworkType.VOLATILE
        assert result.network.use_host_network is False
        assert result.network.network_id is None

    async def test_noop_when_network_type_already_assigned(
        self, rule: AssignNetworkConfigRule
    ) -> None:
        """An already-set ``network_type`` short-circuits the rule."""
        draft = SessionResourceSpecDraft(
            network=SessionNetworkDraft(
                network_type=NetworkType.VOLATILE,
                network_id="leftover-id",  # intentionally inconsistent
            ),
        )
        result = await rule.prepare(draft, _context(use_host_network=True))
        assert result.network.network_type == NetworkType.VOLATILE
        assert result.network.network_id == "leftover-id"
        assert result is draft

    async def test_volatile_when_scaling_group_network_absent(
        self, rule: AssignNetworkConfigRule
    ) -> None:
        """No scaling-group info in the context still yields VOLATILE."""
        draft = SessionResourceSpecDraft()
        result = await rule.prepare(draft, _context(scaling_group=False))
        assert result.network.network_type == NetworkType.VOLATILE
