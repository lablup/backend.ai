"""Types for session creation and enqueueing."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from ai.backend.common.identifier.image import ImageID
from ai.backend.common.types import (
    SessionId,
    SlotName,
    SlotTypes,
)
from ai.backend.manager.data.dotfile.types import DotfileBundle
from ai.backend.manager.data.resource.types import SlotTypePolicy
from ai.backend.manager.data.session.creation import (
    ContainerUserInfo,
    ImageInfo,
    ScalingGroupNetworkInfo,
)
from ai.backend.manager.models.scaling_group import ScalingGroupOpts


@dataclass
class SessionDependencyData:
    """Data for session dependency relationships."""

    session_id: SessionId
    depends_on: SessionId


@dataclass
class AllowedScalingGroup:
    """Allowed scaling group for a user."""

    name: str
    is_private: bool
    scheduler_opts: ScalingGroupOpts


@dataclass
class SessionSpecContextFetch:
    """Raw data fetched by ``ScheduleDBSource.fetch_session_spec_contexts``.

    Kept as a plain record so the repository layer does not need to
    import sokovan's scheduling-controller types (which would create a
    circular import: preparer/validator types pull data-layer types
    defined right here). The controller converts this bundle into its
    typed :class:`SessionSpecPreparationContext` +
    :class:`SessionSpecValidationContext` pair.
    """

    resource_group_defaults: Any  # DefaultSessionOptions (avoid data-layer import here)
    resource_group_network: ScalingGroupNetworkInfo | None
    container_user_info: ContainerUserInfo
    image_infos: dict[ImageID, ImageInfo]
    resource_group_allow_fractional: bool
    dotfile_data: DotfileBundle
    keypair_resource_policy: Any | None  # KeyPairResourcePolicyData
    known_slot_types: Mapping[SlotName, SlotTypes] = field(default_factory=dict)
    slot_type_policy: SlotTypePolicy = field(default_factory=SlotTypePolicy)
    active_session_count: int = 0
