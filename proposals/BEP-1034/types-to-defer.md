# KernelV2 GQL - Types to Defer

These types reference entities that should be represented as proper Relay Node connections. Since the corresponding Node types are not yet implemented, these fields/types should be **omitted** and added later.

---

## Summary

For each deferred Node type, we include the **ID field immediately** (for direct fetching) and defer only the **Node connection** (for full object resolution).

Node references are placed directly on `KernelV2GQL`:

| Node Field | Type |
|------------|------|
| `session_node` | `SessionNode \| None` |
| `user_node` | `UserNode \| None` |
| `keypair_node` | `KeypairNode \| None` |
| `domain_node` | `DomainNode \| None` |
| `project_node` | `GroupNode \| None` |
| `agent_node` | `AgentNode \| None` |
| `resource_group_node` | `ResourceGroupNode \| None` |
| `vfolder_nodes` | `VFolderConnection` |

ID fields are included in sub-info types:

| Sub-Info Type | ID Field |
|---------------|----------|
| `KernelSessionInfoGQL` | `session_id: uuid.UUID` |
| `KernelUserInfoGQL` | `user_id`, `access_key`, `domain_name`, `group_id` |
| `KernelResourceInfoGQL` | `agent_id`, `resource_group_name` |

---

## User/Auth Types (Defer to Node connections)

### KernelUserInfoGQL

This type includes ID fields immediately, with Node connections deferred:

| Field | Type | Include Now? | Future Node |
|-------|------|--------------|-------------|
| `user_id` | `uuid.UUID \| None` | Yes | `user: UserNode` |
| `access_key` | `str \| None` | Yes | `keypair: KeypairNode` |
| `domain_name` | `str \| None` | Yes | `domain: DomainNode` |
| `group_id` | `uuid.UUID \| None` | Yes | `project: GroupNode` |

**Action**: Include all ID fields now. Defer Node connections to future PRs.

**Resulting type (current PR)**:
```python
@strawberry.type(name="KernelUserInfo")
class KernelUserInfoGQL:
    user_id: uuid.UUID | None
    access_key: str | None
    domain_name: str | None
    group_id: uuid.UUID | None
```

**Future additions** (on `KernelV2GQL`):
- `user_node: UserNode | None`
- `keypair_node: KeypairNode | None`
- `domain_node: DomainNode | None`
- `project_node: GroupNode | None`

---

## Session Types (Defer to SessionNode)

### KernelSessionInfoGQL.session_id

**Action**: Include `session_id` field now. Defer `session: SessionNode` connection.

**Resulting type (current PR)**:
```python
@strawberry.type(name="KernelSessionInfo")
class KernelSessionInfoGQL:
    session_id: uuid.UUID
    creation_id: str | None
    name: str | None
    session_type: SessionTypes
```

**Future additions** (on `KernelV2GQL`):
- `session_node: SessionNode | None`

---

## Resource Types (Defer to Node connections)

### KernelResourceInfoGQL.resource_group

**Action**: Include `resource_group_name: str | None` field now. Defer `resource_group: ResourceGroupNode` connection.

**Future additions** (on `KernelV2GQL`):
- `resource_group_node: ResourceGroupNode | None`
- `agent_node: AgentNode | None`

---

## VFolder Types (Defer to VFolderNode)

**Future additions** (on `KernelV2GQL`):
- `vfolder_nodes: VFolderConnection`

---

## Future Implementation PRs

| PR | Node Field on `KernelV2GQL` |
|----|-------------------------|
| SessionNode PR | `session_node: SessionNode` |
| UserNode PR | `user_node: UserNode` |
| KeypairNode PR | `keypair_node: KeypairNode` |
| DomainNode PR | `domain_node: DomainNode` |
| GroupNode PR | `project_node: GroupNode` |
| AgentNode PR | `agent_node: AgentNode` |
| ResourceGroupNode PR | `resource_group_node: ResourceGroupNode` |
| VFolderNode PR | `vfolder_nodes: VFolderConnection` |
