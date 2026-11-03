# KernelV2 GQL - 미룰 타입

이 타입들은 적절한 Relay Node 연결로 표현해야 하는 엔티티를 참조한다. 해당 Node 타입이 아직 없으므로 이 필드와 타입은 **빼고** 나중에 추가한다.

---

## 요약

미룬 Node 타입마다 **ID 필드는 바로** 포함하고(직접 조회용) **Node 연결**만 미룬다(객체 전체 조회용).

Node 참조는 `KernelV2GQL` 에 바로 둔다.

| Node 필드 | 타입 |
|------------|------|
| `session_node` | `SessionNode \| None` |
| `user_node` | `UserNode \| None` |
| `keypair_node` | `KeypairNode \| None` |
| `domain_node` | `DomainNode \| None` |
| `project_node` | `GroupNode \| None` |
| `agent_node` | `AgentNode \| None` |
| `resource_group_node` | `ResourceGroupNode \| None` |
| `vfolder_nodes` | `VFolderConnection` |

ID 필드는 하위 정보 타입에 포함한다.

| 하위 정보 타입 | ID 필드 |
|---------------|----------|
| `KernelSessionInfoGQL` | `session_id: uuid.UUID` |
| `KernelUserInfoGQL` | `user_id`, `access_key`, `domain_name`, `group_id` |
| `KernelResourceInfoGQL` | `agent_id`, `resource_group_name` |

---

## 사용자, 인증 타입(Node 연결로 미룸)

### KernelUserInfoGQL

이 타입은 ID 필드를 바로 포함하고 Node 연결은 미룬다.

| 필드 | 타입 | 지금 포함 | 이후 Node |
|-------|------|--------------|-------------|
| `user_id` | `uuid.UUID \| None` | 예 | `user: UserNode` |
| `access_key` | `str \| None` | 예 | `keypair: KeypairNode` |
| `domain_name` | `str \| None` | 예 | `domain: DomainNode` |
| `group_id` | `uuid.UUID \| None` | 예 | `project: GroupNode` |

**동작**: ID 필드를 모두 지금 포함한다. Node 연결은 이후 PR 로 미룬다.

**이번 PR 의 결과 타입**:
```python
@strawberry.type(name="KernelUserInfo")
class KernelUserInfoGQL:
    user_id: uuid.UUID | None
    access_key: str | None
    domain_name: str | None
    group_id: uuid.UUID | None
```

**이후 추가**(`KernelV2GQL`):
- `user_node: UserNode | None`
- `keypair_node: KeypairNode | None`
- `domain_node: DomainNode | None`
- `project_node: GroupNode | None`

---

## 세션 유형(SessionNode 로 미룸)

### KernelSessionInfoGQL.session_id

**동작**: `session_id` 필드를 지금 포함한다. `session: SessionNode` 연결은 미룬다.

**이번 PR 의 결과 타입**:
```python
@strawberry.type(name="KernelSessionInfo")
class KernelSessionInfoGQL:
    session_id: uuid.UUID
    creation_id: str | None
    name: str | None
    session_type: SessionTypes
```

**이후 추가**(`KernelV2GQL`):
- `session_node: SessionNode | None`

---

## 자원 타입(Node 연결로 미룸)

### KernelResourceInfoGQL.resource_group

**동작**: `resource_group_name: str | None` 필드를 지금 포함한다. `resource_group: ResourceGroupNode` 연결은 미룬다.

**이후 추가**(`KernelV2GQL`):
- `resource_group_node: ResourceGroupNode | None`
- `agent_node: AgentNode | None`

---

## VFolder 타입(VFolderNode 로 미룸)

**이후 추가**(`KernelV2GQL`):
- `vfolder_nodes: VFolderConnection`

---

## 이후 구현 PR

| PR | `KernelV2GQL` 의 Node 필드 |
|----|-------------------------|
| SessionNode PR | `session_node: SessionNode` |
| UserNode PR | `user_node: UserNode` |
| KeypairNode PR | `keypair_node: KeypairNode` |
| DomainNode PR | `domain_node: DomainNode` |
| GroupNode PR | `project_node: GroupNode` |
| AgentNode PR | `agent_node: AgentNode` |
| ResourceGroupNode PR | `resource_group_node: ResourceGroupNode` |
| VFolderNode PR | `vfolder_nodes: VFolderConnection` |
