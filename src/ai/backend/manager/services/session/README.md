# Session Service

The Session Service is the core component of Backend.AI's compute session management system, responsible for managing the complete lifecycle of compute sessions from creation to destruction, including code execution, file operations, and service management.

## Service Overview

The Session Service provides comprehensive session management capabilities including creation, execution, monitoring, modification, and cleanup of compute sessions. It supports both interactive and batch workloads with proper resource management, permission checking, and integration with the agent infrastructure.

### Key Components

- **SessionService**: Main service class that orchestrates all session operations
- **SessionProcessors**: Handles action processing and monitoring with 25+ specialized processors
- **SessionRepository & AdminSessionRepository**: Data access layer with repository pattern
- **Action Classes**: Structured actions for each session operation type
- **Base Classes**: Common abstractions for session and batch actions

## Key Features and Capabilities

### 1. Session Creation and Management
- **Parameter-based Creation**: Create sessions with detailed resource specifications
- **Template-based Creation**: Create sessions from predefined templates
- **Cluster Creation**: Multi-node session creation with scaling support
- **Session Modification**: Update session attributes and configurations
- **Session Renaming**: Change session names with validation
- **Session Restart**: Restart failed or completed sessions

### 2. Session Execution and Control
- **Code Execution**: Execute code snippets and commands within sessions
- **Session Completion**: Handle session completion and cleanup
- **Session Interruption**: Interrupt running sessions safely
- **Status Monitoring**: Real-time session status tracking and transitions
- **Session Destruction**: Clean session termination with resource cleanup

### 3. File Operations
- **File Upload**: Upload files to session containers
- **File Download**: Download single files from sessions
- **Bulk Download**: Download multiple files as archives
- **File Listing**: Browse session filesystem with detailed information
- **File Management**: Complete file system operations within sessions

### 4. Service Management
- **Service Startup**: Start HTTP services within sessions
- **Service Shutdown**: Stop running services cleanly
- **Direct Access**: Get direct access URLs for services
- **Service Monitoring**: Track service status and health

### 5. Information and Monitoring
- **Session Information**: Retrieve detailed session metadata
- **Status History**: Get complete session status change history
- **Container Logs**: Access session container logs
- **Dependency Graphs**: Visualize session dependencies
- **Resource Usage**: Monitor resource consumption
- **Abuse Reports**: Generate usage and abuse reports

### 6. Advanced Features
- **Session Commit**: Create snapshots of session state
- **Image Conversion**: Convert sessions to custom container images
- **Commit Status**: Track image creation progress
- **Session Matching**: Find sessions by pattern matching
- **Status Transitions**: Automated status checking and transitions

## Operation Scenarios

### Session Creation Workflow
1. Validate session parameters and resources
2. Check user permissions and quotas
3. Select appropriate agent and scaling group
4. Create session record in database
5. Request session creation from agent
6. Monitor session startup and initialization
7. Return session data or error information

### Session Execution Workflow
1. Validate session state and permissions
2. Prepare execution environment
3. Submit code/command to session
4. Monitor execution progress
5. Handle execution results and outputs
6. Update session statistics
7. Return execution results

### File Operations Workflow
1. Validate session access permissions
2. Check file system quotas and limits
3. Perform file operations via agent
4. Update session file system metadata
5. Handle file transfer and streaming
6. Return operation results

### Service Management Workflow
1. Validate service configuration
2. Check port availability and permissions
3. Start/stop services via agent
4. Configure proxy routing
5. Monitor service health
6. Return service access information

## API Usage Examples

### Creating a Session
```python
from ai.backend.manager.services.session.actions.create_from_params import CreateFromParamsAction
from ai.backend.common.types import ResourceSlot, AccessKey

action = CreateFromParamsAction(
    name="my-python-session",
    access_key=AccessKey("user-access-key"),
    image="python:3.9",
    architecture="x86_64",
    resource_slots=ResourceSlot(cpu=2, mem=4096),
    session_type=SessionTypes.INTERACTIVE,
    cluster_mode=ClusterMode.SINGLE_NODE,
    cluster_size=1,
    timeout=3600,
    bootstrap_script="pip install -r requirements.txt",
    tag="development"
)

result = await processors.create_from_params.wait_for_complete(action)
if result.success:
    print(f"Session created: {result.session_data.name}")
```

### Executing Code in a Session
```python
from ai.backend.manager.services.session.actions.execute_session import ExecuteSessionAction

action = ExecuteSessionAction(
    session_name="my-python-session",
    access_key=AccessKey("user-access-key"),
    code="print('Hello, Backend.AI!')",
    mode="query",
    opts={}
)

result = await processors.execute_session.wait_for_complete(action)
print(f"Execution result: {result.result}")
```

### Uploading Files to a Session
```python
from ai.backend.manager.services.session.actions.upload_files import UploadFilesAction

action = UploadFilesAction(
    session_name="my-python-session",
    access_key=AccessKey("user-access-key"),
    files=[
        FileUploadSpec(
            filename="script.py",
            content=b"print('Hello from file!')",
            path="/home/work/"
        )
    ]
)

result = await processors.upload_files.wait_for_complete(action)
```

### Starting a Service
```python
from ai.backend.manager.services.session.actions.start_service import StartServiceAction

action = StartServiceAction(
    session_name="my-python-session",
    access_key=AccessKey("user-access-key"),
    service="jupyter",
    port=8888,
    arguments=["--no-browser", "--ip=0.0.0.0"],
    login_session_token="user-token"
)

result = await processors.start_service.wait_for_complete(action)
print(f"Service URL: {result.wsproxy_addr}")
```

### Getting Session Information
```python
from ai.backend.manager.services.session.actions.get_session_info import GetSessionInfoAction

action = GetSessionInfoAction(
    session_name="my-python-session",
    owner_access_key=AccessKey("user-access-key")
)

result = await processors.get_session_info.wait_for_complete(action)
print(f"Session status: {result.session_info.status}")
print(f"Resource usage: {result.session_info.occupied_slots}")
```

### Monitoring Session Status
```python
from ai.backend.manager.services.session.actions.get_status_history import GetStatusHistoryAction

action = GetStatusHistoryAction(
    session_name="my-python-session",
    owner_access_key=AccessKey("user-access-key")
)

result = await processors.get_status_history.wait_for_complete(action)
for entry in result.status_history["history"]:
    print(f"Status: {entry['status']} at {entry['timestamp']}")
```

## Integration Points

### Agent Registry Integration
- **Session Creation**: Request session creation from appropriate agents
- **Code Execution**: Submit execution requests to session containers
- **File Operations**: Handle file uploads/downloads via agent protocol
- **Service Management**: Start/stop services through agent communication
- **Resource Monitoring**: Collect resource usage statistics from agents

### Database Integration
- **SessionRepository**: Standard session operations with validation
- **AdminSessionRepository**: Administrative operations with elevated permissions
- **Database Schema**: PostgreSQL with SQLAlchemy ORM for session metadata
- **Transaction Management**: Atomic operations with rollback support

### Background Task Manager
- **Long-running Operations**: Image conversion and commit operations
- **Async Processing**: Non-blocking execution of heavy operations
- **Progress Tracking**: Monitor background task progress
- **Error Handling**: Proper error propagation and cleanup

### Event Hub Integration
- **Status Changes**: Broadcast session status transitions
- **Resource Events**: Notify about resource allocation/deallocation
- **Lifecycle Events**: Session creation, completion, and destruction events
- **Service Events**: Service startup and shutdown notifications

### Storage Integration
- **VFolder Management**: Virtual folder mounting and access control
- **Container Registry**: Custom image storage and retrieval
- **File System Operations**: Session-level file system management
- **Backup and Restore**: Session state preservation

### WebSocket Proxy Integration
- **Service Routing**: Dynamic service proxy configuration
- **Authentication**: Token-based service access control
- **Load Balancing**: Service request distribution
- **Connection Management**: WebSocket connection handling

## Testing Guidelines

### Unit Testing
- Use `ScenarioBase` class for parameterized testing
- Test both success and failure scenarios
- Verify database state changes
- Mock agent communication and external dependencies
- Test action validation and error handling

### Integration Testing
- Test complete workflows end-to-end
- Verify agent communication protocols
- Test session lifecycle management
- Validate resource allocation and cleanup
- Test concurrent session operations

### Performance Testing
- Test with large numbers of concurrent sessions
- Verify resource usage monitoring accuracy
- Test file operation performance
- Monitor memory and CPU usage
- Test scaling behavior under load

### Error Handling Testing
- Test network failures and timeouts
- Verify proper error messages and codes
- Test agent communication failures
- Validate cleanup operations on errors
- Test resource exhaustion scenarios

## Common Error Scenarios

### Session Creation Errors
- **Resource Unavailable**: Insufficient compute resources or quota exceeded
- **Image Not Found**: Requested container image doesn't exist
- **Permission Denied**: User lacks session creation permissions
- **Invalid Configuration**: Malformed session parameters or resource specifications
- **Agent Unavailable**: No suitable agents available for session creation

### Session Execution Errors
- **Session Not Found**: Target session doesn't exist or is terminated
- **Session Not Ready**: Session is still initializing or in invalid state
- **Execution Timeout**: Code execution exceeds time limits
- **Resource Exhaustion**: Session runs out of memory or disk space
- **Permission Denied**: User lacks execution permissions

### File Operation Errors
- **File Not Found**: Target file doesn't exist in session
- **Permission Denied**: Insufficient file system permissions
- **Quota Exceeded**: File operation exceeds storage quota
- **Transfer Failed**: Network issues during file transfer
- **Invalid Path**: Malformed file paths or restricted directories

### Service Management Errors
- **Port Conflict**: Requested port already in use
- **Service Failed**: Service startup or configuration failure
- **Permission Denied**: User lacks service management permissions
- **Invalid Configuration**: Malformed service parameters
- **Network Issues**: Service routing or proxy configuration problems

## Available Actions

### Session Lifecycle Actions
- **create_from_params**: Create session with detailed parameters
- **create_from_template**: Create session from predefined template
- **create_cluster**: Create multi-node session cluster
- **modify_session**: Update session configuration
- **rename_session**: Change session name
- **restart_session**: Restart terminated session
- **destroy_session**: Terminate and cleanup session

### Execution Actions
- **execute_session**: Execute code in session
- **complete**: Handle session completion
- **interrupt**: Interrupt running session

### File Operations
- **upload_files**: Upload files to session
- **download_file**: Download single file
- **download_files**: Download multiple files
- **list_files**: List session files

### Information Actions
- **get_session_info**: Get session metadata
- **get_status_history**: Get status change history
- **get_container_logs**: Access container logs
- **get_dependency_graph**: Get dependency visualization
- **get_abusing_report**: Generate usage reports
- **match_sessions**: Find sessions by pattern

### Service Management
- **start_service**: Start HTTP service
- **shutdown_service**: Stop running service
- **get_direct_access_info**: Get service access URLs

### Advanced Operations
- **commit_session**: Create session snapshot
- **convert_session_to_image**: Convert to container image
- **get_commit_status**: Track image creation progress
- **check_and_transit_status**: Update session status

## Best Practices

1. **Resource Management**: Always specify appropriate resource limits and quotas
2. **Error Handling**: Implement comprehensive error handling for all operations
3. **Permission Validation**: Check user permissions before session operations
4. **Status Monitoring**: Monitor session status before performing operations
5. **Cleanup Operations**: Ensure proper cleanup of failed or interrupted sessions
6. **Concurrent Access**: Handle concurrent operations on the same session safely
7. **Resource Efficiency**: Use appropriate session sizes and cleanup unused sessions
8. **Security**: Validate all user inputs and maintain session isolation

## Security Considerations

- **Access Control**: Strict session access control based on ownership and permissions
- **Input Validation**: All user inputs are validated before processing
- **Code Execution**: Sandboxed execution environment with resource limits
- **File System Isolation**: Session-level file system isolation
- **Network Security**: Controlled network access and service exposure
- **Audit Logging**: Comprehensive logging of all session operations
- **Resource Limits**: Enforcement of resource quotas and limits
- **Data Protection**: Secure handling of session data and user files

## Architecture Considerations

### Scalability
- **Agent Distribution**: Session load balancing across multiple agents
- **Resource Pooling**: Efficient resource allocation and sharing
- **Background Processing**: Non-blocking operations for better responsiveness
- **Caching**: Session metadata caching for improved performance

### Reliability
- **Error Recovery**: Automatic recovery from transient failures
- **Timeout Management**: Proper timeout handling for all operations
- **State Consistency**: Consistent session state across distributed components
- **Monitoring**: Comprehensive monitoring and alerting

### Maintainability
- **Action Pattern**: Clear separation of concerns using action-based architecture
- **Repository Pattern**: Clean data access layer abstraction
- **Type Safety**: Strong typing for all interfaces and data structures
- **Documentation**: Comprehensive code documentation and examples
