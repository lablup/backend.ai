# VFolder Service

## Service Overview

The VFolder service is a core component of Backend.AI that manages virtual folders (storage volumes). It provides comprehensive functionality for file storage creation, file operations, sharing, and permission management. The service is designed with a modular architecture that separates concerns into distinct sub-services.

## Key Features and Capabilities

### 1. VFolder Management
- **Create**: Create new virtual folders with customizable quota, permissions, and usage modes
- **Update**: Modify VFolder attributes including name, permissions, and cloneable status
- **Delete**: Safe deletion with trash/restore functionality and force delete options
- **Clone**: Duplicate VFolders for backup or experimentation purposes
- **List & Get**: Retrieve VFolder information and usage statistics

### 2. File Operations
- **Upload/Download**: Secure file transfer with multipart support for large files
- **List Files**: Browse directory contents with filtering and sorting capabilities
- **File Management**: Rename, delete files and create directories
- **Permissions**: Fine-grained access control (read-only, read-write, read-write-delete)

### 3. Sharing and Collaboration
- **Invite**: Share VFolders with other users with specific permissions
- **Accept/Reject**: Manage incoming VFolder invitations
- **Update Permissions**: Modify sharing permissions for existing collaborators
- **Leave Shared Folders**: Allow users to remove themselves from shared VFolders

## Operation Scenarios

### Personal Workspace Creation
```python
# Create a personal VFolder for individual work
action = CreateVFolderAction(
    name="my-workspace",
    folder_host="storage1",
    mount_permission=VFolderPermission.READ_WRITE,
    usage_mode=VFolderUsageMode.GENERAL,
    user_uuid=user_id,
    quota=10737418240  # 10GB
)
```

### Team Collaboration
```python
# Create a project VFolder and invite team members
create_action = CreateVFolderAction(
    name="team-project",
    group_id_or_name=project_id,
    usage_mode=VFolderUsageMode.DATA,
    cloneable=True
)

invite_action = InviteVFolderAction(
    vfolder_uuid=vfolder_id,
    invitee_user_uuids=[member1_id, member2_id],
    mount_permission=VFolderPermission.READ_WRITE
)
```

### Model Deployment Storage
```python
# Create read-only model storage for serving
action = CreateVFolderAction(
    name="ml-models",
    usage_mode=VFolderUsageMode.MODEL,
    mount_permission=VFolderPermission.READ_ONLY
)
```

## API Usage Examples

### File Upload Workflow
```python
# 1. Create upload session
upload_action = CreateUploadSessionAction(
    vfolder_uuid=vfolder_id,
    path="/data/dataset.csv",
    size="104857600"  # 100MB
)
result = await file_service.create_upload_session(upload_action)

# 2. Use the returned token and URL for actual file upload
# Client uploads file chunks to result.url using result.token
```

### VFolder Cloning
```python
# Clone a VFolder for experimentation
clone_action = CloneVFolderAction(
    source_vfolder_uuid=original_id,
    target_name="experiment-copy",
    target_host="storage1"
)
result = await vfolder_service.clone(clone_action)
# Monitor progress using result.bgtask_id
```

### Permission Management
```python
# Update VFolder to make it cloneable
modifier = VFolderAttributeModifier(
    cloneable=OptionalState.set(True),
    mount_permission=OptionalState.set(VFolderPermission.READ_WRITE)
)
update_action = UpdateVFolderAttributeAction(
    vfolder_uuid=vfolder_id,
    modifier=modifier
)
```

## Integration Points

### 1. Storage Backend Integration
- **StorageSessionManager**: Handles actual file operations and quota management
- **Multiple Storage Hosts**: Support for distributed storage infrastructure
- **Unmanaged Paths**: Mount external storage locations (admin only)

### 2. Permission System
- **User-based**: Personal VFolders owned by individual users
- **Group-based**: Project VFolders shared within groups
- **Invitation System**: Fine-grained sharing with external users

### 3. Background Task System
- **Clone Operations**: Asynchronous copying of large VFolders
- **Deletion Tasks**: Background cleanup of deleted VFolders
- **Task Monitoring**: Track progress of long-running operations

### 4. Quota Management
- **Resource Policies**: Enforce user/group storage limits
- **Usage Tracking**: Real-time monitoring of storage consumption
- **Quota Scopes**: Flexible quota assignment per VFolder

## Testing Guidelines

### Unit Testing
Tests are organized by sub-service:
- `test_vfolder.py`: Core VFolder management operations
- `test_file.py`: File operation functionality
- `test_invite.py`: Sharing and invitation features

### Test Scenarios
Each test file uses parametrized test scenarios that cover:
- Success cases with various configurations
- Permission validation
- Error handling and edge cases
- Quota enforcement

### Running Tests
```bash
# Run all VFolder service tests
pants test tests/services/vfolder::

# Run specific sub-service tests
pants test tests/services/vfolder/test_file.py
```

### Mock Requirements
Tests use mocked dependencies:
- `StorageSessionManager`: File operations
- `VFolderRepository`: Data access
- `QuotaRepository`: Quota validation
- `ActionMonitor`: Event tracking

## Security Considerations

1. **Permission Validation**: All operations must validate user permissions
2. **Host Access Control**: Restrict storage host access based on resource policies
3. **Quota Enforcement**: Prevent storage abuse through strict quota limits
4. **Audit Trail**: Log all VFolder operations for security monitoring

## Future Enhancements

1. **Versioning**: File version history and rollback capabilities
2. **Encryption**: At-rest encryption for sensitive data
3. **Replication**: Cross-region VFolder replication for disaster recovery
4. **Advanced Sharing**: Time-limited shares and access tokens
5. **Storage Tiering**: Automatic migration between hot/cold storage