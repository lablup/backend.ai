# Services Layer

← [Back to Manager](../README.md#manager-architecture-documentation) | [Architecture Overview](../../README.md#manager)

## Overview

The Services layer encapsulates the business logic of Backend.AI Manager. This layer performs domain-specific operations and provides clear input/output interfaces through Actions and ActionResults.

## Architecture

```
API Layer (api/, api/gql)
    ↓
Action Processor (actions/)  ← Authorization and Service invocation
    ↓
Services Layer (services/)  ← Current document (Business logic)
    ↓
Repositories Layer (repositories/)  ← Data access and transaction management
    ↓
Database Models (models/)
```

## Standard Operations

Services implement 6 standard operations:

1. **create** - Create new entity
2. **get** - Retrieve single entity
3. **search** - Query with filters
4. **update** - Update entity
5. **delete** - Delete entity
6. **purge** - Permanently remove entity

**Batch operations:**
- `batch_update` - Update multiple entities
- `batch_delete` - Delete multiple entities
- `batch_purge` - Permanently remove multiple entities

**Method naming (no prefix):**
```python
# Service methods accept Actions and return ActionResults
await service.create_user(action: CreateUserAction)
await service.user(action: GetUserAction)  # getter uses entity name
await service.search_users(action: SearchUsersAction)
await service.update_user(action: UpdateUserAction)
await service.delete_user(action: DeleteUserAction)
await service.purge_user(action: PurgeUserAction)
await service.batch_update_users(action: BatchUpdateUsersAction)
await service.batch_delete_users(action: BatchDeleteUsersAction)
await service.batch_purge_users(action: BatchPurgeUsersAction)
```

**See:** `/service-guide` skill for detailed implementation patterns.

## Key Responsibilities

### 1. Business Logic Implementation
- Apply domain-specific rules and constraints
- Orchestrate complex workflows
- Validate and transform data

### 2. External Service Orchestration
- Communicate with external components via Clients package (Agent, Storage Proxy, etc.)
- Publish events and handle notifications
- Coordinate multiple external service calls

### 3. Quota and Limit Enforcement
- Check resource quotas
- Verify usage limits
- Apply policy-based constraints

**Note**: Authorization is handled by the Action Processor layer, and transaction management is the responsibility of the Repository layer.


## Directory Structure

```
services/
├── session/              # Session lifecycle management
├── deployment/          # Deployment management (App Proxy integration)
├── vfolder/            # Virtual folder management
├── scaling_group/      # Scaling group management
├── user/               # User management
├── group/              # Group management
├── kernel/             # Kernel management
└── ...
```

## Design Principles

### 1. Single Responsibility Principle

Each service is responsible for only one domain area.

```python
# Good example - Clear single responsibility
class SessionService:
    """Manages session lifecycle only"""
    async def get_session_info(
        self,
        action: GetSessionInfoAction,
    ) -> GetSessionInfoActionResult:
        ...

    async def destroy_session(
        self,
        action: DestroySessionAction,
    ) -> DestroySessionActionResult:
        ...

# Bad example - Multiple domains mixed
class MixedService:
    """Manages sessions, users, and groups - Unclear responsibility"""
    async def create_session_and_update_user(self, ...):
        ...
```

### 2. Action/ActionResult Pattern

All service methods accept an Action as input and return an ActionResult.

```python
# Action definition
@dataclass
class GetSessionInfoAction(SessionAction):
    session_name: str
    owner_access_key: AccessKey

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_info"

# ActionResult definition
@dataclass
class GetSessionInfoActionResult(BaseActionResult):
    session_info: LegacySessionInfo
    session_data: SessionData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.session_data.id)

# Service method
class SessionService:
    async def get_session_info(
        self,
        action: GetSessionInfoAction,
    ) -> GetSessionInfoActionResult:
        # Perform business logic
        session = await self._session_repository.get_session_validated(
            action.session_name,
            action.owner_access_key,
        )

        session_info = self._build_session_info(session)

        return GetSessionInfoActionResult(
            session_info=session_info,
            session_data=session.to_dataclass(),
        )
```

### 3. Repository Pattern Utilization

Data access is performed only through Repositories.

```python
class SessionService:
    _session_repository: SessionRepository

    async def get_session_info(
        self,
        action: GetSessionInfoAction,
    ) -> GetSessionInfoActionResult:
        # Query data through Repository
        session = await self._session_repository.get_session_validated(
            action.session_name,
            action.owner_access_key,
        )

        # Process business logic
        await self._validate_session_access(session)
        session_info = self._build_session_info(session)

        return GetSessionInfoActionResult(
            session_info=session_info,
            session_data=session.to_dataclass(),
        )
```

### 4. Explicit Exception Handling

Exceptions are defined as domain exceptions inheriting from BackendAIError and are raised explicitly.

```python
# Exception definitions
class SessionError(BackendAIError):
    """Base exception for session service"""
    pass

class SessionNotFound(SessionError):
    """Session not found"""
    def __init__(self, session_name: str) -> None:
        super().__init__(f"Session {session_name} not found")

class InvalidSessionState(SessionError):
    """Invalid session state"""
    def __init__(self, message: str) -> None:
        super().__init__(message)

# Raising exceptions in Service
async def destroy_session(
    self,
    action: DestroySessionAction,
) -> DestroySessionActionResult:
    session = await self._session_repository.get_session_validated(
        action.session_name,
        action.owner_access_key,
    )

    # Validate state
    if session.status not in TERMINATABLE_STATUSES:
        raise InvalidSessionState(
            f"Cannot terminate session in {session.status} state"
        )

    # Perform business logic
    await self._do_destroy_session(session)

    return DestroySessionActionResult(session_id=str(session.id))
```

**Note**: Avoid the pattern of catching and re-raising exceptions. Exceptions are handled at the Action Processor or API Layer.

## Common Patterns

### 1. External Service Calls

Communicate with external services through the Clients package.

```python
from ai.backend.manager.clients.storage_proxy import StorageProxyClient

class VFolderService:
    _storage_proxy_client: StorageProxyClient

    async def upload_file(
        self,
        action: UploadFileAction,
    ) -> UploadFileActionResult:
        # Query VFolder information
        vfolder = await self._vfolder_repository.get_vfolder(
            action.vfolder_name,
            action.owner_access_key,
        )

        # Upload file through Storage Proxy
        upload_result = await self._storage_proxy_client.upload_file(
            vfolder_id=vfolder.id,
            file_path=action.file_path,
            file_content=action.file_content,
        )

        return UploadFileActionResult(
            file_id=upload_result.file_id,
            file_size=upload_result.size,
        )
```

### 2. Coordinating Multiple Repositories

```python
async def create_session_with_vfolders(
    self,
    action: CreateSessionAction,
) -> CreateSessionActionResult:
    # Orchestrate business logic across multiple Repositories
    # (Transactions are managed within each Repository method)

    # 1. Validate VFolders
    vfolders = await self._vfolder_repository.get_vfolders(
        action.vfolder_names,
        action.owner_access_key,
    )

    # 2. Check quota
    quota = await self._user_repository.get_resource_quota(
        action.owner_access_key
    )
    if not self._check_quota(action.requested_slots, quota):
        raise InsufficientQuota("Resource quota exceeded")

    # 3. Create session
    session = await self._session_repository.create_session(action)

    # 4. Attach VFolders
    await self._vfolder_repository.attach_to_session(
        vfolders,
        session.id,
    )

    return CreateSessionActionResult(session_id=str(session.id))
```

## Type Definitions

### Action Definitions

Actions define the input for service methods.

```python
@dataclass
class CreateSessionAction(SessionAction):
    """Session creation request"""
    image: str
    type: SessionType
    cluster_size: int
    requested_slots: ResourceSlot
    vfolder_mounts: list[VFolderMount]
    environ: dict[str, str]
    scaling_group: str
    owner_access_key: AccessKey

    @override
    def entity_id(self) -> Optional[str]:
        return None  # No ID yet for creation request

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "create"

@dataclass
class DestroySessionAction(SessionAction):
    """Session termination request"""
    session_name: str
    owner_access_key: AccessKey
    forced: bool = False

    @override
    def entity_id(self) -> Optional[str]:
        return self.session_name

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "destroy"
```

### ActionResult Definitions

ActionResults define the output of service methods.

```python
@dataclass
class CreateSessionActionResult(BaseActionResult):
    """Session creation result"""
    session_id: str
    service_ports: list[ServicePort]

    @override
    def entity_id(self) -> Optional[str]:
        return self.session_id

@dataclass
class DestroySessionActionResult(BaseActionResult):
    """Session termination result"""
    session_id: str
    terminated_at: datetime

    @override
    def entity_id(self) -> Optional[str]:
        return self.session_id
```

### Domain Data Structures

Domain data used in business logic is defined as dataclasses.

```python
@dataclass(frozen=True)
class VFolderMount:
    """VFolder mount information"""
    name: str
    mount_path: str
    permission: VFolderPermission

@dataclass(frozen=True)
class ServicePort:
    """Service port information"""
    name: str
    protocol: str
    port: int
```

## Error Handling

### Exception Hierarchy

Each service defines domain-specific exceptions.

```python
# services/session/exceptions.py
class SessionError(BackendAIError):
    """Base exception for session service"""
    pass

class SessionNotFound(SessionError):
    """Session not found"""
    def __init__(self, session_name: str) -> None:
        super().__init__(f"Session {session_name} not found")

class InvalidSessionState(SessionError):
    """Invalid session state"""
    def __init__(self, message: str) -> None:
        super().__init__(message)

class InsufficientQuota(SessionError):
    """Insufficient quota"""
    def __init__(self, message: str) -> None:
        super().__init__(message)

class SessionCreationFailed(SessionError):
    """Session creation failed"""
    pass
```

### Exception Usage

```python
async def create_session(
    self,
    action: CreateSessionAction,
) -> CreateSessionActionResult:
    # Check quota
    quota = await self._user_repository.get_resource_quota(
        action.owner_access_key
    )
    if not self._check_quota(action.requested_slots, quota):
        # Explicitly raise exception
        raise InsufficientQuota("Resource quota exceeded")

    # Validate image
    image_info = await self._session_repository.resolve_image(action.image)
    if not image_info:
        raise InvalidImageName(f"Image {action.image} not found")

    # Create session
    session = await self._session_repository.create_session(action)

    return CreateSessionActionResult(session_id=str(session.id))
```

**Note**: Avoid the pattern of catching exceptions for transformation or logging. Exceptions are propagated directly to the upper layers.

## Testing Strategy

### Unit Testing

Service logic is tested by mocking Repositories.

```python
# tests/manager/services/test_session_service.py
async def test_create_session(
    mock_session_repository: Mock,
    mock_vfolder_repository: Mock,
    mock_user_repository: Mock,
) -> None:
    # Given
    service = SessionService(
        session_repository=mock_session_repository,
        vfolder_repository=mock_vfolder_repository,
        user_repository=mock_user_repository,
    )

    action = CreateSessionAction(
        image="python:3.11",
        type=SessionType.INTERACTIVE,
        requested_slots=ResourceSlot(...),
        owner_access_key=AccessKey("AKIAIOSFODNN7EXAMPLE"),
        ...
    )

    mock_user_repository.get_resource_quota.return_value = ResourceSlot(...)
    mock_session_repository.create_session.return_value = SessionRow(...)

    # When
    result = await service.create_session(action)

    # Then
    assert result.session_id is not None
    mock_session_repository.create_session.assert_called_once()
```

## Performance Considerations

### Early Return

Check conditions early to keep code concise.

```python
async def list_sessions(
    self,
    action: ListSessionsAction,
) -> ListSessionsActionResult:
    # Early return for cleaner code
    if not action.filters:
        return ListSessionsActionResult(sessions=[])

    # Perform actual logic
    sessions = await self._session_repository.list_sessions(
        action.owner_access_key,
        action.filters,
    )

    return ListSessionsActionResult(sessions=sessions)
```

## Best Practices

### 1. Break Down into Small Methods

Break complex logic into multiple small private methods.

```python
async def create_session(
    self,
    action: CreateSessionAction,
) -> CreateSessionActionResult:
    # Public method orchestrates the overall flow
    await self._validate_session_spec(action)
    quota = await self._check_resource_quota(action)
    vfolders = await self._validate_vfolders(action)

    session = await self._session_repository.create_session(action)
    await self._attach_vfolders(session.id, vfolders)
    await self._publish_creation_event(session)

    return CreateSessionActionResult(session_id=str(session.id))

async def _validate_session_spec(self, action: CreateSessionAction) -> None:
    """Validate session specification"""
    ...

async def _check_resource_quota(
    self,
    action: CreateSessionAction,
) -> ResourceSlot:
    """Check resource quota"""
    ...

async def _validate_vfolders(
    self,
    action: CreateSessionAction,
) -> list[VFolderRow]:
    """Validate VFolders"""
    ...
```

### 2. Use Immutable Data Structures

Keep input data immutable.

```python
@dataclass(frozen=True)
class CreateSessionAction(SessionAction):
    """Immutability guaranteed with frozen=True"""
    image: str
    type: SessionType
    requested_slots: ResourceSlot
    ...
```

### 3. Clear Naming

Method and variable names should clearly convey intent.

```python
# Good examples
async def get_session_info(
    self,
    action: GetSessionInfoAction,
) -> GetSessionInfoActionResult:
    """Query session information"""
    ...

async def destroy_session(
    self,
    action: DestroySessionAction,
) -> DestroySessionActionResult:
    """Terminate session"""
    ...

# Bad examples
async def process(self, data: dict) -> dict:
    """Ambiguous name"""
    ...

async def handle(self, id: str) -> None:
    """Unclear intent"""
    ...
```

## Implementation Guide

This section provides practical guidance for implementing new services following Backend.AI patterns.

**For comprehensive step-by-step instructions, see the `/service-guide` skill.**

### Quick Start Checklist

When creating a new service:

1. ✅ Define operations enum in `types.py`
2. ✅ Create `actions/base.py` with base action classes
3. ✅ Implement concrete actions in `actions/{operation}.py`
4. ✅ Define service protocol in `service.py`
5. ✅ Implement service methods
6. ✅ Create processor package in `processors.py`
7. ✅ Write tests with mocked repositories (see `/tdd-guide`)
8. ✅ Integrate with API handlers (see `/api-guide`)

### Directory Structure

Services follow a standardized structure:

```
services/{domain}/
├── __init__.py
├── types.py                # Domain types and operation enums
├── service.py              # Service protocol and implementation
├── processors.py           # Processor package for orchestration
└── actions/
    ├── __init__.py
    ├── base.py            # Base action/result classes
    ├── create.py          # Create operation
    ├── update.py          # Update operation
    └── delete.py          # Delete operation
```

**Example**: See `services/storage_namespace/` for complete implementation.

### Actions File Structure

#### Base Actions (`actions/base.py`)

Define abstract base classes for all actions in the domain:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..types import StorageNamespaceOperation

if TYPE_CHECKING:
    from ai.backend.manager.types import StorageNamespaceId


@dataclass(frozen=True)
class StorageNamespaceAction:
    """Base class for storage namespace actions."""

    def entity_id(self) -> str:
        """Return unique identifier for the entity being acted upon."""
        raise NotImplementedError

    def operation_type(self) -> StorageNamespaceOperation:
        """Return the type of operation being performed."""
        raise NotImplementedError


@dataclass(frozen=True)
class StorageNamespaceActionResult:
    """Base class for storage namespace action results."""

    def entity_id(self) -> str:
        """Return unique identifier for the entity that was acted upon."""
        raise NotImplementedError
```

**Key Requirements:**
- Actions are immutable (`frozen=True`)
- Implement `entity_id()` for tracking
- Implement `operation_type()` for categorization
- Use `TYPE_CHECKING` for type-only imports

#### Concrete Actions (`actions/create.py`, etc.)

Each operation gets its own file:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .base import StorageNamespaceAction, StorageNamespaceActionResult
from ..types import StorageNamespaceOperation

if TYPE_CHECKING:
    from ai.backend.common.types import BinarySize
    from ai.backend.manager.types import StorageNamespaceId


@dataclass(frozen=True)
class CreateStorageNamespaceAction(StorageNamespaceAction):
    """Action to create a new storage namespace."""

    name: str
    sgroup_name: str
    domain_name: str
    usage_mode: UsageMode
    permission: Permission
    resource_limit: BinarySize | None = None

    def entity_id(self) -> str:
        return self.name

    def operation_type(self) -> StorageNamespaceOperation:
        return StorageNamespaceOperation.CREATE


@dataclass(frozen=True)
class CreateStorageNamespaceActionResult(StorageNamespaceActionResult):
    """Result of creating a storage namespace."""

    namespace_id: StorageNamespaceId

    def entity_id(self) -> str:
        return str(self.namespace_id)
```

**Naming Conventions:**
- Action: `{Verb}{Entity}Action` (e.g., `CreateStorageNamespaceAction`)
- Result: `{ActionName}Result` (e.g., `CreateStorageNamespaceActionResult`)
- Operation enum: `{VERB}` (e.g., `StorageNamespaceOperation.CREATE`)

### Processors Pattern

Processors orchestrate action execution with hooks, metrics, and middleware:

```python
from ai.backend.manager.services.processors import (
    AbstractProcessorPackage,
    ActionProcessor,
)


class StorageNamespaceProcessorPackage(AbstractProcessorPackage):
    """Processor package for storage namespace operations."""

    def __init__(
        self,
        service: StorageNamespaceServiceProtocol,
    ) -> None:
        self._service = service
        self._create_processor = ActionProcessor[
            CreateStorageNamespaceAction,
            CreateStorageNamespaceActionResult,
        ](
            action_name="create_storage_namespace",
            handler=service.create_storage_namespace,
        )

    @property
    def create_storage_namespace(
        self,
    ) -> ActionProcessor[
        CreateStorageNamespaceAction,
        CreateStorageNamespaceActionResult,
    ]:
        return self._create_processor
```

**Key Components:**
- **ProcessorPackage**: Container for all domain processors
- **ActionProcessor**: Wraps service method with:
  - Pre/post hook execution
  - Metrics collection
  - Error handling
  - Logging
- **Property Pattern**: Expose processors as properties for clean API

### Service Implementation Workflow

#### 1. Define Service Protocol

```python
from typing import Protocol


class StorageNamespaceServiceProtocol(Protocol):
    """Protocol defining storage namespace service interface."""

    async def create_storage_namespace(
        self,
        action: CreateStorageNamespaceAction,
    ) -> CreateStorageNamespaceActionResult:
        """Create a new storage namespace."""
        ...
```

#### 2. Implement Service Methods

```python
class StorageNamespaceService:
    """Service for storage namespace operations."""

    def __init__(
        self,
        repository: StorageNamespaceRepository,
    ) -> None:
        self._repository = repository

    async def create_storage_namespace(
        self,
        action: CreateStorageNamespaceAction,
    ) -> CreateStorageNamespaceActionResult:
        """Create a new storage namespace.

        Args:
            action: Action containing namespace creation parameters

        Returns:
            Result containing created namespace ID

        Raises:
            StorageNamespaceAlreadyExists: If namespace with same name exists
            InvalidStorageNamespace: If namespace parameters are invalid
        """
        # 1. Validate action parameters
        if not action.name:
            raise InvalidStorageNamespace("Namespace name cannot be empty")

        # 2. Check business rules
        existing = await self._repository.get_by_name(action.name)
        if existing:
            raise StorageNamespaceAlreadyExists(
                f"Namespace '{action.name}' already exists"
            )

        # 3. Create entity via repository
        namespace_id = await self._repository.create(
            name=action.name,
            sgroup_name=action.sgroup_name,
            domain_name=action.domain_name,
            usage_mode=action.usage_mode,
            permission=action.permission,
            resource_limit=action.resource_limit,
        )

        # 4. Return result
        return CreateStorageNamespaceActionResult(namespace_id=namespace_id)
```

**Method Structure:**
1. **Validate**: Check action parameters
2. **Business Logic**: Apply domain rules
3. **Repository Calls**: Coordinate data access
4. **Return Result**: Create ActionResult

### Repository Integration

Services coordinate with repositories for data access:

```python
class DomainService:
    def __init__(
        self,
        domain_repository: DomainRepository,
        user_repository: UserRepository,
        group_repository: GroupRepository,
    ) -> None:
        self._domain_repo = domain_repository
        self._user_repo = user_repository
        self._group_repo = group_repository

    async def create_domain_with_admin(
        self,
        action: CreateDomainWithAdminAction,
    ) -> CreateDomainWithAdminActionResult:
        # Coordinate multiple repositories
        domain_id = await self._domain_repo.create(action.domain_name)
        user_id = await self._user_repo.create(
            username=action.admin_username,
            domain_id=domain_id,
        )
        await self._group_repo.add_user_to_group(
            user_id=user_id,
            group_name=f"{action.domain_name}-admins",
        )

        return CreateDomainWithAdminActionResult(
            domain_id=domain_id,
            admin_user_id=user_id,
        )
```

**See `/repository-guide` for repository implementation patterns.**

### Action Naming Conventions

Follow these patterns for consistency:

**Create Operations:**
```python
CreateStorageNamespaceAction / CreateStorageNamespaceActionResult
StorageNamespaceOperation.CREATE
```

**Update Operations:**
```python
UpdateStorageNamespaceAction / UpdateStorageNamespaceActionResult
StorageNamespaceOperation.UPDATE
```

**Delete Operations:**
```python
DeleteStorageNamespaceAction / DeleteStorageNamespaceActionResult
StorageNamespaceOperation.DELETE
```

**Domain-Specific Operations:**
```python
ArchiveStorageNamespaceAction / ArchiveStorageNamespaceActionResult
StorageNamespaceOperation.ARCHIVE
```

### Testing Services

**Critical Rule**: Service tests MUST NOT use real database. Mock repositories instead.

```python
from unittest.mock import AsyncMock, Mock
import pytest


@pytest.fixture
def database_engine() -> None:
    """Raise error if service test tries to use database."""
    raise RuntimeError(
        "Service tests must not use database. "
        "Mock repositories instead."
    )


@pytest.fixture
def mock_repository() -> Mock:
    """Mock repository for testing."""
    repo = Mock()
    repo.get_by_name = AsyncMock(return_value=None)
    repo.create = AsyncMock(return_value=StorageNamespaceId("test-id"))
    return repo


@pytest.fixture
def service(mock_repository: Mock) -> StorageNamespaceService:
    """Service instance with mocked repository."""
    return StorageNamespaceService(repository=mock_repository)


async def test_create_storage_namespace_success(
    service: StorageNamespaceService,
    mock_repository: Mock,
) -> None:
    """Test successful namespace creation."""
    # Given
    action = CreateStorageNamespaceAction(
        name="test-namespace",
        sgroup_name="default",
        domain_name="default",
        usage_mode=UsageMode.GENERAL,
        permission=Permission.RW,
    )

    # When
    result = await service.create_storage_namespace(action)

    # Then
    assert result.namespace_id == StorageNamespaceId("test-id")
    mock_repository.get_by_name.assert_called_once_with("test-namespace")
    mock_repository.create.assert_called_once()
```

**See `/tdd-guide` for complete test-driven development workflow.**

## Service-Specific Documentation

Detailed documentation for individual service implementations:

### Core Services
- **[Session Service](./session/README.md)**: Session lifecycle management and execution
  - Session creation and validation
  - Session state management
  - Resource allocation and cleanup

- **[User Service](./user/README.md)**: User account and authentication management
  - User creation and profile management
  - Authentication and credential handling

- **[Domain Service](./domain/README.md)**: Multi-tenant domain management
  - Domain creation and configuration
  - Domain-level settings and policies

### Resource Policy Services
- **[Resource Preset Service](./resource_preset/README.md)**: Resource template management
  - Predefined resource configurations
  - Resource allocation templates

- **[Keypair Resource Policy Service](./keypair_resource_policy/README.md)**: Access key-level resource policies
  - Per-keypair resource limits
  - Access key quota management

- **[Project Resource Policy Service](./project_resource_policy/README.md)**: Project-level resource policies
  - Project resource quotas
  - Multi-user resource sharing policies

- **[User Resource Policy Service](./user_resource_policy/README.md)**: User-level resource policies
  - Per-user resource limits
  - User quota management

### Monitoring Services
- **[Metric Service](./metric/README.md)**: Container metrics collection and querying
  - Prometheus integration
  - Resource utilization metrics
  - Time-series data queries

## References

### Related Documentation
- [Action Processor Layer](../actions/README.md): Permission validation and request handling
- [Repositories Layer](../repositories/README.md): Data access and query patterns
- [Sokovan Orchestration](../sokovan/README.md): Session scheduling and orchestration
- [Manager Overview](../README.md): Manager component architecture
