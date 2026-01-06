---
Author: Gyubong Lee (gbl@lablup.com)
Status: Draft
Created: 2026-01-06
Created-Version: 26.1.0
Target-Version: 26.1.0
Implemented-Version:
---

# VFolder Destination Support for Artifact Import

## Motivation

Currently, when users import artifacts via the `import_artifacts` GraphQL mutation, the download destination is determined by the pre-configured `artifact_storage` in the system settings. This limits flexibility as users cannot choose where to store their imported models.

### Current Structure

The current artifact import flow works as follows:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Client (WebUI)                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ import_artifacts(artifactRevisionIds)
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                 Manager                                     │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  ArtifactRevisionService.import_revision()                            │  │
│  │    1. Load artifact & revision data from DB                           │  │
│  │    2. Read reservoir_config from settings                             │  │
│  │    3. Resolve storage_host from artifact_storage config               │  │
│  │    4. Build storage_step_mappings (DOWNLOAD, VERIFY, ARCHIVE)         │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ POST /import (with storage_step_mappings)
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             Storage Proxy                                   │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Import Pipeline                                                      │  │
│  │    1. DOWNLOAD: Fetch model from external registry (HuggingFace/etc)  │  │
│  │    2. VERIFY: Run verification (malware scan, etc.)                   │  │
│  │    3. ARCHIVE: Store to final destination                             │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                      │                                      │
│                                      ▼                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  StoragePool                                                          │  │
│  │    ├── VFSStorage (pre-configured from config file)                   │  │
│  │    └── ObjectStorage (pre-configured from config file)                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         artifact_storage (destination)                      │
│                                                                             │
│   Pre-configured in storage-proxy.toml:                                     │
│   ┌─────────────────────┐    or    ┌─────────────────────┐                  │
│   │  VFS Storage        │          │  Object Storage     │                  │
│   │  /path/to/artifacts │          │  s3://bucket/...    │                  │
│   └─────────────────────┘          └─────────────────────┘                  │
│                                                                             │
│   ⚠️  Cannot download directly to user's VFolder                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Limitation**: Models cannot be downloaded directly to user VFolders, which limits direct integration with Backend.AI's compute sessions and model serving features.

### Use Case: Model Store Integration

On the Model Store page, users need the ability to download models directly to their own vfolders:

1. User clicks the "Import Model to My VFolder" button on the Model Store page.
2. A vfolder selection page is displayed, where the user can create a model-type vfolder or select an existing one.
3. The selected vfolder ID is passed to the `import_artifacts` mutation, and the model is downloaded to that vfolder instead of the preconfigured storage.

This enhancement allows users to download models to:
- Their own VFS (Virtual File System)
- Object storage
- The model store

## Proposed Changes

### API Changes

Add an optional `vfolderId` parameter to the `import_artifacts` mutation:

```graphql
mutation {
  importArtifacts(
    input: {
      artifactRevisionIds: ["..."]
      vfolderId: "uuid-of-target-vfolder"  # New optional parameter
    }
  ) {
    ...
  }
}
```

When `vfolderId` is provided:
- The system resolves the vfolder's storage host and uses it for all import steps (DOWNLOAD, VERIFY, ARCHIVE)
- The vfolder's host format is `{proxy_name}:{volume_name}`, which is parsed to route requests correctly

### Architecture Changes

#### 1. VFolderStorage Class

Introduce a new `VFolderStorage` class that inherits from `AbstractStorage`.

**Why is VFolderStorage needed?**

The existing import pipeline is designed around the `AbstractStorage` interface with `storage_step_mappings` that map import steps to storage names. Rather than modifying the entire pipeline to handle vfolder paths directly, we create a `VFolderStorage` that:

- Implements the same `AbstractStorage` interface (stream_upload, stream_download, get_file_info, delete_file)
- Resolves the vfolder's base path using `volume.mangle_vfpath(vfid)`
- Integrates seamlessly with the existing pipeline without modifying service layer logic

This approach follows the Open/Closed Principle—extending functionality by adding a new class rather than modifying existing code extensively.

#### 2. Dynamic Storage Registration Pattern

**Why register and unregister VFolderStorage for each request?**

Unlike pre-configured storages (VFSStorage, ObjectStorage) that are created at server startup from configuration files, VFolderStorage instances are:

1. **Created on-demand**: Each request may target a different vfolder
2. **Transient by nature**: The storage is only needed for the duration of the import task
3. **Potentially numerous**: There could be thousands of vfolders, making pre-registration impractical

The lifecycle is managed as follows:

```
API Request with vfolderId
    │
    ▼
Create VFolderStorage (name: vfolder_{request_id})
    │
    ▼
Register to StoragePool
    │
    ▼
Start background import task ──► Return response to client
    │
    ▼
[Background task runs...]
    │
    ▼
Task completes (success or failure)
    │
    ▼
on_complete callback: Unregister from StoragePool
```

Using `request_id` in the storage name ensures uniqueness and traceability. The cleanup callback guarantees no memory leaks even if the import fails.
