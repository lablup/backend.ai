---
name: error-code-and-status-axes
type: design-rationale
description: The error-code triple and its no-underscore constraint, error code and HTTP status as independent axes, mixin-less base errors, GraphQL carrying only the code, absence of a central code registry, the separation from common/exception.py and the legacy manager/exceptions.py, the errors that stay on BackendAIError for want of a declared row type or of an action operation
scope: src/ai/backend/manager/errors
keywords: [BackendAIError, ErrorCode, ErrorDomain, ErrorOperation, ErrorDetail, ObjectNotFound, EntityError, FieldError, ActionOperationType, problem+json, exceptions.py]
sources:
  - src/ai/backend/common/exception.py
  - src/ai/backend/manager/actions/types.py
  - src/ai/backend/manager/api/rest/middleware/exception.py
  - src/ai/backend/manager/api/gql/extensions/exception_handler.py
generated:
  by: claude-code/opus-5
  at: 2026-09-11
status: stable
---

# Manager errors — Knowledge

> Rules: `AGENTS.md` in the same directory.

## Why this package exists

Domain errors are a public contract — every failure that leaves the manager
carries a machine-readable code and an RFC-7807 body, and clients branch on the
code instead of parsing messages. This package exists to keep that contract in
one place per domain.

## The code triple has exactly one format constraint

- `ErrorCode` is `(domain, operation, error_detail)`, rendered as `domain_operation_detail` and parsed by splitting on `_` — **no underscores in enum values** (hyphenate compound words).
- There is no central code registry — uniqueness is enforced nowhere, and the only machine-readable surface is the generated OpenAPI document.
- Before defining a new error, check both `manager/errors/` and `common/exception.py` (which holds about 40 concrete errors).

## Code and HTTP status are independent axes

- HTTP status comes solely from the class-base aiohttp mixin (`web.HTTPNotFound` → 404) — the code describes the failure, not the status.
- That is why concrete exceptions **must inherit a status mixin at definition time** — the defining side cannot know when an exception will surface externally (as an HTTP response), and a mixin-less exception that leaks out becomes a generic 500 instead of a meaningful status.
- Domain base errors (`RepositoryError` and 8 others) deliberately have no mixin — a status on the base would precede the subclass's own mixin in the MRO. Never raise them directly.
- GraphQL drops the status and carries only the code string in `extensions.code`; REST renders `problem+json`.
- A handler that leaks a non-`BackendAIError` exception loses the code — the middleware force-converts it to a generic code.

## Reuse by subclassing concrete errors

- `ObjectNotFound` builds its title from `object_name`, and about 20 domain not-found errors inherit it setting only `object_name`.
- When the meaning fits, extend an existing concrete error rather than deriving fresh from `BackendAIError`.

## An error stays on `BackendAIError` for want of a row type, or of an action operation

- Declaring the missing `EntityType` or `FieldType` reopens the first case.
- The second does not reopen: the entity and field bases take an
  `ActionOperationType`, and authenticating is not one, nor is starting an app.
  Neither gains a member — a permission and an audit record would have to name
  it too.

| Error | Why it stays |
|---|---|
| `RoleAlreadyAssigned`, `RoleNotAssigned` | the `user_roles` row has no `EntityType` or `FieldType` |
| `GroupMembershipNotFoundError` | it reads the `entity_memberships` edge, whose id is a plain `NewType` in `data/permission/id.py`, no `EntityType` |
| `ArtifactAssociationDeletionError`, `ArtifactAssociationNotFoundError` | the `association_artifacts_storages` row has no `FieldType` |
| `ContainerRegistryGroupsAssociationNotFound` | the `association_container_registries_groups` row has no `FieldType` |
| `InvalidFieldPermission` | validates a requested field scope for both permission entries and entity shares, so it names no one row kind |
| `VirtualEntityNotFound` | `data/entity/virtual_entity.py` declares an id alone, no `EntityType` |
| `NotEnoughPermission`, `InsufficientPrivilege`, `ContainerRegistryWebhookAuthorizationFailed`, `ImageAccessForbiddenError` | an authorization denial about the caller, not about a row |
| `InvalidCredentials`, `InvalidAuthParameters`, `AuthorizationFailed`, `OpenIDAuthenticationFailed` | the credentials are judged before a subject is settled, so no row is named |
| `InvalidClientIPConfig` | the manager's own client-address configuration, not a row |
| `PasswordExpired`, `LoginSessionExpiredError`, `LoginBlockedError`, `TooManyConcurrentLoginSessions` | a row is named, but what failed is the authentication — `ErrorOperation.AUTH`, which no `ActionOperationType` maps to |
| `DeploymentDefinitionFileReadError` | a file inside a vfolder, which no row type declares |
| `NoUpdatesToApply` | a modifier that changed nothing; the row is whichever one the caller was updating |
| `AppServiceStartFailed` | an app started inside a session is no row, and `ActionOperationType` has no `start` |
| `AppProxyConnectionError`, `AppProxyResponseError` | AppProxy is a system domain by the `AGENTS.md` table |
| `NotificationProcessingFailure`, `NotificationTemplateRenderingFailure` | a notification is rendered and delivered, and the message that comes out is no row; only the two notification tables have a type |
| `InvalidSecretKeyMaterial`, `SecretEncryptionMisconfigured` | the configured encryption keys and key providers, which no stored secret is read to reach |
| `ExportReportNotFound`, `InvalidExportFieldKeys` | a report is a `ReportDef` in a code-declared registry, not a row, and its field keys with it |
| `RetentionCategoryNotSupportedError` | a `RetentionCategory` with no cleanup wired — a gap in this build, not in a row |
| `QuotaScopeNotFoundError`, `StorageProxyNotFound` | neither quota scopes nor storage proxies declare a row kind |
| the four `Dotfile*` errors | dotfiles are a msgpack blob in a `keypairs` column, not rows |
| `VFolderBadRequest`, `VFolderOperationFailed`, `VFolderCreationFailure` | they report the storage-proxy call rather than the row, under a `generic` operation |
| `StorageProxyConnectionError`, `StorageProxyTimeoutError`, `UnexpectedStorageProxyResponseError` | the external call itself, under a `request` no `ActionOperationType` maps to |
| `VFolderPermissionError`, `VFolderInvalidParameter`, `InsufficientStoragePermission` | an authorization denial about the caller, or a parameter refused before a row is reached |
| `ModelCardParseError` | a model-definition file that does not parse, before any model card row exists |
| `VFolderFilterStatusNotAvailable` | the status-set alias names no entry in a constant map; the row-status half is `VFolderFilterStatusFailed` |
| `UnsupportedStorageTypeError`, `ObjectStorageOperationNotSupported` | a requested storage type, or a configured one offering no such operation |
| `AppNotFound` | an app absent from a session's `service_ports`, which is a value, not a row |
| `UnresolvableResourceGroup` | no group resolves at all, so it names none, and it reports `access` |
| `AgentNotAllocated` | a kernel with no agent assigned yet, reported under an `access` no `ActionOperationType` maps to |
| `InvalidUserUpdateMode`, `InvalidPresetQuery` | a request's own mode value, or a query naming neither id nor name |
| `NoCurrentTaskContext`, `DatabaseConnectionUnavailable`, `ConfigurationLoadFailed`, `DataTransformationFailed`, `DBOperationFailed` | the asyncio context, the connection, the configuration load or the database call itself |
| `BackendAgentError`, `KernelExecutionFailed`, `InvalidStreamMode` | they report `access` or `execute`, which no `ActionOperationType` maps to |
| `AgentConnectionUnavailable` | reaching an agent, under that same `access` |
| `InvalidSessionId`, `InvalidKernelConfig`, `IncompleteSessionSpec` | they refuse a request before it reaches a row; `IncompleteSessionSpec` is one of three `BackendAISchema.build_validation_error` overrides, a hook declared to return `BackendAIError` |
| the three `IdleCheckerAssignment*` errors | the assignment row's id is a `NewType`, with no `EntityType` |
| `IdlePolicyNotFound` | no idle-policy row type, and it is raised for absent config values rather than a row |
| `QuotaExceeded` | a resource-policy limit reached, not a condition of one row |
| `ConflictingSessionRescheduleNotSupported` | an unimplemented cleanup policy, not a condition of an agent row |
| `InvalidArtifactRegistryTypeError` | three of its four raise sites read a registry type off an event, naming no row |
| `ArtifactScanLimitExceededError` | bounds a scan request's `limit` before any row is named |
| `ArtifactImportDelegationError` | reports two returned lists disagreeing in length |
| `ArtifactDeletionError`, `RemoteReservoirArtifactImportError`, `ReservoirConnectionError`, `RemoteReservoirScanError` | report a storage-proxy or remote reservoir call failing |

## The legacy neighbor is a different kind

- `manager/exceptions.py` is internal non-HTTP plumbing (`AgentError`, `RPCError`, the kernel `status_data` TypedDict) — not domain errors.
- Beware the name collision: its `ErrorDetail` TypedDict is unrelated to the `ErrorDetail` enum in `common/exception.py`.
