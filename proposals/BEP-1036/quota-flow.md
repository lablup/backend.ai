# Artifact Storage Quota Flow Diagram

## Unified Import Flow with Quota Check

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         import_revision(action)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. Get revision_data (includes size)                                        │
│                                                                              │
│  2. Determine storage destination                                            │
│     ┌─────────────────────────────┬────────────────────────────────────┐    │
│     │    vfolder_id provided?     │                                    │    │
│     └──────────┬──────────────────┴────────────────────┬───────────────┘    │
│                │ YES                                   │ NO                  │
│                ▼                                       ▼                     │
│     ┌─────────────────────────┐          ┌─────────────────────────────┐    │
│     │  VFolderDestination     │          │  StorageNamespaceDestination│    │
│     │  - vfolder_id           │          │  - namespace_id             │    │
│     │  - quota_scope_id       │          │                             │    │
│     └───────────┬─────────────┘          └───────────────┬─────────────┘    │
│                 │                                         │                  │
│                 └──────────────┬──────────────────────────┘                  │
│                                ▼                                             │
│  3. ┌──────────────────────────────────────────────────────────────────┐    │
│     │            ArtifactStorageQuotaService.check_quota()             │    │
│     └──────────────────────────────────────────────────────────────────┘    │
│                                │                                             │
│                 ┌──────────────┴──────────────┐                              │
│                 ▼                              ▼                             │
│     ┌─────────────────────────┐    ┌─────────────────────────────────┐      │
│     │ _check_vfolder_quota()  │    │ _check_storage_namespace_quota()│      │
│     │                         │    │                                 │      │
│     │ See: vfolder_storage.md │    │ See: storage_namespace.md       │      │
│     └───────────┬─────────────┘    └───────────────┬─────────────────┘      │
│                 │                                   │                        │
│                 └──────────────┬────────────────────┘                        │
│                                ▼                                             │
│                 ┌──────────────────────────────┐                             │
│                 │     Quota Exceeded?          │                             │
│                 └──────────────┬───────────────┘                             │
│                    YES │              │ NO                                   │
│                        ▼              ▼                                      │
│     ┌─────────────────────────┐    ┌─────────────────────────────────┐      │
│     │ Raise appropriate error │    │ 4. Proceed with import          │      │
│     │ - VFolderQuotaExceeded  │    │    - Call storage proxy         │      │
│     │ - StorageNamespace      │    │    - Update status              │      │
│     │   QuotaExceeded         │    │    - Associate with storage     │      │
│     └─────────────────────────┘    └─────────────────────────────────┘      │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Data Sources for Quota Check

### StorageNamespace Quota

Usage is aggregated from artifact revisions linked to the namespace via the association table.

```
┌─────────────────────┐     ┌─────────────────────────────────┐
│ storage_namespace   │     │ association_artifacts_storages  │
├─────────────────────┤     ├─────────────────────────────────┤
│ id                  │◄────│ storage_namespace_id            │
│ max_size (NEW)      │     │ artifact_revision_id ───────────┼──┐
└─────────────────────┘     └─────────────────────────────────┘  │
                                                                  │
                            ┌─────────────────────────────────┐  │
                            │ artifact_revisions              │  │
                            ├─────────────────────────────────┤  │
                            │ id ◄────────────────────────────┼──┘
                            │ size                            │
                            └─────────────────────────────────┘

Usage = SUM(artifact_revisions.size) WHERE linked to namespace
```

### VFolder Quota

Usage is queried from the storage proxy, and limit comes from resource policies.

```
┌─────────────────────┐     ┌─────────────────────────────────┐
│ vfolders            │     │ user_resource_policies /        │
├─────────────────────┤     │ project_resource_policies       │
│ id                  │     ├─────────────────────────────────┤
│ quota_scope_id ─────┼────►│ max_quota_scope_size            │
└─────────────────────┘     └─────────────────────────────────┘
         │
         │ VFolderID
         ▼
┌─────────────────────┐
│ Storage Proxy       │
├─────────────────────┤
│ get_quota_scope_    │
│ usage(quota_scope)  │──► Current usage in bytes
└─────────────────────┘
```

## Quota Check Comparison

| Aspect | StorageNamespace | VFolder |
|--------|------------------|---------|
| Limit Source | `storage_namespace.max_size` | `resource_policy.max_quota_scope_size` |
| Usage Source | DB aggregation via association table | Storage proxy API |
| Unlimited Value | `NULL` | `-1` |
| Scope | Per namespace | Per quota scope (user/project) |
