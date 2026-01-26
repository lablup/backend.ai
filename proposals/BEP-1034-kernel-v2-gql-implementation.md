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

#### Input Types (Filter/Order)
- `KernelStatusFilterGQL` - Status filter input
- `KernelFilterGQL` - Main filter input
- `KernelOrderByGQL` - Ordering input

#### Status Data Types
- `KernelStatusErrorInfoGQL` - Error information
- `KernelStatusDataGQL` - Kernel status data
- `KernelSessionStatusDataGQL` - Session status data
- `KernelStatusDataContainerGQL` - Container for status data

#### Internal Data Types
- `KernelInternalDataGQL` - Internal kernel data

#### Sub-Info Types
- `KernelSessionInfoGQL` - Session info (session_id deferred)
- `KernelClusterInfoGQL` - Cluster config
- `KernelUserPermissionInfoGQL` - Unix process permissions only (most fields deferred)
- `KernelDeviceModelInfoGQL` - Device model info
- `KernelAttachedDeviceEntryGQL` - Device entry
- `KernelAttachedDevicesGQL` - Attached devices collection
- `KernelResourceInfoGQL` - Resource allocation (scaling_group deferred, agent included)
- `KernelRuntimeInfoGQL` - Runtime config (partial - see deferred)
- `KernelNetworkInfoGQL` - Network config
- `KernelLifecycleInfoGQL` - Lifecycle info (partial - see skipped)
- `KernelMetricsInfoGQL` - Metrics info
- `KernelMetadataInfoGQL` - Metadata

#### Main Types
- `KernelV2GQL` - Main kernel node type
- `KernelEdgeGQL` - Edge type
- `KernelConnectionV2GQL` - Connection type

#### Common Types (from common/types.py)
- `ResourceOptsEntryGQL`, `ResourceOptsGQL` - Resource options
- `ResourceOptsEntryInput`, `ResourceOptsInput` - Resource options input
- `ServicePortEntryGQL`, `ServicePortsGQL` - Service ports
- `DotfileInfoGQL`, `SSHKeypairGQL` - Internal data types

### Types to Skip (Do Not Implement)

| Type | Reason |
|------|--------|
| `SchedulerPredicateGQL` | Replaced by new scheduler design |
| `SchedulerInfoGQL` | Replaced by new scheduler design |
| `KernelStatusHistoryEntryGQL` | Replaced by new status tracking design |
| `KernelStatusHistoryGQL` | Replaced by new status tracking design |

### Types to Defer (Node Connections Only)

For each deferred Node type, we include the **ID field now** and defer only the **Node connection**.

| Type/Field | ID Field (Include Now) | Future Node (Defer) |
|------------|------------------------|---------------------|
| `KernelV2GQL` | `image_ref: str` | `image: ImageNode` |
| `KernelUserPermissionInfoGQL` | `user_id`, `access_key`, `domain_name`, `group_id` | `user`, `keypair`, `domain`, `project` |
| `KernelSessionInfoGQL` | `session_id: uuid.UUID` | `session: SessionNode` |
| `KernelResourceInfoGQL` | `scaling_group_name: str` | `scaling_group: ScalingGroupNode` |
| `KernelRuntimeInfoGQL` | `vfolder_ids: list[uuid.UUID]` | `vfolders: list[VFolderNode]` |

**Types to skip entirely**: `KernelImageInfoGQL`, `VFolderMountGQL`

## Implementation Checklist

### PR Scope

- [ ] Implement all types listed in "Types to Include"
- [ ] Skip all types listed in "Types to Skip"
- [ ] Include ID fields for deferred Node types:
  - `KernelV2GQL`: add `image_id`
  - `KernelUserPermissionInfoGQL`: include `user_id`, `access_key`, `domain_name`, `group_id` (plus `uid`, `main_gid`, `gids`)
  - `KernelSessionInfoGQL`: include `session_id`
  - `KernelResourceInfoGQL`: include `agent_id`, `scaling_group_name`
  - `KernelRuntimeInfoGQL`: include `vfolder_ids`
- [ ] Update `KernelLifecycleInfoGQL` to remove `status_history`, `status_info`, `status_data`, `status_changed` fields
- [ ] Update `KernelStatusDataContainerGQL` to remove `scheduler` field
- [ ] Update `from_kernel_info()` method to match new type structure

### Future PRs

- [ ] ImageNode PR: Add `image: ImageNode` to `KernelV2GQL`
- [ ] UserNode PR: Add `user: UserNode` to `KernelUserPermissionInfoGQL`
- [ ] KeypairNode PR: Add `keypair: KeypairNode` to `KernelUserPermissionInfoGQL`
- [ ] DomainNode PR: Add `domain: DomainNode` to `KernelUserPermissionInfoGQL`
- [ ] GroupNode PR: Add `project: GroupNode` to `KernelUserPermissionInfoGQL`
- [ ] SessionNode PR: Add `session: SessionNode` to `KernelSessionInfoGQL`
- [ ] ScalingGroupNode PR: Add `scaling_group: ScalingGroupNode` to `KernelResourceInfoGQL`
- [ ] VFolderNode PR: Add `vfolders: list[VFolderNode]` to `KernelRuntimeInfoGQL`

## References

- [BEP-1010: GraphQL API Migration to Strawberry](BEP-1010-new-gql.md)
