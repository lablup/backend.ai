---
Author: Gyubong Lee (gbl@lablup.com)
Status: Draft
Created: 2025-01-21
Created-Version: 26.2.0
Target-Version: 26.2.0
Implemented-Version:
---

# BEP-1034: KernelV2 GQL Implementation

## Related Issues

- Parent: BEP-1010 (GraphQL API Migration to Strawberry)
- Reference PR: https://github.com/lablup/backend.ai/pull/8079

## Overview

This document defines the implementation plan for `KernelV2GQL` types as part of the Strawberry GraphQL migration. It specifies:

1. **Types to Include** - Types that will be implemented in the new PR
2. **Types to Skip** - Types that are replaced by other designs (do not implement)
3. **Types to Defer** - Types requiring Node connections (implement later)

Since we're creating a fresh PR, skipped types simply won't be included rather than being removed.

## Document Structure

| Document | Description |
|----------|-------------|
| [types-to-include.md](BEP-1034/types-to-include.md) | Detailed specifications of types to implement |
| [types-to-skip.md](BEP-1034/types-to-skip.md) | Types replaced by other designs |
| [types-to-defer.md](BEP-1034/types-to-defer.md) | Types requiring Node connections |

## Summary

### Types to Include

#### Enums
- `KernelStatusGQL` - Kernel status enum
- `KernelOrderFieldGQL` - Ordering field enum

#### Input Types (Filter/Order)
- `KernelStatusFilterGQL` - Status filter input
- `KernelFilterGQL` - Main filter input
- `KernelOrderByGQL` - Ordering input

#### Status Data Types
- `KernelStatusErrorInfoGQL` - Error information
- `KernelStatusDataGQL` - Kernel status data
- `KernelSessionStatusDataGQL` - Session status data
- `KernelStatusDataContainerGQL` - Container for status data

#### Statistics Types
- `KernelStatEntryGQL` - Single stat entry
- `KernelStatGQL` - Collection of stats

#### Internal Data Types
- `KernelInternalDataGQL` - Internal kernel data

#### Sub-Info Types
- `KernelSessionInfoGQL` - Session info
- `KernelClusterInfoGQL` - Cluster config
- `KernelUserPermissionInfoGQL` - User/permission info (partial - see deferred)
- `KernelDeviceModelInfoGQL` - Device model info
- `KernelAttachedDeviceEntryGQL` - Device entry
- `KernelAttachedDevicesGQL` - Attached devices collection
- `KernelResourceInfoGQL` - Resource allocation
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
- `SessionTypesGQL`, `SessionResultGQL` - Session enums
- `MountPermissionGQL`, `VFolderUsageModeGQL` - VFolder enums
- `ServicePortProtocolGQL` - Service port protocol enum
- `ResourceOptsEntryGQL`, `ResourceOptsGQL` - Resource options
- `ResourceOptsEntryInput`, `ResourceOptsInput` - Resource options input
- `ServicePortEntryGQL`, `ServicePortsGQL` - Service ports
- `MetricStatGQL`, `MetricValueGQL` - Metric types
- `DotfileInfoGQL`, `SSHKeypairGQL` - Internal data types

### Types to Skip (Do Not Implement)

| Type | Reason |
|------|--------|
| `SchedulerPredicateGQL` | Replaced by new scheduler design |
| `SchedulerInfoGQL` | Replaced by new scheduler design |
| `KernelStatusHistoryEntryGQL` | Replaced by new status tracking design |
| `KernelStatusHistoryGQL` | Replaced by new status tracking design |

### Types to Defer (Node Connections)

| Type/Field | Future Node | Action |
|------------|-------------|--------|
| `KernelImageInfoGQL` | `ImageNode` | Do not include |
| `KernelUserPermissionInfoGQL.user_uuid` | `UserNode` | Omit field |
| `KernelUserPermissionInfoGQL.group_id` | `GroupNode` | Omit field |
| `KernelRuntimeInfoGQL.vfolder_mounts` | `VFolderNode` | Omit field |

## Implementation Checklist

### PR Scope

- [ ] Implement all types listed in "Types to Include"
- [ ] Skip all types listed in "Types to Skip"
- [ ] Omit fields listed in "Types to Defer"
- [ ] Update `KernelLifecycleInfoGQL` to remove `status_history` field
- [ ] Update `KernelStatusDataContainerGQL` to remove `scheduler` field
- [ ] Update `from_kernel_info()` method to match new type structure

### Future PRs

- [ ] ImageNode PR: Add `image` connection
- [ ] UserNode PR: Add `owner` connection  
- [ ] GroupNode PR: Add `project` connection
- [ ] VFolderNode PR: Add `mounted_vfolders` connection

## References

- [BEP-1010: GraphQL API Migration to Strawberry](BEP-1010-new-gql.md)
- [PR #8079: Original KernelV2 Implementation](https://github.com/lablup/backend.ai/pull/8079)
