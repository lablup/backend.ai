# Backend.AI Claude Code Skills

This directory contains Claude Code skills for Backend.AI development tasks.

## Available Skills

### Development Guides

#### `/repository-guide`
Guide for implementing Backend.AI repositories using base patterns.

**Use when:**
- Creating new repository
- Extending existing repository
- Understanding base utilities (Querier, BatchQuerier, Creator, etc.)
- Learning repository patterns

**Example:**
```
User: "How do I implement a new repository?"
Agent: /repository-guide
```

**Key Topics:**
- Base pattern overview (Querier, BatchQuerier, Creator, Updater, Purger)
- SearchScope for multi-tenant access control
- Transaction management
- Query optimization
- Type safety

---

#### `/tdd-guide`
Test-Driven Development workflow guide for Backend.AI.

**Use when:**
- Starting new feature implementation
- Fixing bugs with test-first approach
- Learning TDD workflow
- Understanding test strategies

**Example:**
```
User: "How do I follow TDD for this feature?"
Agent: /tdd-guide
```

**Key Topics:**
- TDD cycle: Red → Green → Refactor
- Scenario definition (success + exception cases)
- Test structure and fixtures
- Repository vs. Service testing strategies
- Quality checks integration

**Workflow:**
1. Define test scenarios
2. Write failing tests
3. Implement minimum code
4. Pass tests
5. Refactor with confidence

---

#### `/service-guide`
Guide for implementing Backend.AI service layer with Actions, Processors, and Service methods.

**Use when:**
- Creating new service
- Implementing Actions/ActionResults
- Setting up Processors
- Understanding service patterns
- Learning Action-Service-Repository flow

**Example:**
```
User: "How do I implement a service layer?"
Agent: /service-guide
```

**Key Topics:**
- Actions and ActionResults patterns
- Processors orchestration
- Service method implementation
- Repository integration
- Testing with mocked repositories

**Workflow:**
1. Define operations enum
2. Create base action classes
3. Implement concrete actions
4. Define service protocol
5. Implement service methods
6. Create processor package
7. Write tests (mock repositories)
8. Integrate with API handlers

---

#### `/api-guide`
Guide for implementing REST and GraphQL APIs with scope, filter, admin_ prefix patterns, and client SDK/CLI integration.

**Use when:**
- Creating REST API endpoints
- Implementing GraphQL resolvers
- Understanding scope/filter patterns
- Implementing admin operations
- Integrating with client SDK/CLI

**Example:**
```
User: "How do I implement a REST API with scope and filters?"
Agent: /api-guide
```

**Key Topics:**
- REST API patterns (scope, filter, admin_, pagination)
- GraphQL patterns (scope, filter, admin_, cursor)
- REST + CLI + SDK bundle integration
- Testing strategies (REST → CLI → SDK)
- Permission checking patterns

**Coverage:**
- **REST API**: Handler, adapter, scope, filter, pagination
- **GraphQL**: Resolver, input types, admin check, cursor pagination
- **Client SDK**: BaseFunction, @api_function, Session
- **CLI**: Click commands, integration with SDK

---

### Database Management

#### `/db-status`
Check current database schema version and migration status.

**Use when:**
- Before applying migrations
- After pulling code changes
- Debugging database issues
- Verifying migration completion

**Example:**
```
User: "Check database migration status"
Agent: /db-status
```

**Supported components:**
- `manager` (default) - Main manager database
- `accountmgr` - Account manager database
- `appproxy` - Application proxy database

---

#### `/db-migrate`
Apply database schema migrations (upgrade/downgrade).

**Use when:**
- Pending migrations need to be applied
- Rolling back schema changes
- Initial database setup

**Example:**
```
User: "Run database migrations"
Agent:
1. /db-status  # Check current status
2. /db-migrate  # Apply migrations
3. /db-status  # Verify success
```

**Safety features:**
- Pre-flight checks before execution
- Error diagnosis with actionable solutions
- Automatic detection of multiple heads

---

### Component Execution

#### `/cli-executor`
Execute Backend.AI component CLI commands with guidance and pre-flight checks.

**Use when:**
- Starting development services
- Running component health checks
- Executing administrative tasks
- Troubleshooting component issues

**Example:**
```
User: "Start manager server"
Agent:
1. Runs pre-flight checks (DB, Redis, etcd)
2. Checks database migrations
3. Guides through execution
4. Provides troubleshooting if errors
```

**Supported components:**
- `mgr` - Manager (core orchestration)
- `ag` - Agent (compute resources)
- `storage` - Storage Proxy (storage abstraction)
- `web` - Web Server (UI)
- `app-proxy-coordinator` - App Proxy Coordinator (routing)
- `app-proxy-worker` - App Proxy Worker (request handling)

**Features:**
- Component-specific pre-flight checks
- Infrastructure dependency verification
- Automatic error diagnosis
- Command suggestions

---

## Skill Usage

### Natural Language

Skills can be invoked using natural language:

```
"Check database migration status"
"Run database migrations"
"Start manager server"
"Create migration for new field"
"Resolve diverged heads"
```

Claude Code will automatically invoke the appropriate skill.

### Direct Invocation

Skills can also be invoked directly:

```
/db-status
/db-status --component=appproxy
/db-migrate
/db-migrate --component=appproxy
/cli-executor
/cli-executor --component=mgr
/cli-executor --component=mgr --subcommand=health
```

---

## Workflow Examples

### TDD Feature Development

```
1. Read guides: /repository-guide, /service-guide, /tdd-guide
2. Define test scenarios (success + exceptions)
3. Write failing tests
4. Run tests: pants test tests/manager/{layer}/test_feature.py
5. Implement using base patterns
6. Run tests: pants test --changed-since=HEAD~1
7. Refactor: pants fmt, pants check, pants lint
```

### Implementing Complete Feature Stack

```
1. Repository layer: /repository-guide
   - Define scope, querier patterns
   - Implement repository methods
   - Test with real DB (with_tables)

2. Service layer: /service-guide
   - Define Actions/ActionResults
   - Implement service methods
   - Create processor package
   - Test with mocked repositories

3. API layer: /api-guide
   - Implement REST handler or GraphQL resolver
   - Add scope/filter/admin patterns
   - Integrate with processors

4. Client integration: /api-guide
   - Add SDK function (@api_function)
   - Create CLI command
   - Test REST → CLI → SDK flow
```

### Daily Development Workflow

```
1. Pull code: git pull origin main
2. Check database: /db-status
3. Apply migrations: /db-migrate
4. Start components: /cli-executor --component=mgr
```

### Creating New Migration

```
1. Modify SQLAlchemy models
2. Generate migration: ./py -m alembic revision --autogenerate -m "Add new field"
3. Review generated file
4. Test upgrade: /db-migrate
5. Test downgrade: /db-migrate --direction=downgrade --target=-1
6. Re-upgrade: /db-migrate
7. Commit migration file
```

### Resolving Merge Conflicts

```
1. Merge branches: git merge feature-branch
2. Check for diverged heads: /db-status
3. If diverged:
   - Check history: ./py -m alembic heads
   - Resolve: ./py -m scripts/alembic-rebase.py {base_head} {top_head}
4. Apply migrations: /db-migrate
5. Verify: /db-status
```

### Starting Development Environment

```
1. Start infrastructure: ./scripts/run-dev.sh
2. Check database: /db-status
3. Apply migrations if needed: /db-migrate
4. Start Manager: /cli-executor --component=mgr --subcommand=start-server
5. Start Agent: /cli-executor --component=ag --subcommand=start-server
```

---

## Skill Integration

Skills are designed to work together:

**Development Flow:**
- **repository-guide** → Data access layer → **service-guide**
- **service-guide** → Business logic → **api-guide**
- **api-guide** → API + SDK + CLI → Complete feature

**Testing Flow:**
- **tdd-guide** → Test strategy → **repository-guide** / **service-guide** / **api-guide**
- Tests → Quality checks (BUILDING.md)

**Infrastructure Flow:**
- **db-status** → Identifies issues → **db-migrate**
- **db-migrate** → Pre-flight checks with infrastructure and database
- **cli-executor** → Detects migration issues → **db-status** + **db-migrate**
- **cli-executor** → Pre-flight checks → Verifies infrastructure before starting components

---

## Documentation

Each skill provides:
- **Purpose**: When and why to use
- **Parameters**: Required and optional arguments
- **Execution Steps**: Step-by-step process
- **Error Handling**: Common errors and solutions
- **Examples**: Usage examples
- **Related Skills**: Links to related skills

Refer to individual skill SKILL.md files for detailed documentation.

---

## Troubleshooting

### Skills Not Working

**Symptom:** Skill not invoked by natural language

**Solution:**
- Try direct invocation: `/skill-name`
- Check skill name spelling
- Verify skill file exists: `.claude/skills/skill-name/SKILL.md`

---

### Command Execution Fails

**Symptom:** Skill runs but command fails

**Solution:**
1. Check error message from skill
2. Follow troubleshooting steps provided
3. Verify infrastructure running: `docker ps`
4. Check configuration files exist

---

### Database Issues

**Symptom:** Database connection or migration errors

**Solution:**
1. Use `/db-status` to check current state
2. Verify PostgreSQL running: `docker ps | grep postgres`
3. Check database configuration
4. Start infrastructure: `./scripts/run-dev.sh`

---

## Additional Resources

- **CLAUDE.md**: Core development principles
- **tests/CLAUDE.md**: Testing guidelines and strategies
- **BUILDING.md**: Build system and quality enforcement
- **Component READMEs**: `src/ai/backend/{component}/README.md`
- **Configuration Guide**: `docs/config/`
- **Development Guide**: `docs/dev/`

---

## Contributing

When adding new skills:

1. Create skill directory: `.claude/skills/skill-name/`
2. Write SKILL.md following the template
3. Add examples and templates if needed
4. Update this README with skill documentation
5. Test skill with natural language and direct invocation

**Skill Template Structure:**
```yaml
---
name: skill-name
description: Brief description
disable-model-invocation: false
---

## Purpose
## Parameters
## Execution Steps
## Error Handling
## Related Skills
## Examples
```

---

## Feedback

If you encounter issues with skills or have suggestions:

1. **Report Issues**: GitHub Issues
2. **Documentation**: Update skill SKILL.md
3. **Improvements**: Submit PR with enhancements

Skills are continuously improved based on user feedback and real-world usage patterns.
