"""UpdaterSpec implementations for keypair repository."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class KeyPairUpdaterSpec(UpdaterSpec[KeyPairRow]):
    """UpdaterSpec for keypair updates."""

    is_active: OptionalState[bool] = field(default_factory=OptionalState.nop)
    is_admin: OptionalState[bool] = field(default_factory=OptionalState.nop)
    resource_policy: OptionalState[str] = field(default_factory=OptionalState.nop)
    rate_limit: OptionalState[int] = field(default_factory=OptionalState.nop)

    @property
    @override
    def row_class(self) -> type[KeyPairRow]:
        return KeyPairRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.is_active.update_dict(to_update, "is_active")
        self.is_admin.update_dict(to_update, "is_admin")
        self.resource_policy.update_dict(to_update, "resource_policy")
        self.rate_limit.update_dict(to_update, "rate_limit")
        return to_update


@dataclass
class KeyPairSSHUpdaterSpec(UpdaterSpec[KeyPairRow]):
    """UpdaterSpec for writing SSH public/private keys to a keypair.

    Use ``TriState.update(value)`` to set a key, ``TriState.nullify()``
    to clear it, and ``TriState.nop()`` (the default) to leave it alone.
    """

    ssh_public_key: TriState[str] = field(default_factory=TriState.nop)
    ssh_private_key: TriState[str] = field(default_factory=TriState.nop)

    @property
    @override
    def row_class(self) -> type[KeyPairRow]:
        return KeyPairRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.ssh_public_key.update_dict(to_update, "ssh_public_key")
        self.ssh_private_key.update_dict(to_update, "ssh_private_key")
        return to_update
