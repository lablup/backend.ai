@dataclass
class GroupModifiableFields:
    name: OptionalState[str] = field(default_factory=OptionalState.nop)
    domain_name: OptionalState[str] = field(default_factory=OptionalState.nop)
    description: OptionalState[str] = field(default_factory=OptionalState.nop)
    total_resource_slots: OptionalState[dict[str, Any]] = field(default_factory=OptionalState.nop)
    allowed_vfolder_hosts: OptionalState[list[str]] = field(default_factory=OptionalState.nop)
    integration_id: OptionalState[str] = field(default_factory=OptionalState.nop)
    is_active: OptionalState[bool] = field(default_factory=OptionalState.nop)
    resource_policy: OptionalState[str] = field(default_factory=OptionalState.nop)