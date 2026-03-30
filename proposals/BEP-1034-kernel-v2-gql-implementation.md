---
Author: Gyubong Lee (gbl@lablup.com)
Status: Draft
Created: 2025-01-21
Created-Version: 26.2.0
Target-Version: 26.2.0
Implemented-Version:
---

# BEP-1034: KernelV2 GQL Implementation

## Overview

This document defines the implementation plan for `KernelV2GQL` types as part of the Strawberry GraphQL migration (BEP-1010). It specifies:

1. **Types to Include** - Types that will be implemented
2. **Types to Skip** - Types replaced by other designs
3. **Types to Defer** - Types requiring Node connections (implement later)

## Document Structure

| Document | Description |
|----------|-------------|
| [types-to-include.md](BEP-1034/types-to-include.md) | Detailed specifications of types to implement |
| [types-to-skip.md](BEP-1034/types-to-skip.md) | Types replaced by other designs |
| [types-to-defer.md](BEP-1034/types-to-defer.md) | Types requiring Node connections |

## Summary

### Types to Include

#### Enums
- [`KernelOrderField`](BEP-1034/types-to-include.md#kernelorderfield) - Ordering field enum

#### Input Types (Filter/Order)
- [`KernelStatusFilterGQL`](BEP-1034/types-to-include.md#kernelstatusfiltergql) - Status filter input
- [`KernelFilterGQL`](BEP-1034/types-to-include.md#kernelfiltergql) - Main filter input
- [`KernelOrderByGQL`](BEP-1034/types-to-include.md#kernelorderbygql) - Ordering input

#### Sub-Info Types
- [`KernelSessionInfoGQL`](BEP-1034/types-to-include.md#kernelsessioninfogql) - Session info
- [`KernelClusterInfoGQL`](BEP-1034/types-to-include.md#kernelclusterinfogql) - Cluster config
- [`KernelUserInfoGQL`](BEP-1034/types-to-include.md#kerneluserinfogql) - User/permission info
- [`ResourceAllocationGQL`](BEP-1034/types-to-include.md#resourceallocationgql) - Resource allocation (requested/used)
- [`KernelResourceInfoGQL`](BEP-1034/types-to-include.md#kernelresourceinfogql) - Resource info
- [`KernelNetworkInfoGQL`](BEP-1034/types-to-include.md#kernelnetworkinfogql) - Network config
- [`KernelLifecycleInfoGQL`](BEP-1034/types-to-include.md#kernellifecycleinfogql) - Lifecycle info (partial - see skipped)

> **Note**: `image_id` and `startup_command` are inlined directly on `KernelV2GQL` (single-element types removed)

#### Main Types
- [`KernelV2GQL`](BEP-1034/types-to-include.md#kernelv2gql) - Main kernel node type
- [`KernelEdgeGQL`](BEP-1034/types-to-include.md#kerneledgegql) - Edge type
- [`KernelConnectionV2GQL`](BEP-1034/types-to-include.md#kernelconnectionv2gql) - Connection type

#### Common Types (from common/types.py)
- `ResourceOptsEntryGQL`, `ResourceOptsGQL`, `ResourceOptsEntryInput`, `ResourceOptsInput` - Resource options (already exist)
- [`ServicePortEntryGQL`, `ServicePortsGQL`](BEP-1034/types-to-include.md#service-port-types) - Service ports

### Types to Skip (Do Not Implement)

| Type | Reason |
|------|--------|
| `SchedulerPredicateGQL` | Replaced by new scheduler design |
| `SchedulerInfoGQL` | Replaced by new scheduler design |
| `KernelStatusHistoryEntryGQL` | Replaced by new status tracking design |
| `KernelStatusHistoryGQL` | Replaced by new status tracking design |

### Types to Defer (Node Connections Only)

For each deferred Node type, we include the **ID field now** and defer only the **Node connection**.

Node references are placed directly on `KernelV2GQL`:

| Node Field | Type |
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

## Implementation Checklist

### PR Scope

- [ ] Implement all types listed in "Types to Include"
- [ ] Skip all types listed in "Types to Skip"
- [ ] Include ID fields for deferred Node types:
  - `KernelUserInfoGQL`: include `user_id`, `access_key`, `domain_name`, `group_id`
  - `KernelSessionInfoGQL`: include `session_id`, `creation_id`
  - `KernelResourceInfoGQL`: include `agent_id`, `resource_group_name`
- [ ] Update `KernelLifecycleInfoGQL` to remove `status_history`, `status_info`, `status_data`, `status_changed` fields
- [ ] Update `from_kernel_info()` method to match new type structure

### Future PRs

- [ ] ImageNode PR: Implement `image_node: ImageNode` on `KernelV2GQL`
- [ ] SessionNode PR: Implement `session_node: SessionNode` on `KernelV2GQL`
- [ ] UserNode PR: Implement `user_node: UserNode` on `KernelV2GQL`
- [ ] KeypairNode PR: Implement `keypair_node: KeypairNode` on `KernelV2GQL`
- [ ] DomainNode PR: Implement `domain_node: DomainNode` on `KernelV2GQL`
- [ ] GroupNode PR: Implement `project_node: GroupNode` on `KernelV2GQL`
- [ ] AgentNode PR: Implement `agent_node: AgentNode` on `KernelV2GQL`
- [ ] ResourceGroupNode PR: Implement `resource_group_node: ResourceGroupNode` on `KernelV2GQL`
- [ ] VFolderNode PR: Implement `vfolder_nodes: VFolderConnection` on `KernelV2GQL`

## References

- [BEP-1010: GraphQL API Migration to Strawberry](BEP-1010-new-gql.md)
- [PR #8292: ImageNode Implementation](https://github.com/lablup/backend.ai/pull/8292)
