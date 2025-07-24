# Backend.AI App Proxy

## Architecture Overview

### Core Components

1. **Common Module** (`src/ai/backend/appproxy/common/`)
   - Shared utilities, configuration, logging, types
   - Database utilities and distributed locking mechanisms
   - Configuration validation with Pydantic

2. **Coordinator** (`src/ai/backend/appproxy/coordinator/`)
   - REST API endpoints for circuit/worker management
   - PostgreSQL database models with SQLAlchemy 2.0
   - Alembic database migrations
   - CLI interface for server management

3. **Worker** (`src/ai/backend/appproxy/worker/`)
   - Multiple proxy backends: HTTP, H2, TCP, Traefik
   - Port-based and subdomain-based proxy frontends
   - Health check API
   - CLI interface for worker management

### Key Technologies

- **Web Framework**: aiohttp (fully async)
- **Database**: PostgreSQL with asyncpg and SQLAlchemy 2.0
- **Migrations**: Alembic
- **Configuration**: TOML with Pydantic validation
- **Service Discovery**: etcd integration
- **Caching**: Redis with sentinel support
- **Type Checking**: MyPy with Pydantic plugin


## Configuration

Configuration files are located in `configs/` with separate files for coordinator and worker:

- `configs/app-proxy-coordinator/sample.toml` - Coordinator configuration template
- `configs/app-proxy-worker/sample.toml` - Worker configuration template
- `configs/app-proxy-coordinator/halfstack.toml` - Development setup
- `configs/app-proxy-worker/halfstack.toml` - Development setup
