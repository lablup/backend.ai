# Export CLI Guide

This guide covers the Backend.AI CSV export system CLI commands for exporting data to CSV files.

## Overview

The export system allows administrators to export Backend.AI data to CSV files with flexible filtering and ordering options. Supported report types:
- **Users**: User account information
- **Sessions**: Compute session data
- **Projects**: Project (group) information
- **Audit Logs**: System audit log records

## Quick Start

### 1. List Available Reports

Check what report types are available for export:

```bash
./backend.ai admin export list-reports
```

This displays all available reports with their fields and descriptions.

### 2. Export Data

Export data to a file or stdout:

```bash
# Export to file
./backend.ai admin export users -o users.csv

# Export to stdout (pipe to file)
./backend.ai admin export sessions > sessions.csv
```

## Command Reference

### List Reports

Display all available export reports with their fields:

```bash
./backend.ai admin export list-reports
```

### Users Export

Export user account data.

**Available fields:** uuid, username, email, full_name, domain_name, role, status, created_at

```bash
./backend.ai admin export users [OPTIONS]

Options:
  -o, --output FILE           Output file path (default: stdout)
  --fields TEXT               Comma-separated field keys to include
  --filter-username TEXT      Filter by username (contains)
  --filter-email TEXT         Filter by email (contains)
  --filter-domain TEXT        Filter by domain name (contains)
  --filter-role TEXT          Filter by role (equals)
  --filter-status TEXT        Filter by status (equals)
  --filter-after DATETIME     Filter created_at after this datetime
  --filter-before DATETIME    Filter created_at before this datetime
  --order, -O TEXT            Order by field (format: 'field:asc' or 'field:desc')
  --encoding TEXT             CSV encoding (default: utf-8)
```

**Examples:**

```bash
# Export all users to file
./backend.ai admin export users -o users.csv

# Export specific fields
./backend.ai admin export users --fields uuid,username,email,status -o users.csv

# Filter by domain
./backend.ai admin export users --filter-domain "example.com" -o users.csv

# Filter by status with ordering
./backend.ai admin export users --filter-status active --order created_at:desc -o users.csv

# Filter by date range
./backend.ai admin export users \
  --filter-after "2026-01-01" \
  --filter-before "2026-12-31" \
  --order created_at:asc \
  -o users-2026.csv

# Export admin users only
./backend.ai admin export users --filter-role admin -o admins.csv

# Multi-level sorting
./backend.ai admin export users \
  --order domain_name:asc \
  --order username:asc \
  -o users-sorted.csv
```

### Sessions Export

Export compute session data.

**Available fields:** id, name, session_type, domain_name, access_key, status, status_info, scaling_group_name, cluster_size, occupying_slots, created_at, terminated_at

```bash
./backend.ai admin export sessions [OPTIONS]

Options:
  -o, --output FILE                Output file path (default: stdout)
  --fields TEXT                    Comma-separated field keys to include
  --filter-name TEXT               Filter by session name (contains)
  --filter-type TEXT               Filter by session type (equals)
  --filter-domain TEXT             Filter by domain name (contains)
  --filter-access-key TEXT         Filter by access key (contains)
  --filter-status TEXT             Filter by status (equals)
  --filter-scaling-group TEXT      Filter by scaling group (contains)
  --filter-created-after DATETIME  Filter created_at after
  --filter-created-before DATETIME Filter created_at before
  --filter-terminated-after DATETIME   Filter terminated_at after
  --filter-terminated-before DATETIME  Filter terminated_at before
  --order, -O TEXT                 Order by field (format: 'field:asc')
  --encoding TEXT                  CSV encoding (default: utf-8)
```

**Examples:**

```bash
# Export all sessions to file
./backend.ai admin export sessions -o sessions.csv

# Export specific fields
./backend.ai admin export sessions \
  --fields id,name,status,created_at,terminated_at \
  -o sessions.csv

# Filter by session type
./backend.ai admin export sessions --filter-type interactive -o interactive-sessions.csv

# Filter by status
./backend.ai admin export sessions --filter-status TERMINATED -o terminated.csv

# Filter sessions created in 2026
./backend.ai admin export sessions \
  --filter-created-after "2026-01-01" \
  --filter-created-before "2026-12-31" \
  -o sessions-2026.csv

# Filter by termination date range
./backend.ai admin export sessions \
  --filter-terminated-after "2026-06-01" \
  --filter-terminated-before "2026-06-30" \
  --order terminated_at:desc \
  -o terminated-june.csv

# Filter by scaling group
./backend.ai admin export sessions \
  --filter-scaling-group "gpu-cluster" \
  -o gpu-sessions.csv

# Filter by access key
./backend.ai admin export sessions \
  --filter-access-key "AKIA" \
  --order created_at:desc \
  -o user-sessions.csv

# Export with Korean encoding
./backend.ai admin export sessions \
  --encoding euc-kr \
  -o sessions-korean.csv
```

### Projects Export

Export project (group) data.

**Available fields:** id, name, description, domain_name, total_resource_slots, is_active, created_at

```bash
./backend.ai admin export projects [OPTIONS]

Options:
  -o, --output FILE           Output file path (default: stdout)
  --fields TEXT               Comma-separated field keys to include
  --filter-name TEXT          Filter by project name (contains)
  --filter-domain TEXT        Filter by domain name (contains)
  --filter-active/--filter-inactive  Filter by active status
  --filter-after DATETIME     Filter created_at after
  --filter-before DATETIME    Filter created_at before
  --order, -O TEXT            Order by field (format: 'field:asc')
  --encoding TEXT             CSV encoding (default: utf-8)
```

**Examples:**

```bash
# Export all projects to file
./backend.ai admin export projects -o projects.csv

# Export specific fields
./backend.ai admin export projects \
  --fields id,name,domain_name,is_active \
  -o projects.csv

# Filter by project name
./backend.ai admin export projects --filter-name "research" -o research-projects.csv

# Filter active projects only
./backend.ai admin export projects --filter-active -o active-projects.csv

# Filter inactive projects
./backend.ai admin export projects --filter-inactive -o inactive-projects.csv

# Filter by domain
./backend.ai admin export projects \
  --filter-domain "university" \
  --order name:asc \
  -o university-projects.csv

# Filter by creation date with ordering
./backend.ai admin export projects \
  --filter-after "2026-01-01" \
  --order created_at:desc \
  -o recent-projects.csv
```

### Audit Logs Export

Export system audit log records for compliance and monitoring.

**Available fields:** id, action_id, entity_type, entity_id, operation, status, created_at, description, request_id, triggered_by, duration

```bash
./backend.ai admin export audit-logs [OPTIONS]

Options:
  -o, --output FILE           Output file path (default: stdout)
  --fields TEXT               Comma-separated field keys to include
  --filter-entity-type TEXT   Filter by entity type (equals)
  --filter-entity-id TEXT     Filter by entity ID (contains)
  --filter-operation TEXT     Filter by operation (equals)
  --filter-status TEXT        Filter by status (equals)
  --filter-triggered-by TEXT  Filter by triggered_by (contains)
  --filter-request-id TEXT    Filter by request ID (contains)
  --filter-after DATETIME     Filter created_at after
  --filter-before DATETIME    Filter created_at before
  --order, -O TEXT            Order by field (format: 'field:asc')
  --encoding TEXT             CSV encoding (default: utf-8)
```

**Examples:**

```bash
# Export all audit logs to file
./backend.ai admin export audit-logs -o audit-logs.csv

# Export specific fields
./backend.ai admin export audit-logs \
  --fields created_at,entity_type,operation,status,triggered_by \
  -o audit-logs.csv

# Filter by entity type (e.g., sessions)
./backend.ai admin export audit-logs \
  --filter-entity-type session \
  -o session-audit.csv

# Filter by operation type
./backend.ai admin export audit-logs \
  --filter-operation create \
  -o create-operations.csv

# Filter by status (success/failure)
./backend.ai admin export audit-logs \
  --filter-status success \
  -o successful-operations.csv

# Filter by user
./backend.ai admin export audit-logs \
  --filter-triggered-by "admin@example.com" \
  -o admin-actions.csv

# Filter by date range for compliance reporting
./backend.ai admin export audit-logs \
  --filter-after "2026-01-01" \
  --filter-before "2026-03-31" \
  --order created_at:asc \
  -o q1-audit-report.csv

# Filter by specific request ID for debugging
./backend.ai admin export audit-logs \
  --filter-request-id "req-abc123" \
  -o request-trace.csv

# Comprehensive audit trail
./backend.ai admin export audit-logs \
  --filter-entity-type user \
  --filter-operation delete \
  --filter-after "2026-06-01" \
  --order created_at:desc \
  -o user-deletions.csv
```

## Common Workflows

### Monthly User Report

Generate a monthly report of active users:

```bash
./backend.ai admin export users \
  --filter-status active \
  --filter-after "2026-01-01" \
  --filter-before "2026-01-31" \
  --fields uuid,username,email,domain_name,created_at \
  --order created_at:desc \
  -o january-users-report.csv
```

### Session Usage Report

Export session data for billing or resource analysis:

```bash
./backend.ai admin export sessions \
  --filter-created-after "2026-01-01" \
  --filter-created-before "2026-01-31" \
  --fields id,name,access_key,session_type,occupying_slots,created_at,terminated_at \
  --order created_at:asc \
  -o january-sessions.csv
```

### Compliance Audit Report

Generate audit logs for compliance review:

```bash
./backend.ai admin export audit-logs \
  --filter-after "2026-01-01" \
  --filter-before "2026-03-31" \
  --fields created_at,entity_type,entity_id,operation,status,triggered_by,description \
  --order created_at:asc \
  -o q1-compliance-report.csv
```

### Project Inventory

Export all active projects with their resource allocations:

```bash
./backend.ai admin export projects \
  --filter-active \
  --fields id,name,domain_name,total_resource_slots,created_at \
  --order domain_name:asc \
  -o active-projects-inventory.csv
```

### Terminated Sessions Analysis

Export recently terminated sessions for analysis:

```bash
./backend.ai admin export sessions \
  --filter-status TERMINATED \
  --filter-terminated-after "2026-06-01" \
  --fields id,name,status_info,created_at,terminated_at \
  --order terminated_at:desc \
  -o terminated-analysis.csv
```

## Field Selection

Use the `--fields` option to specify which columns to include in the export:

```bash
# Select only specific fields
./backend.ai admin export users --fields uuid,username,email -o users.csv

# Multiple fields with comma separation (no spaces)
./backend.ai admin export sessions \
  --fields id,name,status,created_at,terminated_at \
  -o sessions.csv
```

**Available fields by report type:**

| Report | Fields |
|--------|--------|
| Users | uuid, username, email, full_name, domain_name, role, status, created_at |
| Sessions | id, name, session_type, domain_name, access_key, status, status_info, scaling_group_name, cluster_size, occupying_slots, created_at, terminated_at |
| Projects | id, name, description, domain_name, total_resource_slots, is_active, created_at |
| Audit Logs | id, action_id, entity_type, entity_id, operation, status, created_at, description, request_id, triggered_by, duration |

## Ordering Results

Use the `--order` or `-O` option to sort results. Format: `field:direction`

- `asc`: Ascending order (A-Z, oldest first)
- `desc`: Descending order (Z-A, newest first)

```bash
# Single field ordering
./backend.ai admin export users --order created_at:desc -o users.csv

# Multi-level ordering (multiple -O flags)
./backend.ai admin export sessions \
  -O domain_name:asc \
  -O created_at:desc \
  -o sessions.csv
```

## Encoding Options

By default, CSV files are exported with UTF-8 encoding. For systems requiring legacy Korean encoding:

```bash
# UTF-8 encoding (default)
./backend.ai admin export users -o users.csv

# EUC-KR encoding for Korean Excel compatibility
./backend.ai admin export users --encoding euc-kr -o users-korean.csv
```

## Tips

1. **Use field selection**: Export only needed fields to reduce file size
2. **Filter large datasets**: Use date filters to limit result size
3. **Ordering matters**: Sort data in export to avoid post-processing
4. **Test filters first**: Export to stdout without `-o` to preview results
5. **Use date ranges**: Combine `--filter-after` and `--filter-before` for precise date filtering
6. **EUC-KR for Korean Excel**: Use `--encoding euc-kr` if opening in Korean Excel

## Troubleshooting

**Export hangs or takes too long:**
- Add date range filters to reduce the dataset
- Use field selection to export only needed columns
- Check server logs for timeout errors

**Empty output:**
- Verify filter conditions match existing data
- Check if the date format is correct (YYYY-MM-DD or "YYYY-MM-DD HH:MM:SS")
- Remove filters to test if data exists

**Encoding issues in Excel:**
- Use `--encoding utf-8` (default) for most applications
- Use `--encoding euc-kr` for Korean Windows Excel
- Save as UTF-8 CSV if Excel shows garbled text

**Permission denied:**
- Only superadmin users can access export functionality
- Verify your access credentials

**Field not found:**
- Use `./backend.ai admin export list-reports` to check available fields
- Field names are case-sensitive
