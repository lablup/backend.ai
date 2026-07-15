"""Tests for ``BuildInternalDataRule``.

Verifies the session-level overlay onto per-kernel ``internal_data``:

  * ``context.dotfile_data`` (dotfiles + optional ssh_keypair) flows onto every kernel draft
  * ``model_definition_path`` / ``model_definition`` / ``sudo_session_enabled``
    are added only when their input values are present
  * caller-pre-populated keys on a kernel's ``internal_data`` survive
    unless the overlay explicitly sets the same key (legacy precedence)
  * empty inputs result in a no-op
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

from ai.backend.manager.data.dotfile.types import (
    DotfileBundle,
    DotfileEntry,
    SSHKeypair,
)
from ai.backend.manager.data.session.draft import (
    KernelSpecDraft,
    SessionResourceSpecDraft,
)
from ai.backend.manager.data.session.options import (
    DefaultSessionOptions,
    InternalDataExtras,
)
from ai.backend.manager.sokovan.scheduling_controller.preparers.build_internal_data_rule import (
    BuildInternalDataRule,
)
from ai.backend.manager.sokovan.scheduling_controller.preparers.draft_rule import (
    SessionSpecPreparationContext,
)


@pytest.fixture
def rule() -> BuildInternalDataRule:
    return BuildInternalDataRule()


def _context(*, dotfile_data: DotfileBundle | None = None) -> SessionSpecPreparationContext:
    return SessionSpecPreparationContext(
        resource_group_defaults=DefaultSessionOptions(),
        dotfile_data=dotfile_data or DotfileBundle(),
    )


def _draft(
    *kernels: KernelSpecDraft,
    sudo_session_enabled: bool = False,
    model_definition_path: str | None = None,
    model_definition: Mapping[str, Any] | None = None,
) -> SessionResourceSpecDraft:
    return SessionResourceSpecDraft(
        kernel_specs=kernels,
        internal_data_extras=InternalDataExtras(
            sudo_session_enabled=sudo_session_enabled,
            model_definition_path=model_definition_path,
            model_definition=model_definition,
        ),
    )


class TestBuildInternalDataRule:
    async def test_noop_when_all_inputs_empty(self, rule: BuildInternalDataRule) -> None:
        """Zero overlay keys returns the draft unchanged."""
        draft = _draft(KernelSpecDraft(cluster_role="main"))
        result = await rule.prepare(draft, _context())
        assert result is draft

    async def test_overlay_dotfile_data(self, rule: BuildInternalDataRule) -> None:
        """Dotfile/ssh_keypair entries from the context land on each kernel."""
        bundle = DotfileBundle(
            dotfiles=(DotfileEntry(path="/etc/profile.d/bai.sh", perm="755", data="echo hi"),),
            ssh_keypair=SSHKeypair(public_key="ssh-rsa A", private_key="-----..."),
        )
        draft = _draft(KernelSpecDraft(cluster_role="main"))

        result = await rule.prepare(draft, _context(dotfile_data=bundle))

        kernel = result.kernel_specs[0]
        assert kernel.internal_data["dotfiles"] == [
            {"path": "/etc/profile.d/bai.sh", "perm": "755", "data": "echo hi"},
        ]
        assert kernel.internal_data["ssh_keypair"] == {
            "public_key": "ssh-rsa A",
            "private_key": "-----...",
        }

    async def test_overlay_deployment_keys(self, rule: BuildInternalDataRule) -> None:
        """Model-definition / path flow through when supplied."""
        draft = _draft(
            KernelSpecDraft(cluster_role="main"),
            model_definition_path="/models/foo.yaml",
            model_definition={"kind": "Model", "name": "foo"},
        )
        result = await rule.prepare(draft, _context())
        kernel = result.kernel_specs[0]
        assert kernel.internal_data["model_definition_path"] == "/models/foo.yaml"
        assert kernel.internal_data["model_definition"] == {
            "kind": "Model",
            "name": "foo",
        }

    async def test_sudo_flag_only_added_when_true(self, rule: BuildInternalDataRule) -> None:
        """``sudo_session_enabled=False`` is not emitted into the overlay."""
        off_draft = _draft(KernelSpecDraft(cluster_role="main"), sudo_session_enabled=False)
        off = await rule.prepare(off_draft, _context())
        assert off is off_draft  # no overlay keys → no-op

        on_draft = _draft(KernelSpecDraft(cluster_role="main"), sudo_session_enabled=True)
        on = await rule.prepare(on_draft, _context())
        assert on.kernel_specs[0].internal_data == {"sudo_session_enabled": True}

    async def test_overlay_overrides_caller_keys_on_conflict(
        self, rule: BuildInternalDataRule
    ) -> None:
        """Legacy precedence: overlay wins on key conflict."""
        draft = _draft(
            KernelSpecDraft(
                cluster_role="main",
                internal_data={
                    "sudo_session_enabled": False,  # will be overwritten
                    "prevent_vfolder_mounts": True,  # caller-only key, survives
                },
            ),
            sudo_session_enabled=True,
        )
        result = await rule.prepare(draft, _context())
        kernel = result.kernel_specs[0]
        assert kernel.internal_data["sudo_session_enabled"] is True
        assert kernel.internal_data["prevent_vfolder_mounts"] is True

    async def test_applies_to_every_kernel_draft(self, rule: BuildInternalDataRule) -> None:
        """Every kernel in the draft receives the same overlay."""
        draft = _draft(
            KernelSpecDraft(cluster_role="main"),
            KernelSpecDraft(cluster_role="worker"),
            sudo_session_enabled=True,
        )
        result = await rule.prepare(draft, _context())
        for k in result.kernel_specs:
            assert k.internal_data["sudo_session_enabled"] is True
