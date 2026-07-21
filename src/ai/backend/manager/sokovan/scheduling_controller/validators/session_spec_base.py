"""Base interfaces for ``SessionSpec``-based validators.

The draft-based preparer chain feeds a finalized :class:`SessionSpec`
straight into validation without reshaping. Each rule implements
:class:`SessionSpecValidatorRule` and the runner
:class:`SessionSpecValidator` applies the declared rule sequence
against a :class:`SessionSpecValidationContext` supplied by the
scheduling controller.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

from ai.backend.common.identifier.image import ImageID
from ai.backend.common.types import SlotName, SlotTypes
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.dotfile.types import DotfileBundle
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData, SlotTypePolicy
from ai.backend.manager.data.session.creation import ImageInfo
from ai.backend.manager.data.session.spec import SessionSpec

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass(frozen=True)
class SessionSpecValidationContext:
    """Read-only per-session state the validator chain consumes.

    Distinct from
    :class:`~ai.backend.manager.sokovan.scheduling_controller.preparers.draft_rule.SessionSpecPreparationContext`
    by design — prep-time and validate-time pre-fetches have different
    lifecycles and live in separate containers so controllers can wire
    them up independently.

    ``image_infos`` is intentionally duplicated with the preparer-side
    context: both phases need image metadata (prepare: minimum-slot
    fill / shmem; validate: min/max + service-port labels), and the
    controller pre-fetches the dict once and forwards to both.

    ``dotfile_data`` is a typed :class:`DotfileBundle` carrying the same
    snapshot loaded by ``_fetch_dotfile_data`` in the scheduler
    repository. :class:`.dotfile_vfolder_conflict_rule.DotfileVFolderConflictRule`
    reads it to detect path collisions between dotfile targets and
    resolved vfolder mounts — the conflict branch the legacy
    ``prepare_dotfiles`` used to run inline.

    ``pending_session_count`` feeds the ``PendingSessionCountLimitRule``
    so the validator can bound the user's pending-queue depth against
    ``max_pending_session_count`` on the keypair resource policy. The
    count is scoped per user (the session owner), not per access key.
    """

    keypair_resource_policy: KeyPairResourcePolicyData | None = None
    image_infos: Mapping[ImageID, ImageInfo] = field(default_factory=dict)
    known_slot_types: Mapping[SlotName, SlotTypes] = field(default_factory=dict)
    slot_type_policy: SlotTypePolicy = field(default_factory=SlotTypePolicy)
    dotfile_data: DotfileBundle = field(default_factory=DotfileBundle)
    pending_session_count: int = 0


class SessionSpecValidatorRule(ABC):
    """Abstract base class for SessionSpec-based validator rules."""

    @abstractmethod
    def name(self) -> str:
        """Return the validator rule name."""
        raise NotImplementedError

    @abstractmethod
    def validate(
        self,
        spec: SessionSpec,
        context: SessionSpecValidationContext,
    ) -> None:
        """Validate a finalized ``SessionSpec`` against the shared context.

        Raises:
            BackendAIError subclass (``InvalidAPIParameters``,
            ``QuotaExceeded``, ...) when validation fails.
        """
        raise NotImplementedError


class SessionSpecValidator:
    """Applies an ordered chain of :class:`SessionSpecValidatorRule` rules."""

    _rules: tuple[SessionSpecValidatorRule, ...]

    def __init__(self, rules: Iterable[SessionSpecValidatorRule]) -> None:
        self._rules = tuple(rules)

    def validate(
        self,
        spec: SessionSpec,
        context: SessionSpecValidationContext,
    ) -> None:
        for rule in self._rules:
            log.debug("Applying SessionSpec validation rule: {}", rule.name())
            rule.validate(spec, context)
