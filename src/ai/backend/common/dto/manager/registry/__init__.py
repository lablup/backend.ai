"""
Registry DTOs for Manager API.

Covers container registry, HuggingFace registry,
group registry quota, and artifact registry models (common-safe subset).

Note: Artifact registry models depending on manager-specific types
remain in ``ai.backend.manager.dto``.

Import directly from submodules:
- request: PatchContainerRegistryRequestModel, CreateRegistryQuotaReq, etc.
- response: PatchContainerRegistryResponseModel, RegistryQuotaResponse, etc.
"""
