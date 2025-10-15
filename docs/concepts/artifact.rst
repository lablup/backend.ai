.. role:: raw-html-m2r(raw)
   :format: html

Artifact Management
===================

Artifacts
---------

Backend.AI's artifact registry manages AI models, packages, and images from external sources like HuggingFace Hub and Reservoir.

An **artifact** represents a computational resource that can be used within Backend.AI.
There are three types:

- **MODEL**: AI/ML models (neural networks, trained models)
- **PACKAGE**: Software packages, libraries, code repositories  
- **IMAGE**: Container images or executable environments

Each artifact contains metadata, registry information, and availability status.

Artifact Revisions
------------------

An **artifact revision** represents a specific version of an artifact (e.g., "main", "v1.0", "latest").
Each revision contains the actual files, version information, size, and README documentation.

Status Lifecycle
~~~~~~~~~~~~~~~~~

Artifact revisions progress through these statuses:

**SCANNED**
  Discovered in external registry, metadata registered, no files downloaded yet.

**PULLING** 
  Currently downloading from external source.

**PULLED**
  Downloaded to temporary storage, being moved to final location.

**AVAILABLE**
  Fully imported and ready for use in compute sessions.

Workflow
--------

1. **Scan**: Discovery of artifacts from external registries (HuggingFace, Reservoir)
2. **Import**: Download selected artifacts to Backend.AI storage  
3. **Use**: Mount artifacts in compute sessions as volumes
4. **Cleanup**: Remove files while keeping metadata to free storage space

Artifact Registries
-------------------

**External registries** are sources where artifacts originate:

- **HuggingFace Hub**: Primary source for AI/ML models and datasets
- **Reservoir**: Backend.AI's internal registry for enterprise deployments

**Local registries** are Backend.AI's internal storage where artifacts are cached for access.

Storage and Access
-----------------

- Artifacts are stored in object storage using S3-compatible APIs
- Files are accessed securely through presigned URLs
- Storage is organized by namespaces for logical separation
- Access is controlled through Backend.AI's standard authentication and authorization
