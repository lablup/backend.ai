---
name: db-migrate
description: Apply database schema migrations (alembic upgrade head, alembic downgrade, resolve diverged heads) for Backend.AI components (manager, accountmgr, appproxy)
disable-model-invocation: false
---

## Purpose

Execute Alembic migrations to upgrade or downgrade database schema for Backend.AI components.

**When to use:**
- After pulling code with new migrations
- To apply pending schema changes
- To rollback migrations (downgrade)
- During initial database setup

**Safety note:** Always check status with `/db-status` before migrating.

## Parameters

- **component** (optional): Target component
  - `manager` (default) - Main manager database
  - `accountmgr` - Account manager database
  - `appproxy` - Application proxy database

- **direction** (optional): Migration direction
  - `upgrade` (default) - Apply newer migrations
  - `downgrade` - Rollback migrations

- **target** (optional): Target revision
  - `head` (default) - Latest migration
  - `<revision_id>` - Specific revision (e.g., abc123def456)
  - Relative: `+1`, `-1`, `+2`, etc.

## Pre-flight Checks

Before executing migration, verify:
1. ✅ Database connection available
2. ✅ No diverged heads (run `/db-status` first)
3. ✅ Backup exists (for downgrade operations)
4. ✅ Database in expected state

## Execution Steps

### 1. Verify Current Status
```bash
# Check current revision and pending migrations
/db-status --component=<component>
```

### 2. Select Alembic Config
- manager → `alembic.ini`
- accountmgr → `alembic-accountmgr.ini`
- appproxy → `alembic-appproxy.ini`

### 3. Execute Migration
```bash
./py -m alembic -c <config> <direction> <target>
```

**Examples:**
```bash
# Upgrade manager to latest
./py -m alembic -c alembic.ini upgrade head

# Upgrade appproxy to latest
./py -m alembic -c alembic-appproxy.ini upgrade head

# Downgrade manager by 1 revision
./py -m alembic -c alembic.ini downgrade -1

# Upgrade to specific revision
./py -m alembic -c alembic.ini upgrade abc123def456
```

### 4. Verify New Status
```bash
# Confirm migration success
/db-status --component=<component>
```

## Expected Output

**Successful upgrade:**
```
✅ Migration successful

Component: manager
Direction: upgrade
Target: head

Applied migrations:
  - abc123def456 → def456ghi789: Add domain fair share
  - def456ghi789 → ghi789jkl012: Add session priority

New status: Database is up-to-date

Next steps:
- Verify application functionality
- Restart affected services if needed
```

**Successful downgrade:**
```
✅ Migration successful

Component: manager
Direction: downgrade
Target: -1

Reverted migrations:
  - ghi789jkl012 → def456ghi789: Add session priority (reverted)

New status: Database at revision def456ghi789

Warning: Downgrade may have removed data or features.
Verify application compatibility.
```

## Error Handling

**Multiple heads detected:**
```
❌ Error: Multiple heads detected

Details: Cannot proceed with migration when heads are diverged

Recommended actions:
1. Check diverged heads: /db-status
2. Resolve heads: /db-rebase
3. Retry migration: /db-migrate

Related skill: /db-rebase
```

**Cannot locate revision:**
```
❌ Error: Cannot locate revision 'abc123'

Details: Revision not found in migration history

Recommended actions:
1. List available revisions:
   ./py -m alembic -c alembic.ini history
2. Check for typos in revision ID
3. Ensure you're using correct component config

Use /db-status to see current and head revisions.
```

**Foreign key constraint failed:**
```
❌ Error: Foreign key constraint violation

Details: Cannot add/modify column due to existing data

Recommended actions:
1. Check migration script for data migration logic
2. Manually fix data integrity issues
3. Consider modifying migration to handle existing data
4. Rollback: /db-migrate --direction=downgrade --target=-1

This usually requires manual intervention. Review migration file.
```

**Database connection failed:**
```
❌ Error: Cannot connect to database

Details: Connection refused to localhost:5432

Recommended actions:
1. Check PostgreSQL is running: docker ps | grep postgres
2. Verify database configuration
3. Start infrastructure: ./scripts/run-dev.sh

Related skill: /cli-executor
```

**Migration file missing:**
```
❌ Error: Migration file not found

Details: Expected migration at versions/abc123_add_field.py

Recommended actions:
1. Ensure you pulled latest code: git pull
2. Check if migration was committed
3. Verify correct branch
4. Generate migration if needed: /db-create-migration
```

## Safety Notes

### Before Downgrade
- **Backup database:** Downgrades may lose data
- **Test on development:** Never test downgrade on production first
- **Review migration:** Check what data will be removed
- **Stop services:** Ensure no active connections during downgrade

### After Upgrade
- **Verify functionality:** Test key features after schema changes
- **Restart services:** Some changes require service restart
- **Monitor logs:** Check for migration-related errors
- **Document changes:** Note any manual steps required

### Best Practices
- **Always use version control:** Commit migrations to Git
- **Test migrations:** Verify upgrade AND downgrade work
- **Review autogenerated migrations:** Don't trust them blindly
- **Keep migrations small:** One logical change per migration

## Related Skills

- `/db-status` - Check status before and after migration
- `/db-rebase` - Resolve diverged heads before migration
- `/db-create-migration` - Create new migrations
- `/cli-executor` - Check infrastructure and start services

## Examples

**Apply pending migrations:**
```
User: "Run database migrations"
Agent:
1. /db-status  # Check current status
2. /db-migrate  # Apply migrations
3. /db-status  # Verify success
```

**Upgrade specific component:**
```
User: "Upgrade appproxy database"
Agent: /db-migrate --component=appproxy
```

**Rollback last migration:**
```
User: "Rollback last database migration"
Agent: /db-migrate --direction=downgrade --target=-1
```

**Upgrade to specific revision:**
```
User: "Upgrade database to revision abc123"
Agent: /db-migrate --target=abc123def456
```

## Workflow Integration

**Typical development workflow:**
```
1. Pull code: git pull origin main
2. Check status: /db-status
3. Apply migrations: /db-migrate
4. Start services: /cli-executor --component=mgr --subcommand=start-server
5. Verify functionality
```

**After creating new migration:**
```
1. Generate migration: /db-create-migration --message="Add new field"
2. Review generated file
3. Test upgrade: /db-migrate
4. Test downgrade: /db-migrate --direction=downgrade --target=-1
5. Re-upgrade: /db-migrate
6. Commit migration file
```

**Resolving merge conflicts:**
```
1. Merge branches: git merge feature-branch
2. Check for diverged heads: /db-status
3. If diverged, resolve: /db-rebase
4. Apply migrations: /db-migrate
5. Verify: /db-status
```

## Implementation Notes

- Uses Alembic's built-in migration engine
- Supports all three Backend.AI database components
- Provides clear error messages with actionable solutions
- Integrates with other skills for complete workflow
- Validates state before and after migration
