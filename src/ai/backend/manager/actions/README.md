# Action Processor Layer

## Overview

The Action Processor layer wraps the Services layer to handle cross-cutting concerns such as authorization, monitoring, and logging. This layer sits between the API layer and Services layer, performing necessary validation and monitoring before and after Action execution.

## Architecture

```
API Layer (api/, api/gql)
    ↓
Action Processor (actions/)  ← Current document (Authorization, Monitoring)
    ↓
Services Layer (services/)  ← Business logic
    ↓
Repositories Layer (repositories/)
    ↓
Database Models (models/)
```

## Key Responsibilities

### 1. Authorization
- RBAC (Role-Based Access Control) permission checking
- Resource access authorization
- Domain-specific permission policies

### 2. Validation
- Action input data validation
- Pre-validation of business rules
- Resource state verification

### 3. Monitoring
- Audit log recording
- Prometheus metrics collection
- Pre and post Action execution monitoring

### 4. Action Execution Orchestration
- Service method invocation
- Exception handling and transformation
- Result return

## Directory Structure

```
actions/
├── action/              # Base classes for Action and ActionResult
│   ├── base.py         # BaseAction, BaseActionResult
│   ├── single_entity.py
│   ├── batch.py
│   └── scope.py
├── processor/          # Action processing logic
│   ├── base.py         # ActionProcessor, ActionRunner
│   ├── single_entity.py
│   ├── batch.py
│   └── scope.py
├── validator/          # Validation logic
│   └── base.py         # ActionValidator abstract class
├── validators/         # Concrete validation implementations
│   ├── auth_validator.py
│   └── rbac/          # RBAC validation
├── monitors/          # Monitoring implementations
│   ├── monitor.py     # ActionMonitor abstract class
│   ├── audit_log.py   # Audit log recording
│   └── prometheus.py  # Prometheus metrics
└── types.py           # Common type definitions
```

## Core Components

### 1. BaseAction

Base class for all Actions.

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

@dataclass
class BaseAction(ABC):
    """Base Action class"""

    @abstractmethod
    def entity_id(self) -> Optional[str]:
        """Target entity ID (None if not applicable)"""
        ...

    @classmethod
    @abstractmethod
    def entity_type(cls) -> str:
        """Entity type (e.g., "session", "vfolder")"""
        ...

    @classmethod
    @abstractmethod
    def operation_type(cls) -> str:
        """Operation type (e.g., "create", "delete", "get_info")"""
        ...

    def spec(self) -> dict:
        """Action specification (for logging/monitoring)"""
        return {}
```

### 2. BaseActionResult

Base class for all ActionResults.

```python
@dataclass
class BaseActionResult(ABC):
    """Base ActionResult class"""

    @abstractmethod
    def entity_id(self) -> Optional[str]:
        """Result entity ID"""
        ...
```

### 3. ActionProcessor

Core class that processes Actions.

```python
class ActionProcessor:
    """Action processor"""
    _validators: list[ActionValidator]
    _runner: ActionRunner

    def __init__(
        self,
        validators: list[ActionValidator],
        runner: ActionRunner,
    ) -> None:
        self._validators = validators
        self._runner = runner

    async def _run(
        self,
        action: BaseAction,
        meta: BaseActionTriggerMeta,
    ) -> ProcessResult:
        """Execute Action"""
        # 1. Validation
        for validator in self._validators:
            await validator.validate(action, meta)

        # 2. Service execution
        result = await self._runner.run(action, meta)

        return ProcessResult(action=action, result=result)
```

### 4. ActionValidator

Abstract class for performing validation.

```python
from abc import ABC, abstractmethod

class ActionValidator(ABC):
    """Action validation interface"""

    @abstractmethod
    async def validate(
        self,
        action: BaseAction,
        meta: BaseActionTriggerMeta,
    ) -> None:
        """Perform validation - raise exception on failure"""
        ...
```

### 5. ActionMonitor

Abstract class for performing monitoring.

```python
from abc import ABC

class ActionMonitor(ABC):
    """Action monitoring interface"""

    async def prepare(
        self,
        action: BaseAction,
        meta: BaseActionTriggerMeta,
    ) -> None:
        """Preparation before Action execution"""
        ...

    async def done(
        self,
        action: BaseAction,
        result: ProcessResult,
    ) -> None:
        """Processing after Action execution"""
        ...
```

## Action Processing Flow

```
API Request
    ↓
1. Create Action (API Layer)
    ↓
2. Invoke ActionProcessor
    ↓
3. Monitor.prepare() - Start monitoring
    ↓
4. Validator.validate() - Authorization and validation
    ├─ RBAC Validator (permission check)
    ├─ Auth Validator (authentication check)
    └─ Domain-specific Validators
    ↓
5. ActionRunner.run() - Invoke Service method
    ↓
6. Monitor.done() - Complete monitoring
    ↓
7. Return ActionResult
    ↓
API Response
```

## Usage Examples

### 1. Action Definition

```python
from dataclasses import dataclass
from typing import Optional

from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.action import BaseAction, BaseActionResult

@dataclass
class GetSessionInfoAction(BaseAction):
    """Action to query session information"""
    session_name: str
    owner_access_key: AccessKey

    def entity_id(self) -> Optional[str]:
        return None  # No specific ID for query

    @classmethod
    def entity_type(cls) -> str:
        return "session"

    @classmethod
    def operation_type(cls) -> str:
        return "get_info"

    def spec(self) -> dict:
        return {
            "session_name": self.session_name,
            "owner_access_key": str(self.owner_access_key),
        }


@dataclass
class GetSessionInfoActionResult(BaseActionResult):
    """Session information query result"""
    session_info: SessionInfo
    session_data: SessionData

    def entity_id(self) -> Optional[str]:
        return str(self.session_data.id)
```

### 2. Validator Implementation

```python
from ai.backend.manager.actions.validator import ActionValidator

class SessionAccessValidator(ActionValidator):
    """Session access permission validation"""

    async def validate(
        self,
        action: BaseAction,
        meta: BaseActionTriggerMeta,
    ) -> None:
        if not isinstance(action, GetSessionInfoAction):
            return

        # Permission validation logic
        if action.owner_access_key != meta.access_key:
            user_role = await self._get_user_role(meta.access_key)
            if user_role not in {UserRole.SUPERADMIN, UserRole.ADMIN}:
                raise InsufficientPermission(
                    "You don't have permission to access this session"
                )
```

### 3. Monitor Implementation

```python
from ai.backend.manager.actions.monitors import ActionMonitor

class AuditLogMonitor(ActionMonitor):
    """Audit log recording"""

    async def prepare(
        self,
        action: BaseAction,
        meta: BaseActionTriggerMeta,
    ) -> None:
        # Record Action start
        await self._log_action_start(
            entity_type=action.entity_type(),
            operation=action.operation_type(),
            user=meta.access_key,
            spec=action.spec(),
        )

    async def done(
        self,
        action: BaseAction,
        result: ProcessResult,
    ) -> None:
        # Record Action completion
        await self._log_action_complete(
            entity_type=action.entity_type(),
            operation=action.operation_type(),
            result_entity_id=result.result.entity_id(),
            success=True,
        )
```

### 4. Using ActionProcessor

```python
from ai.backend.manager.actions.processor import ActionProcessor

# Configure Validators and Runner
validators = [
    RBACValidator(),
    AuthValidator(),
    SessionAccessValidator(),
]

runner = ActionRunner(service)

# Create ActionProcessor
processor = ActionProcessor(
    validators=validators,
    runner=runner,
)

# Execute Action
action = GetSessionInfoAction(
    session_name="my-session",
    owner_access_key=access_key,
)

meta = BaseActionTriggerMeta(
    access_key=access_key,
    domain_name=domain_name,
)

result = await processor._run(action, meta)
```

## Authorization Patterns

### RBAC (Role-Based Access Control)

```python
from ai.backend.manager.actions.validators.rbac import RBACValidator

class RBACValidator(ActionValidator):
    """RBAC-based authorization"""

    async def validate(
        self,
        action: BaseAction,
        meta: BaseActionTriggerMeta,
    ) -> None:
        # Query user role
        user_role = await self._get_user_role(meta.access_key)

        # Check required permission
        required_permission = self._get_required_permission(action)

        # Verify permission
        if not self._has_permission(user_role, required_permission):
            raise InsufficientPermission(
                f"Role {user_role} does not have permission: {required_permission}"
            )

    def _get_required_permission(self, action: BaseAction) -> str:
        """Determine required permission for Action"""
        entity_type = action.entity_type()
        operation = action.operation_type()
        return f"{entity_type}:{operation}"

    def _has_permission(self, role: UserRole, permission: str) -> bool:
        """Check if role has permission"""
        # Query permission matrix
        ...
```

### Resource Ownership Validation

```python
class ResourceOwnershipValidator(ActionValidator):
    """Resource ownership validation"""

    async def validate(
        self,
        action: BaseAction,
        meta: BaseActionTriggerMeta,
    ) -> None:
        entity_id = action.entity_id()
        if not entity_id:
            return  # No validation needed for new resource creation

        # Check resource owner
        owner = await self._get_resource_owner(
            entity_type=action.entity_type(),
            entity_id=entity_id,
        )

        # Verify ownership
        if owner != meta.access_key:
            # Exception for administrators
            user_role = await self._get_user_role(meta.access_key)
            if user_role not in {UserRole.SUPERADMIN, UserRole.ADMIN}:
                raise InsufficientPermission(
                    f"You don't own this {action.entity_type()}"
                )
```

## Monitoring Patterns

### Audit Log

```python
class AuditLogMonitor(ActionMonitor):
    """Audit log recording"""

    async def prepare(
        self,
        action: BaseAction,
        meta: BaseActionTriggerMeta,
    ) -> None:
        await self._create_audit_log_entry(
            entity_type=action.entity_type(),
            entity_id=action.entity_id(),
            operation=action.operation_type(),
            user_id=meta.user_id,
            access_key=meta.access_key,
            domain_name=meta.domain_name,
            status="started",
            spec=action.spec(),
        )

    async def done(
        self,
        action: BaseAction,
        result: ProcessResult,
    ) -> None:
        await self._update_audit_log_entry(
            entity_type=action.entity_type(),
            entity_id=result.result.entity_id(),
            operation=action.operation_type(),
            status="completed",
            result_summary=self._summarize_result(result.result),
        )
```

### Prometheus Metrics

Collects metrics related to Action execution.

**Collected Metrics:**

1. **backend_action_total** (Counter)
   - Total number of Action executions
   - Labels: `entity_type`, `operation`, `status`

2. **backend_action_duration_seconds** (Histogram)
   - Action execution time
   - Labels: `entity_type`, `operation`

3. **backend_action_errors_total** (Counter)
   - Number of Action execution errors
   - Labels: `entity_type`, `operation`, `error_type`

## Error Handling

### Exception Handling in Action Processor

```python
class ActionProcessor:
    async def _run(
        self,
        action: BaseAction,
        meta: BaseActionTriggerMeta,
    ) -> ProcessResult:
        try:
            # Validation
            for validator in self._validators:
                await validator.validate(action, meta)

            # Execution
            result = await self._runner.run(action, meta)

            return ProcessResult(action=action, result=result)

        except InsufficientPermission as e:
            # Insufficient permission - 403
            log.warning(
                "Permission denied",
                entity_type=action.entity_type(),
                operation=action.operation_type(),
                user=meta.access_key,
            )
            raise

        except ValidationError as e:
            # Validation failed - 400
            log.warning(
                "Validation failed",
                entity_type=action.entity_type(),
                operation=action.operation_type(),
                error=str(e),
            )
            raise

        except Exception as e:
            # Unexpected error
            log.error(
                "Action execution failed",
                entity_type=action.entity_type(),
                operation=action.operation_type(),
                exc_info=e,
            )
            raise
```

## Action Types

### Single Entity Action

Operation on a single entity.

```python
@dataclass
class DestroySessionAction(BaseAction):
    """Terminate single session"""
    session_name: str
    owner_access_key: AccessKey

    def entity_id(self) -> Optional[str]:
        return self.session_name

    @classmethod
    def entity_type(cls) -> str:
        return "session"

    @classmethod
    def operation_type(cls) -> str:
        return "destroy"
```

### Batch Action

Batch operation on multiple entities.

```python
@dataclass
class DestroySessionsBatchAction(BaseBatchAction):
    """Batch termination of multiple sessions"""
    session_ids: list[str]
    owner_access_key: AccessKey

    def entity_ids(self) -> list[str]:
        return self.session_ids

    @classmethod
    def entity_type(cls) -> str:
        return "session"

    @classmethod
    def operation_type(cls) -> str:
        return "destroy_batch"
```

### Scope Action

Operation on a specific scope.

```python
@dataclass
class ListSessionsAction(BaseScopeAction):
    """Query session list"""
    owner_access_key: AccessKey
    filters: SessionFilters

    @classmethod
    def entity_type(cls) -> str:
        return "session"

    @classmethod
    def operation_type(cls) -> str:
        return "list"
```

## Best Practices

### 1. Separate into Small Validators

```python
# Good example - Single responsibility
class RBACValidator(ActionValidator):
    """Validate RBAC permissions only"""
    ...

class ResourceOwnershipValidator(ActionValidator):
    """Validate resource ownership only"""
    ...

class QuotaValidator(ActionValidator):
    """Validate quota only"""
    ...

# Bad example - Mixed responsibilities
class MegaValidator(ActionValidator):
    """Validates everything - Unclear responsibility"""
    async def validate(self, action, meta):
        # RBAC validation
        # Ownership validation
        # Quota validation
        # State validation
        ...
```

### 2. Clear Exception Messages

```python
# Good example
raise InsufficientPermission(
    f"User {user_id} does not have permission to {operation} on {entity_type}"
)

# Bad example
raise InsufficientPermission("Permission denied")
```

### 3. Monitors Should Not Fail

```python
class AuditLogMonitor(ActionMonitor):
    async def done(self, action, result):
        try:
            await self._write_audit_log(action, result)
        except Exception as e:
            # Monitor failure should not cause Action failure
            log.error("Failed to write audit log", exc_info=e)
```

## References

### Related Documentation
- [Services Layer](../services/README.md)
- [API Layer](../api/README.md)
