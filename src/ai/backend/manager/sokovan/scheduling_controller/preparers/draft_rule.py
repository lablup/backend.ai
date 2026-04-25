"""Draft-based preparer rule interface.

Each rule is a pure async function of ``(draft, context) -> draft``
that the :class:`SessionSpecPreparer` chains in declaration order. A
rule receives an immutable :class:`SessionSpecDraft` and returns a new
one via ``model_copy`` with additional fields resolved — never
mutating the input::

    draft_0 --rule_1--> draft_1 --rule_2--> ... --rule_N--> draft_final

Finalization (projecting the final draft into a
:class:`~ai.backend.manager.data.session.spec.SessionSpec`) is owned
by the preparer, not the rule surface — see
:class:`.session_spec_preparer.SessionSpecPreparer`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass, field

from ai.backend.common.identifier.image import ImageID
from ai.backend.common.types import VFolderMount
from ai.backend.manager.data.dotfile.types import DotfileBundle
from ai.backend.manager.data.session.draft import SessionSpecDraft
from ai.backend.manager.data.session.options import DefaultSessionOptions
from ai.backend.manager.repositories.scheduler.types.session_creation import (
    ContainerUserInfo,
    ImageInfo,
    ScalingGroupNetworkInfo,
)


@dataclass(frozen=True)
class SessionSpecPreparationContext:
    """Read-only per-session state carried through the preparer chain.

    Holds only the pre-fetched state the preparer rules read. Values
    used solely for post-preparation validation (resource policies,
    slot-type catalogs, active-session counts, ...) live on
    :class:`~.validators.session_spec_base.SessionSpecValidationContext`
    instead.

    ``vfolder_mounts_by_role`` is keyed by ``KernelGroup.role``. The
    controller's batch fetch resolves each group's mount requests into
    a ``VFolderMount`` tuple once and the preparer chain copies the
    tuple onto every :class:`KernelSpecDraft` whose ``cluster_role``
    matches — replicas of the same role share one entry without
    duplication. Empty dict when the request carried no mounts.
    """

    resource_group_defaults: DefaultSessionOptions
    resource_group_network: ScalingGroupNetworkInfo | None = None
    container_user_info: ContainerUserInfo | None = None
    image_infos: Mapping[ImageID, ImageInfo] = field(default_factory=dict)
    resource_group_allow_fractional: bool = False
    dotfile_data: DotfileBundle = field(default_factory=DotfileBundle)
    vfolder_mounts_by_role: Mapping[str, tuple[VFolderMount, ...]] = field(default_factory=dict)


class SessionSpecDraftRule(ABC):
    """Abstract base for draft-based preparer rules.

    Each rule is stateless with respect to a single session and MUST
    be a pure function of its inputs. Returning the same ``draft``
    instance unchanged is explicitly allowed when the rule has
    nothing to contribute.
    """

    @abstractmethod
    def name(self) -> str:
        """Short identifier used in logs and error messages."""
        raise NotImplementedError

    @abstractmethod
    async def prepare(
        self,
        draft: SessionSpecDraft,
        context: SessionSpecPreparationContext,
    ) -> SessionSpecDraft:
        """Return a new draft with this rule's fields resolved."""
        raise NotImplementedError
