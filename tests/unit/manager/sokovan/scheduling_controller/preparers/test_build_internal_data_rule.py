"""Tests for ``BuildInternalDataRule``.

Verifies the session-level overlay onto per-kernel ``internal_data``:

  * dotfile/ssh_keypair from the context flow onto every kernel draft
  * ``model_definition_path`` / ``model_definition`` / ``sudo_session_enabled``
    are added only when their input values are present
  * caller-pre-populated keys on a kernel's ``internal_data`` survive
    unless the overlay explicitly sets the same key (legacy precedence)
  * empty inputs result in a no-op
"""

from __future__ import annotations

import pytest

from ai.backend.manager.data.session.draft import (
    KernelSpecDraft,
    SessionSpecDraft,
)
from ai.backend.manager.data.session.options import DefaultSessionOptions
from ai.backend.manager.sokovan.scheduling_controller.preparers.build_internal_data_rule import (
    BuildInternalDataRule,
)
from ai.backend.manager.sokovan.scheduling_controller.preparers.draft_rule import (
    InternalDataInputs,
    SessionSpecPreparationContext,
)


@pytest.fixture
def rule() -> BuildInternalDataRule:
    return BuildInternalDataRule()


def _context(**inputs: object) -> SessionSpecPreparationContext:
    return SessionSpecPreparationContext(
        resource_group_defaults=DefaultSessionOptions(),
        internal_data_inputs=InternalDataInputs(**inputs),  # type: ignore[arg-type]
    )


def _draft_with_kernels(*kernels: KernelSpecDraft) -> SessionSpecDraft:
    return SessionSpecDraft(kernel_specs=kernels)


class TestBuildInternalDataRule:
    async def test_noop_when_all_inputs_empty(self, rule: BuildInternalDataRule) -> None:
        """Zero overlay keys returns the draft unchanged."""
        draft = _draft_with_kernels(KernelSpecDraft(cluster_role="main"))
        result = await rule.prepare(draft, _context())
        assert result is draft

    async def test_overlay_dotfile_data(self, rule: BuildInternalDataRule) -> None:
        """Dotfile/ssh_keypair entries from the context land on each kernel."""
        dotfiles = [{"path": "/etc/profile.d/bai.sh", "data": "echo hi"}]
        ssh = {"public_key": "ssh-rsa A", "private_key": "-----..."}
        draft = _draft_with_kernels(KernelSpecDraft(cluster_role="main"))

        result = await rule.prepare(
            draft,
            _context(dotfile_data={"dotfiles": dotfiles, "ssh_keypair": ssh}),
        )

        kernel = result.kernel_specs[0]
        assert kernel.internal_data["dotfiles"] == dotfiles
        assert kernel.internal_data["ssh_keypair"] == ssh

    async def test_overlay_deployment_keys(self, rule: BuildInternalDataRule) -> None:
        """Model-definition / path flow through when supplied."""
        draft = _draft_with_kernels(KernelSpecDraft(cluster_role="main"))
        result = await rule.prepare(
            draft,
            _context(
                model_definition_path="/models/foo.yaml",
                model_definition={"kind": "Model", "name": "foo"},
            ),
        )
        kernel = result.kernel_specs[0]
        assert kernel.internal_data["model_definition_path"] == "/models/foo.yaml"
        assert kernel.internal_data["model_definition"] == {
            "kind": "Model",
            "name": "foo",
        }

    async def test_sudo_flag_only_added_when_true(self, rule: BuildInternalDataRule) -> None:
        """``sudo_session_enabled=False`` is not emitted into the overlay."""
        draft = _draft_with_kernels(KernelSpecDraft(cluster_role="main"))

        off = await rule.prepare(draft, _context(sudo_session_enabled=False))
        assert off is draft  # no overlay keys → no-op

        on = await rule.prepare(draft, _context(sudo_session_enabled=True))
        assert on.kernel_specs[0].internal_data == {"sudo_session_enabled": True}

    async def test_overlay_overrides_caller_keys_on_conflict(
        self, rule: BuildInternalDataRule
    ) -> None:
        """Legacy precedence: overlay wins on key conflict."""
        draft = _draft_with_kernels(
            KernelSpecDraft(
                cluster_role="main",
                internal_data={
                    "sudo_session_enabled": False,  # will be overwritten
                    "prevent_vfolder_mounts": True,  # caller-only key, survives
                },
            ),
        )
        result = await rule.prepare(draft, _context(sudo_session_enabled=True))
        kernel = result.kernel_specs[0]
        assert kernel.internal_data["sudo_session_enabled"] is True
        assert kernel.internal_data["prevent_vfolder_mounts"] is True

    async def test_applies_to_every_kernel_draft(self, rule: BuildInternalDataRule) -> None:
        """Every kernel in the draft receives the same overlay."""
        draft = _draft_with_kernels(
            KernelSpecDraft(cluster_role="main"),
            KernelSpecDraft(cluster_role="worker"),
        )
        result = await rule.prepare(draft, _context(sudo_session_enabled=True))
        for k in result.kernel_specs:
            assert k.internal_data["sudo_session_enabled"] is True
