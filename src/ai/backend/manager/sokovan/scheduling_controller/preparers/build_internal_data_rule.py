"""Per-kernel ``internal_data`` composition rule.

Ports the legacy :class:`.internal_data.InternalDataRule` into the
draft-based chain. Two overlay sources are merged onto every kernel
draft's ``internal_data`` mapping:

  * the DB-sourced ``context.dotfile_data`` — dotfiles and
    ``ssh_keypair`` the controller's batch fetch loaded from the
    keypair row and the group/domain dotfile tables.
  * the request-envelope ``draft.internal_data_extras`` — sudo toggle
    and deployment ``model_definition*`` overlay.

Legacy precedence is preserved:

  1. Whatever the caller placed on ``KernelSpecDraft.internal_data``
     (e.g. ``docker_credentials``, ``prevent_vfolder_mounts``,
     ``block_service_ports``, ``domain_socket_proxies``) forms the
     base mapping.
  2. The computed overlay is merged on top, overriding caller-supplied
     keys on conflict.

Overlay order:
``spec.internal_data → dotfile_data → model_definition_path → model_definition → sudo_session_enabled``.

No-op when every overlay source is empty.
"""

from __future__ import annotations

from typing import Any

from ai.backend.manager.data.session.draft import SessionSpecDraft
from ai.backend.manager.sokovan.scheduling_controller.preparers.draft_rule import (
    SessionSpecDraftRule,
    SessionSpecPreparationContext,
)


class BuildInternalDataRule(SessionSpecDraftRule):
    """Compose per-kernel ``internal_data`` from draft + context inputs."""

    def name(self) -> str:
        return "build_internal_data"

    async def prepare(
        self,
        draft: SessionSpecDraft,
        context: SessionSpecPreparationContext,
    ) -> SessionSpecDraft:
        extras = draft.internal_data_extras
        overlay: dict[str, Any] = context.dotfile_data.to_internal_data()
        if extras.model_definition_path is not None:
            overlay["model_definition_path"] = extras.model_definition_path
        if extras.model_definition is not None:
            overlay["model_definition"] = dict(extras.model_definition)
        if extras.sudo_session_enabled:
            overlay["sudo_session_enabled"] = True

        if not overlay:
            return draft

        new_kernels = tuple(
            k.model_copy(update={"internal_data": {**dict(k.internal_data), **overlay}})
            for k in draft.kernel_specs
        )
        return draft.model_copy(update={"kernel_specs": new_kernels})
