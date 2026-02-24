# Implementation Plan: BA-4565

## SDK v2 Client Analysis

### StreamingClient (`src/ai/backend/client/v2/domains/streaming.py`)

| Method | HTTP | Endpoint | Params style | Notes |
|--------|------|----------|-------------|-------|
| `connect_terminal(session_name)` | WS GET | `/stream/session/{session_name}/pty` | path param | Returns `WebSocketSession` context manager |
| `connect_execute(session_name)` | WS GET | `/stream/session/{session_name}/execute` | path param | Returns `WebSocketSession` context manager |
| `connect_http_proxy(session_name, params)` | WS GET | `/stream/session/{session_name}/httpproxy` | path param + query (StreamProxyParams) | `params` serialized via `model_dump(exclude_none=True)` |
| `connect_tcp_proxy(session_name, params)` | WS GET | `/stream/session/{session_name}/tcpproxy` | path param + query (StreamProxyParams) | Same as http_proxy |
| `subscribe_session_events(...)` | SSE GET | `/events/session` | query params | 5 optional kwargs: session_name, owner_access_key, session_id, group_name, scope |
| `subscribe_background_task_events(task_id)` | SSE GET | `/events/background-task` | query params | `taskId` as query param |
| `get_stream_apps(session_name)` | GET | `/stream/session/{session_name}/apps` | path param | Only REST endpoint; returns `GetStreamAppsResponse` |

### EventStreamClient (`src/ai/backend/client/v2/domains/event_stream.py`)

| Method | HTTP | Endpoint | Params style | Notes |
|--------|------|----------|-------------|-------|
| `subscribe_session_events(...)` | SSE GET | `/events/session` | query params | Duplicate of StreamingClient method |
| `subscribe_background_task_events(task_id)` | SSE GET | `/events/background-task` | query params | Duplicate of StreamingClient method |

### Registry Access

- `admin_registry.streaming` → `StreamingClient`
- `admin_registry.event_stream` → `EventStreamClient`

## Server Handler Status

### Stream Subapp (`src/ai/backend/manager/api/stream.py`)

- Handler module: **EXISTS** as `stream.py` (single file, not a package)
- Prefix: `"stream"`, API versions: (2, 3, 4)
- Registered in `global_subapp_pkgs`: **YES** (`.stream`)
- Has `stream_app_ctx` cleanup context (ZMQ, persistent task groups, event subscriptions)
- Has `stream_shutdown` handler

| Handler | Route | Decorators | Dependencies |
|---------|-------|------------|-------------|
| `stream_pty()` | `GET /session/{session_name}/pty` | `@server_status_required`, `@auth_required`, `@adefer` | ZMQ sockets to agent, registry |
| `stream_execute()` | `GET /session/{session_name}/execute` | `@server_status_required`, `@auth_required`, `@adefer` | Agent RPC, ZMQ, registry |
| `stream_proxy()` | `GET /session/{session_name}/httpproxy` | `@server_status_required`, `@auth_required`, `@check_api_params`, `@adefer` | Agent connection, Valkey conn tracking |
| `stream_proxy()` | `GET /session/{session_name}/tcpproxy` | Same as httpproxy | Same as httpproxy |
| `get_stream_apps()` | `GET /session/{session_name}/apps` | `@server_status_required`, `@auth_required` | DB read only (SessionRow + service_ports) |

### Events Subapp (`src/ai/backend/manager/api/events.py`)

- Handler module: **EXISTS** as `events.py` (single file)
- Prefix: `"events"`, API versions: (3, 4)
- Registered in `global_subapp_pkgs`: **YES** (`.events`)
- Has `events_app_ctx` cleanup context (event dispatcher subscriptions)

| Handler | Route | Dependencies |
|---------|-------|-------------|
| `push_session_events()` | `GET /session` | Event hub, event propagator, SSE response |
| `push_background_task_events()` | `GET /background-task` | Event hub, event propagator, SSE response |

### Action Required: **test-only**

All server handlers exist and are registered. No handler implementation needed.

## Testability Analysis

### Testable in Component Tests (HTTP REST)

| Method | Reason |
|--------|--------|
| `get_stream_apps()` | Pure DB read: SessionRow lookup + service_ports field. No agent/ZMQ/event infrastructure. |

### NOT Testable in Component Tests

| Method | Reason |
|--------|--------|
| `connect_terminal()` | Requires ZMQ PUB/SUB sockets to live agent for PTY stdin/stdout |
| `connect_execute()` | Requires agent RPC for code execution + ZMQ relay |
| `connect_http_proxy()` | Requires agent TCP connection for HTTP proxy relay + Valkey conn tracking |
| `connect_tcp_proxy()` | Same as http_proxy |
| `subscribe_session_events()` | Requires event hub + event propagator + long-lived SSE response |
| `subscribe_background_task_events()` | Requires event hub + WithCachePropagator + long-lived SSE response |

Per BA-4552 guide: **"스트리밍 (WebSocket/SSE): 컴포넌트 테스트에서 직접 테스트 불가"**

## Test Scenarios

### Component Tests (`tests/component/streaming/`)

| Test Class | Test Method | Scenario | xfail? |
|------------|-------------|----------|--------|
| `TestGetStreamApps` | `test_admin_gets_stream_apps` | Admin retrieves apps for a RUNNING session with service_ports | - |
| `TestGetStreamApps` | `test_empty_stream_apps` | Session has no service_ports → returns empty list | - |
| `TestGetStreamApps` | `test_session_not_found` | Nonexistent session name → SessionNotFound error | - |

### Integration Tests (`tests/integration/streaming/`)

Integration tests for streaming endpoints require live agents (for WebSocket) or event infrastructure (for SSE), which are only available in full integration environments. Since this series focuses on SDK v2 client-driven tests using the component test framework, integration tests are deferred.

| Test Class | Scenario | Status |
|------------|----------|--------|
| `TestStreamPty` | WS connect → send stdin → receive stdout | Deferred (requires live agent) |
| `TestStreamExecute` | WS connect → send code → receive result | Deferred (requires live agent) |
| `TestStreamProxy` | WS connect to HTTP proxy → relay | Deferred (requires live agent) |
| `TestSessionEvents` | SSE subscribe → receive session lifecycle events | Deferred (requires event infrastructure) |
| `TestBackgroundTaskEvents` | SSE subscribe → receive bgtask events | Deferred (requires event infrastructure) |

## Deferred Items

| Item | Reason |
|------|--------|
| `connect_terminal()` component/integration test | Requires ZMQ sockets to live agent for PTY I/O |
| `connect_execute()` component/integration test | Requires agent RPC for kernel code execution |
| `connect_http_proxy()` component/integration test | Requires agent TCP connection for proxy relay |
| `connect_tcp_proxy()` component/integration test | Requires agent TCP connection for proxy relay |
| `subscribe_session_events()` component/integration test | Requires event hub + propagator for SSE delivery |
| `subscribe_background_task_events()` component/integration test | Requires event hub + WithCachePropagator |
| `EventStreamClient` tests | Duplicate of StreamingClient SSE methods; same constraints apply |
| Full integration test suite | Requires live agent + event infrastructure; out of scope for BA-4552 series |

## Implementation Steps

1. Create `tests/component/streaming/__init__.py`
2. Create `tests/component/streaming/conftest.py`
   - `server_subapp_pkgs()` → `[".auth", ".stream"]`
   - `server_cleanup_contexts()` → standard contexts + `_streaming_domain_ctx`
   - `_streaming_domain_ctx()` → Repositories + Processors + mock registry
   - `session_seed()` fixture with `service_ports` in kernel row
   - `session_seed_no_ports()` fixture (kernel with `service_ports=None`)
3. Create `tests/component/streaming/test_streaming.py`
   - `TestGetStreamApps` with 3 test methods
4. Create `tests/component/streaming/BUILD`
5. Create `tests/integration/streaming/__init__.py` (empty placeholder)
6. Create `tests/integration/streaming/BUILD` (placeholder)
7. `pants fmt :: && pants fix :: && pants lint --changed-since=HEAD~1`
8. PR + changelog
