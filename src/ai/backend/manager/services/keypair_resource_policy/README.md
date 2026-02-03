# KeyPair Resource Policy Service

## Service Overview
The KeyPair Resource Policy service manages resource policies applied to API access keys ("KeyPair") in Backend.AI. Each policy controls compute resource usage, session limits, and storage allocation.

## Key Features
1. **Create KeyPair Resource Policy** – Create a new KeyPair resource policy  
   - Action: `CreateKeyPairResourcePolicyAction`  
   - Result: `CreateKeyPairResourcePolicyActionResult`  
2. **Modify KeyPair Resource Policy** – Modify an existing policy  
   - Action: `ModifyKeyPairResourcePolicyAction`  
   - Result: `ModifyKeyPairResourcePolicyActionResult`  
3. **Delete KeyPair Resource Policy** – Delete a policy  
   - Action: `DeleteKeyPairResourcePolicyAction`  
   - Result: `DeleteKeyPairResourcePolicyActionResult`  

## Operation Scenarios

### Creating a KeyPair Resource Policy

```python
from ai.backend.manager.repositories.keypair_resource_policy.creators import KeyPairResourcePolicyCreatorSpec
from ai.backend.manager.services.keypair_resource_policy.actions.create_keypair_resource_policy import CreateKeyPairResourcePolicyAction

# Create a new keypair resource policy
creator = KeyPairResourcePolicyCreatorSpec(
    name="example-policy",
    max_concurrent_sessions=5,
    max_containers_per_session=2,
    total_resource_slots={"cpu": 8, "mem": "16g"},
    idle_timeout=3600,
    max_session_lifetime=86400,
    max_concurrent_sftp_sessions=3,
    allowed_vfolder_hosts={"local": None}
)

action = CreateKeyPairResourcePolicyAction(creator=creator)
result = await service.create_keypair_resource_policy(action)
```

### Modifying a KeyPair Resource Policy

```python
from ai.backend.manager.services.keypair_resource_policy.actions.modify_keypair_resource_policy import ModifyKeyPairResourcePolicyAction

# Modify an existing policy
action = ModifyKeyPairResourcePolicyAction(
    name="example-policy",
    modifier=modifier_instance  # Contains fields to update
)
result = await service.modify_keypair_resource_policy(action)
```

### Deleting a KeyPair Resource Policy

```python
from ai.backend.manager.services.keypair_resource_policy.actions.delete_keypair_resource_policy import DeleteKeyPairResourcePolicyAction

# Delete a policy
action = DeleteKeyPairResourcePolicyAction(name="example-policy")
result = await service.delete_keypair_resource_policy(action)
```

## Integration Points

### Repository Layer

The service integrates with `KeypairResourcePolicyRepository` (src/ai/backend/manager/repositories/keypair_resource_policy/repository.py:16) which provides:

- **create(fields)** - Create new policy from field mapping
- **get_by_name(name)** - Retrieve policy by name
- **update(name, fields)** - Update existing policy fields  
- **delete(name)** - Delete policy by name

The repository uses SQLAlchemy for database operations with proper transaction handling and error management.

### Database Models

Uses `KeyPairResourcePolicyRow` model (src/ai/backend/manager/models/resource_policy.py) with the following key fields:

- **name** - Unique policy identifier
- **max_concurrent_sessions** - Maximum simultaneous sessions
- **max_containers_per_session** - Container limit per session
- **total_resource_slots** - Available compute resources (CPU, memory, GPU)
- **idle_timeout** - Session idle timeout in seconds
- **max_session_lifetime** - Maximum session duration
- **max_concurrent_sftp_sessions** - SFTP session limit
- **allowed_vfolder_hosts** - Permitted virtual folder hosts
- **max_pending_session_count** - Queued session limit
- **max_pending_session_resource_slots** - Resource allocation for pending sessions

### Action System

Built on Backend.AI's action framework with three main operations:

1. **CreateKeyPairResourcePolicyAction** (src/ai/backend/manager/services/keypair_resource_policy/actions/create_keypair_resource_policy.py:13)
   - Uses `KeyPairResourcePolicyCreatorSpec` for input validation
   - Returns `CreateKeyPairResourcePolicyActionResult` with created policy

2. **ModifyKeyPairResourcePolicyAction** (src/ai/backend/manager/services/keypair_resource_policy/actions/modify_keypair_resource_policy.py)
   - Accepts policy name and modifier object
   - Returns `ModifyKeyPairResourcePolicyActionResult` with updated policy

3. **DeleteKeyPairResourcePolicyAction** (src/ai/backend/manager/services/keypair_resource_policy/actions/delete_keypair_resource_policy.py)
   - Requires only policy name for deletion
   - Returns `DeleteKeyPairResourcePolicyActionResult` with deleted policy data

All actions inherit from `KeypairResourcePolicyAction` base class and follow the standard action pattern with entity_id() and operation_type() methods.

