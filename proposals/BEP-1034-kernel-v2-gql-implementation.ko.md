# BEP-1034: KernelV2 GQL 구현

## 개요

이 문서는 Strawberry GraphQL 이관(BEP-1010)의 일부로 `KernelV2GQL` 타입 구현 계획을 정한다. 다음을 다룬다.

1. **포함할 타입** - 구현할 타입
2. **건너뛸 타입** - 다른 설계로 대체되는 타입
3. **미룰 타입** - Node 연결이 필요한 타입(나중에 구현)

## 문서 구조

| 문서 | 설명 |
|----------|-------------|
| [types-to-include.md](BEP-1034/types-to-include.md) | 구현할 타입의 상세 명세 |
| [types-to-skip.md](BEP-1034/types-to-skip.md) | 다른 설계로 대체되는 타입 |
| [types-to-defer.md](BEP-1034/types-to-defer.md) | Node 연결이 필요한 타입 |

## 요약

### 포함할 타입

#### enum
- [`KernelOrderField`](BEP-1034/types-to-include.md#kernelorderfield) - 정렬 필드 enum

#### 입력 타입(필터, 정렬)
- [`KernelStatusFilterGQL`](BEP-1034/types-to-include.md#kernelstatusfiltergql) - 상태 필터 입력
- [`KernelFilterGQL`](BEP-1034/types-to-include.md#kernelfiltergql) - 기본 필터 입력
- [`KernelOrderByGQL`](BEP-1034/types-to-include.md#kernelorderbygql) - 정렬 입력

#### 하위 정보 타입
- [`KernelSessionInfoGQL`](BEP-1034/types-to-include.md#kernelsessioninfogql) - 세션 정보
- [`KernelClusterInfoGQL`](BEP-1034/types-to-include.md#kernelclusterinfogql) - 클러스터 구성
- [`KernelUserInfoGQL`](BEP-1034/types-to-include.md#kerneluserinfogql) - 사용자, 권한 정보
- [`ResourceAllocationGQL`](BEP-1034/types-to-include.md#resourceallocationgql) - 자원 할당(요청, 사용)
- [`KernelResourceInfoGQL`](BEP-1034/types-to-include.md#kernelresourceinfogql) - 자원 정보
- [`KernelNetworkInfoGQL`](BEP-1034/types-to-include.md#kernelnetworkinfogql) - 네트워크 구성
- [`KernelLifecycleInfoGQL`](BEP-1034/types-to-include.md#kernellifecycleinfogql) - 수명 주기 정보(일부, 건너뛴 타입 참고)

> **참고**: `image_id` 와 `startup_command` 는 `KernelV2GQL` 에 직접 인라인한다(단일 항목 타입은 제거).

#### 주요 타입
- [`KernelV2GQL`](BEP-1034/types-to-include.md#kernelv2gql) - 기본 kernel node 타입
- [`KernelEdgeGQL`](BEP-1034/types-to-include.md#kerneledgegql) - edge 타입
- [`KernelConnectionV2GQL`](BEP-1034/types-to-include.md#kernelconnectionv2gql) - connection 타입

#### 공통 타입(common/types.py)
- `ResourceOptsEntryGQL`, `ResourceOptsGQL`, `ResourceOptsEntryInput`, `ResourceOptsInput` - 자원 옵션(이미 있음)
- [`ServicePortEntryGQL`, `ServicePortsGQL`](BEP-1034/types-to-include.md#service-port-types) - 서비스 포트

### 건너뛸 타입(구현하지 않음)

| 타입 | 이유 |
|------|--------|
| `SchedulerPredicateGQL` | 새 scheduler 설계로 대체 |
| `SchedulerInfoGQL` | 새 scheduler 설계로 대체 |
| `KernelStatusHistoryEntryGQL` | 새 상태 추적 설계로 대체 |
| `KernelStatusHistoryGQL` | 새 상태 추적 설계로 대체 |

### 미룰 타입(Node 연결만)

미룬 Node 타입마다 **ID 필드는 지금** 포함하고 **Node 연결**만 미룬다.

Node 참조는 `KernelV2GQL` 에 바로 둔다.

| Node 필드 | 타입 |
|------------|------|
| `image_node` | `ImageNode \| None` |
| `session_node` | `SessionNode \| None` |
| `user_node` | `UserNode \| None` |
| `keypair_node` | `KeypairNode \| None` |
| `domain_node` | `DomainNode \| None` |
| `project_node` | `GroupNode \| None` |
| `agent_node` | `AgentNode \| None` |
| `resource_group_node` | `ResourceGroupNode \| None` |
| `vfolder_nodes` | `VFolderConnection` |

## 구현 체크리스트

### PR 범위

- [ ] "포함할 타입"에 나열한 타입을 모두 구현한다
- [ ] "건너뛸 타입"에 나열한 타입을 모두 건너뛴다
- [ ] 미룬 Node 타입의 ID 필드를 포함한다.
  - `KernelUserInfoGQL`: `user_id`, `access_key`, `domain_name`, `group_id` 를 포함한다
  - `KernelSessionInfoGQL`: `session_id`, `creation_id` 를 포함한다
  - `KernelResourceInfoGQL`: `agent_id`, `resource_group_name` 을 포함한다
- [ ] `KernelLifecycleInfoGQL` 에서 `status_history`, `status_info`, `status_data`, `status_changed` 필드를 제거한다
- [ ] `from_kernel_info()` 메서드를 새 타입 구조에 맞게 수정한다

### 이후 PR

- [ ] ImageNode PR: `KernelV2GQL` 에 `image_node: ImageNode` 를 구현한다
- [ ] SessionNode PR: `KernelV2GQL` 에 `session_node: SessionNode` 를 구현한다
- [ ] UserNode PR: `KernelV2GQL` 에 `user_node: UserNode` 를 구현한다
- [ ] KeypairNode PR: `KernelV2GQL` 에 `keypair_node: KeypairNode` 를 구현한다
- [ ] DomainNode PR: `KernelV2GQL` 에 `domain_node: DomainNode` 를 구현한다
- [ ] GroupNode PR: `KernelV2GQL` 에 `project_node: GroupNode` 를 구현한다
- [ ] AgentNode PR: `KernelV2GQL` 에 `agent_node: AgentNode` 를 구현한다
- [ ] ResourceGroupNode PR: `KernelV2GQL` 에 `resource_group_node: ResourceGroupNode` 를 구현한다
- [ ] VFolderNode PR: `KernelV2GQL` 에 `vfolder_nodes: VFolderConnection` 을 구현한다

## 참고

- [BEP-1010: GraphQL API Migration to Strawberry](BEP-1010-new-gql.md)
- [PR #8292: ImageNode Implementation](https://github.com/lablup/backend.ai/pull/8292)
