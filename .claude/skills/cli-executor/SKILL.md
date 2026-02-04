---
name: cli-executor
description: Execute Backend.AI component CLI commands (mgr start-server, ag start-server, storage start-server) with pre-flight checks (DB, Redis, etcd), health checks, and troubleshooting
invoke_method: automatic
auto_execute: false
enabled: true
---

## Purpose

Guide execution of Backend.AI component CLI commands with pre-flight checks, command suggestions, and troubleshooting.

**When to use:**
- Running component-specific commands
- Starting development services
- Checking component health
- Executing administrative tasks
- Troubleshooting component issues

**Benefits:**
- Pre-flight infrastructure checks
- Component-specific command suggestions
- Automatic error diagnosis
- Actionable troubleshooting steps

## Parameters

- **component** (required): Target component
  - `mgr` - Manager
  - `ag` - Agent
  - `storage` - Storage Proxy
  - `web` - Web Server
  - `app-proxy-coordinator` - App Proxy Coordinator
  - `app-proxy-worker` - App Proxy Worker

- **subcommand** (optional): Specific command to run
  - If omitted, shows available commands for component

## Supported Components

### Manager (mgr)

**Description:** Core orchestration and API server

**Common Commands:**
- `health` - Check manager health status
- `start-server` - Start manager server (blocking)
- `dbschema show` - Show current database schema version
- `dbschema migrate` - Apply database migrations

**Pre-flight Checks:**
- ✅ PostgreSQL database running
- ✅ Redis running
- ✅ etcd running
- ✅ Database migrations up-to-date (`/db-status`)
- ✅ Configuration file exists

**Usage:**
```bash
./backend.ai mgr <subcommand>
```

**Examples:**
```bash
# Check health
./backend.ai mgr health

# Start manager server (blocks terminal)
./backend.ai mgr start-server

# Show database schema version
./backend.ai mgr dbschema show
```

---

### Agent (ag)

**Description:** Compute resource manager and container orchestrator

**Common Commands:**
- `health` - Check agent health status
- `start-server` - Start agent server (blocking)
- `status` - Show agent registration and status

**Pre-flight Checks:**
- ✅ Manager accessible
- ✅ Docker daemon running
- ✅ GPU drivers installed (if GPU agent)
- ✅ Required permissions
- ✅ Configuration file exists

**Usage:**
```bash
./backend.ai ag <subcommand>
```

**Examples:**
```bash
# Check health
./backend.ai ag health

# Start agent server
./backend.ai ag start-server

# Check agent status
./backend.ai ag status
```

---

### Storage Proxy (storage)

**Description:** Storage backend abstraction layer

**Common Commands:**
- `health` - Check storage proxy health
- `start-server` - Start storage proxy (blocking)
- `volume list` - List available volumes

**Pre-flight Checks:**
- ✅ Manager accessible
- ✅ Storage backend accessible (S3, NFS, etc.)
- ✅ Configuration file exists
- ✅ Required permissions

**Usage:**
```bash
./backend.ai storage <subcommand>
```

**Examples:**
```bash
# Check health
./backend.ai storage health

# Start storage proxy
./backend.ai storage start-server

# List volumes
./backend.ai storage volume list
```

---

### Web Server (web)

**Description:** Web UI and static asset server

**Common Commands:**
- `health` - Check web server health
- `start-server` - Start web server (blocking)

**Pre-flight Checks:**
- ✅ Manager accessible
- ✅ Static assets built
- ✅ Configuration file exists

**Usage:**
```bash
./backend.ai web <subcommand>
```

**Examples:**
```bash
# Check health
./backend.ai web health

# Start web server
./backend.ai web start-server
```

---

### App Proxy Coordinator (app-proxy-coordinator)

**Description:** Application proxy coordinator for service routing

**Common Commands:**
- `health` - Check coordinator health
- `start-server` - Start coordinator server (blocking)

**Pre-flight Checks:**
- ✅ PostgreSQL database running
- ✅ Redis running
- ✅ Database migrations up-to-date (use `/db-status --component=appproxy`)
- ✅ Configuration file exists

**Usage:**
```bash
./backend.ai app-proxy-coordinator <subcommand>
```

**Examples:**
```bash
# Check health
./backend.ai app-proxy-coordinator health

# Start coordinator
./backend.ai app-proxy-coordinator start-server
```

---

### App Proxy Worker (app-proxy-worker)

**Description:** Application proxy worker for request handling

**Common Commands:**
- `health` - Check worker health
- `start-server` - Start worker server (blocking)

**Pre-flight Checks:**
- ✅ Coordinator accessible
- ✅ Redis running
- ✅ Configuration file exists

**Usage:**
```bash
./backend.ai app-proxy-worker <subcommand>
```

**Examples:**
```bash
# Check health
./backend.ai app-proxy-worker health

# Start worker
./backend.ai app-proxy-worker start-server
```

---

## Execution Flow

### 1. Component Selection

If component not specified:
```
Available Backend.AI components:

1. mgr                    - Manager (core orchestration)
2. ag                     - Agent (compute resources)
3. storage                - Storage Proxy (storage abstraction)
4. web                    - Web Server (UI)
5. app-proxy-coordinator  - App Proxy Coordinator (routing)
6. app-proxy-worker       - App Proxy Worker (request handling)

Which component would you like to run?
```

### 2. Pre-flight Checks

Before executing command, verify:
- Infrastructure dependencies (Docker, databases, etc.)
- Configuration files
- Required permissions
- Dependent services

**Example output:**
```
🔍 Pre-flight checks for Manager:

✅ PostgreSQL database running
✅ Redis running
✅ etcd running
⚠️ Database migrations pending (2 migrations)
✅ Configuration file exists

Recommendation: Apply database migrations before starting
Run: /db-migrate
```

### 3. Command Execution

**For blocking commands (start-server):**
```
📌 Running: ./backend.ai mgr start-server

Note: This command blocks the terminal.
- Press Ctrl+C to stop
- Open new terminal for other commands
- Logs will appear in this terminal

Executing...
```

**For non-blocking commands (health, status):**
```
🔄 Running: ./backend.ai mgr health

[Execute and show output]

✅ Manager is healthy

Next steps:
- Start manager: /cli-executor --component=mgr --subcommand=start-server
- Check database: /db-status
```

### 4. Error Handling

Automatic error diagnosis and troubleshooting suggestions.

### 5. Success Guidance

- Show expected output
- Suggest next steps
- Link to related skills

---

## Error Handling

### Infrastructure Errors

**Docker not running:**
```
❌ Error: Docker daemon not accessible

Details: Cannot connect to Docker socket at /var/run/docker.sock

Recommended actions:
1. Start Docker Desktop (macOS/Windows)
   Or start Docker daemon (Linux): sudo systemctl start docker

2. Verify Docker is running:
   docker ps

3. Check Docker permissions:
   sudo usermod -aG docker $USER
   # Log out and back in for group changes

4. For development environment:
   ./scripts/run-dev.sh  # Starts halfstack infrastructure

Related documentation:
- Docker installation: https://docs.docker.com/get-docker/
- Backend.AI halfstack: docs/dev/halfstack.md
```

**Database not running:**
```
❌ Error: PostgreSQL connection failed

Details: Connection refused to localhost:5432

Recommended actions:
1. Check PostgreSQL is running:
   docker ps | grep postgres

2. Start infrastructure:
   ./scripts/run-dev.sh

3. Verify database configuration:
   - Check connection settings in config
   - Ensure correct host/port/credentials

4. Check database status:
   /db-status

Related skills:
- /db-status - Check database schema status
- /db-migrate - Apply database migrations
```

**Redis not running:**
```
❌ Error: Redis connection failed

Details: Connection refused to localhost:6379

Recommended actions:
1. Check Redis is running:
   docker ps | grep redis

2. Start infrastructure:
   ./scripts/run-dev.sh

3. Verify Redis configuration in config file
```

**etcd not running (Manager only):**
```
❌ Error: etcd connection failed

Details: Cannot connect to etcd at localhost:2379

Recommended actions:
1. Check etcd is running:
   docker ps | grep etcd

2. Start infrastructure:
   ./scripts/run-dev.sh

3. Verify etcd configuration in config file
```

### Configuration Errors

**Missing configuration:**
```
❌ Error: Configuration file not found

Details: Cannot find config at ./configs/manager.toml

Recommended actions:
1. Copy sample configuration:
   cp configs/manager.sample.toml configs/manager.toml

2. Edit configuration with your settings

3. For development, sample configs are usually sufficient

Configuration locations:
- Manager: configs/manager.toml
- Agent: configs/agent.toml
- Storage: configs/storage-proxy.toml
- Web: configs/web.toml
- App Proxy: configs/app-proxy-coordinator.toml, app-proxy-worker.toml
```

**Invalid configuration:**
```
❌ Error: Configuration validation failed

Details: Invalid value for 'db.host': expected string, got null

Recommended actions:
1. Review configuration file for syntax errors
2. Check required fields are present
3. Validate against sample configuration
4. Refer to docs/config/ for configuration guide
```

### Permission Errors

**GPU access denied (Agent only):**
```
❌ Error: Cannot access GPU devices

Details: Permission denied accessing /dev/nvidia0

Recommended actions:
1. Install NVIDIA Docker runtime:
   https://github.com/NVIDIA/nvidia-docker

2. Add user to docker group:
   sudo usermod -aG docker $USER

3. Verify GPU access:
   docker run --gpus all nvidia/cuda:11.0-base nvidia-smi

4. Check NVIDIA drivers:
   nvidia-smi
```

**File permission error:**
```
❌ Error: Permission denied

Details: Cannot write to /var/log/backend.ai/manager.log

Recommended actions:
1. Check file/directory permissions:
   ls -la /var/log/backend.ai/

2. Create directory with correct permissions:
   sudo mkdir -p /var/log/backend.ai
   sudo chown $USER:$USER /var/log/backend.ai

3. Or configure alternative log location in config
```

### Dependency Errors

**Manager not accessible (Agent, Storage, Web):**
```
❌ Error: Cannot connect to Manager

Details: Connection refused to localhost:8081

Recommended actions:
1. Check Manager is running:
   /cli-executor --component=mgr --subcommand=health

2. Start Manager:
   /cli-executor --component=mgr --subcommand=start-server

3. Verify Manager configuration:
   - Check Manager endpoint in component config
   - Ensure correct host/port
```

**Coordinator not accessible (App Proxy Worker):**
```
❌ Error: Cannot connect to App Proxy Coordinator

Details: Connection refused to localhost:6010

Recommended actions:
1. Check Coordinator is running:
   /cli-executor --component=app-proxy-coordinator --subcommand=health

2. Start Coordinator:
   /cli-executor --component=app-proxy-coordinator --subcommand=start-server

3. Verify Coordinator endpoint in Worker config
```

### Migration Errors

**Database migrations pending:**
```
⚠️ Warning: Database migrations pending

Details: Database is behind by 2 migrations

Recommended actions:
1. Check migration status:
   /db-status

2. Apply migrations:
   /db-migrate

3. Retry starting component

Note: Starting with pending migrations may cause errors
```

---

## Related Skills

- `/db-status` - Check database migration status
- `/db-migrate` - Apply database migrations
- `/db-rebase` - Resolve diverged migration heads

---

## Examples

### Example 1: Component Discovery

**User:** "What Backend.AI components can I run?"

**Agent:**
```
Available Backend.AI components:

1. mgr                    - Manager (core orchestration)
2. ag                     - Agent (compute resources)
3. storage                - Storage Proxy (storage abstraction)
4. web                    - Web Server (UI)
5. app-proxy-coordinator  - App Proxy Coordinator (routing)
6. app-proxy-worker       - App Proxy Worker (request handling)

Use: /cli-executor --component=<name> to run a component
```

### Example 2: Starting Manager

**User:** "Start manager server"

**Agent:**
```
🔍 Pre-flight checks for Manager:

✅ PostgreSQL database running
✅ Redis running
✅ etcd running
✅ Database schema up-to-date
✅ Configuration file exists

📌 Running: ./backend.ai mgr start-server

Note: This command blocks the terminal.
- Press Ctrl+C to stop
- Open new terminal for other commands
- Logs will appear here

Executing...

[Manager starts and logs appear]
```

### Example 3: Complete Development Setup

**User:** "Set up and start manager for development"

**Agent workflow:**
```
Step 1: Check infrastructure
🔍 Checking Docker, PostgreSQL, Redis, etcd...
✅ All infrastructure running

Step 2: Check database schema
Running: /db-status
⚠️ 2 migrations pending

Step 3: Apply migrations
Running: /db-migrate
✅ Migrations applied successfully

Step 4: Verify setup
✅ All pre-flight checks passed

Step 5: Start Manager
Running: /cli-executor --component=mgr --subcommand=start-server
📌 Manager starting...

Manager is now running!
- API: http://localhost:8081
- Press Ctrl+C to stop
```

---

## Notes

### Blocking Commands

Commands like `start-server` block the terminal:
- Terminal shows real-time logs
- Press Ctrl+C to stop
- Open new terminal for other commands
- Use `screen` or `tmux` for persistent sessions

### Infrastructure Setup

**For development (halfstack):**
```bash
./scripts/run-dev.sh
```

This starts:
- PostgreSQL
- Redis
- etcd
- Other required infrastructure

**For production:**
- Set up infrastructure separately
- Use systemd/docker-compose for service management
- Configure monitoring and logging

### Configuration Files

Default locations:
- Manager: `configs/manager.toml`
- Agent: `configs/agent.toml`
- Storage: `configs/storage-proxy.toml`
- Web: `configs/web.toml`
- App Proxy Coordinator: `configs/app-proxy-coordinator.toml`
- App Proxy Worker: `configs/app-proxy-worker.toml`

Use sample configurations for development:
```bash
cp configs/manager.sample.toml configs/manager.toml
```

---

## Implementation Notes

- Uses `./backend.ai` entrypoint script
- Performs component-specific pre-flight checks
- Provides actionable error messages
- Integrates with database skills
- Guides users through complete workflows
- Handles both blocking and non-blocking commands
