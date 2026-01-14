# Fair Share Scheduler CLI Guide

This guide covers the Backend.AI fair share scheduler CLI commands for viewing fair share factors.

## Overview

The fair share scheduler ensures equitable resource allocation across users, projects, and domains based on their historical usage patterns. It calculates a **fair share factor** for each entity that influences scheduling priority:

- **Lower fair share factor** = Higher priority (less historical usage)
- **Higher fair share factor** = Lower priority (more historical usage)

**Note**: All fair share commands require **superadmin privileges**.

## Quick Start

### 1. View Domain Fair Shares

List all domain fair shares in a resource group:

```bash
./backend.ai fair-share domain list --resource-group default
```

### 2. View Project Fair Shares

List project fair shares filtered by domain:

```bash
./backend.ai fair-share project list --resource-group default --domain-name default
```

### 3. View User Fair Shares

List user fair shares for a specific project:

```bash
./backend.ai fair-share user list --resource-group default --project-id <PROJECT_ID>
```

## Command Reference

### Domain Fair Share Commands

#### List Domain Fair Shares

```bash
./backend.ai fair-share domain list [OPTIONS]

Options:
  --resource-group TEXT   Filter by resource group name
  --domain-name TEXT     Filter by domain name
  --limit INTEGER        Number of results (default: 20)
  --offset INTEGER       Starting offset for pagination
  --order-by TEXT        Sort field (fair_share_factor, domain_name, created_at)
  --order TEXT           Sort direction (ASC, DESC, default: DESC)
  --json                 Output as JSON format
```

Example:
```bash
# List domain fair shares sorted by fair share factor
./backend.ai fair-share domain list --resource-group default --order-by fair_share_factor --order ASC
```

#### Get Domain Fair Share Details

```bash
./backend.ai fair-share domain get <RESOURCE_GROUP> <DOMAIN_NAME>
```

Example:
```bash
./backend.ai fair-share domain get default default
```

### Project Fair Share Commands

#### List Project Fair Shares

```bash
./backend.ai fair-share project list [OPTIONS]

Options:
  --resource-group TEXT   Filter by resource group name
  --project-id TEXT      Filter by project ID
  --domain-name TEXT     Filter by domain name
  --limit INTEGER        Number of results (default: 20)
  --offset INTEGER       Starting offset for pagination
  --order-by TEXT        Sort field (fair_share_factor, created_at)
  --order TEXT           Sort direction (ASC, DESC, default: DESC)
  --json                 Output as JSON format
```

Example:
```bash
# List all project fair shares for a specific domain
./backend.ai fair-share project list --resource-group default --domain-name default
```

#### Get Project Fair Share Details

```bash
./backend.ai fair-share project get <RESOURCE_GROUP> <PROJECT_ID>
```

Example:
```bash
./backend.ai fair-share project get default 550e8400-e29b-41d4-a716-446655440000
```

### User Fair Share Commands

#### List User Fair Shares

```bash
./backend.ai fair-share user list [OPTIONS]

Options:
  --resource-group TEXT   Filter by resource group name
  --project-id TEXT      Filter by project ID
  --user-uuid TEXT       Filter by user UUID
  --domain-name TEXT     Filter by domain name
  --limit INTEGER        Number of results (default: 20)
  --offset INTEGER       Starting offset for pagination
  --order-by TEXT        Sort field (fair_share_factor, created_at)
  --order TEXT           Sort direction (ASC, DESC, default: DESC)
  --json                 Output as JSON format
```

Example:
```bash
# List users with lowest fair share factors (highest priority)
./backend.ai fair-share user list --resource-group default --order-by fair_share_factor --order ASC
```

#### Get User Fair Share Details

```bash
./backend.ai fair-share user get <RESOURCE_GROUP> <PROJECT_ID> <USER_UUID>
```

Example:
```bash
./backend.ai fair-share user get default 550e8400-e29b-41d4-a716-446655440000 660e8400-e29b-41d4-a716-446655440001
```

## Common Workflows

### Investigate Scheduling Delays

When a user reports their sessions are waiting longer than expected:

**1. Check the user's fair share factor:**
```bash
./backend.ai fair-share user get default <PROJECT_ID> <USER_UUID>
```

**2. Compare with other users in the same project:**
```bash
./backend.ai fair-share user list --resource-group default --project-id <PROJECT_ID> --order-by fair_share_factor --order ASC
```

### Monitor Domain Resource Distribution

**1. List all domain fair shares:**
```bash
./backend.ai fair-share domain list --resource-group default --json | jq '.'
```

**2. Identify high-usage domains:**
```bash
./backend.ai fair-share domain list --resource-group default --order-by fair_share_factor --order DESC
```

### Compare Fair Share Across Projects

```bash
# Get all projects' fair share factors in descending order
./backend.ai fair-share project list --resource-group default --order-by fair_share_factor --order DESC --json
```

### Export Fair Share Data for Analysis

```bash
# Export domain fair shares as JSON
./backend.ai fair-share domain list --resource-group default --limit 1000 --json > domain_fair_shares.json

# Export user fair shares as JSON
./backend.ai fair-share user list --resource-group default --limit 1000 --json > user_fair_shares.json
```

## Understanding Fair Share Data

### Fair Share Factor

The fair share factor is a value between 0 and 1:
- **0.0**: No historical usage, highest scheduling priority
- **1.0**: Maximum relative usage, lowest scheduling priority

### Calculation Snapshot

Each fair share record includes a calculation snapshot with:
- **fair_share_factor**: The computed scheduling priority factor
- **total_decayed_usage**: Resource usage with exponential decay applied
- **normalized_usage**: Usage normalized relative to other entities
- **lookback_start/end**: Time window used for calculation

## Output Formats

### Text Format (Default)

```
ID: 550e8400-e29b-41d4-a716-446655440000
Resource Group: default
Domain: default
Fair Share Factor: 0.234567
Normalized Usage: 0.234567
Created: 2024-01-15T10:30:00
---
```

### JSON Format

Use `--json` flag for machine-readable output:

```bash
./backend.ai fair-share domain list --resource-group default --json
```

## Tips

1. **Start with domain level**: Domain fair shares give a high-level view of resource distribution
2. **Use JSON for automation**: The `--json` flag provides structured output for scripts
3. **Filter by resource group**: Always specify `--resource-group` to view data for the correct resource pool
4. **Sort by fair share factor**: Use `--order-by fair_share_factor --order ASC` to find highest priority entities

## Troubleshooting

**No fair share data found:**
- The fair share scheduler may not have run yet for this resource group
- No sessions have been scheduled in this resource group

**Permission denied:**
- Fair share commands require superadmin privileges
- Verify your user account has superadmin role

**Unexpected fair share values:**
- Fair share factors are relative to other entities in the same resource group
- High usage by one entity affects all other entities' relative factors

## Related Commands

- `./backend.ai resource-usage domain list`: View resource usage history
- `./backend.ai session list`: View current and past sessions
- `./backend.ai scaling-group list`: List available resource groups
