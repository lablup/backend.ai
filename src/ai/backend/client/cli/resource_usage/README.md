# Resource Usage CLI Guide

This guide covers the Backend.AI resource usage CLI commands for viewing historical resource usage data.

## Overview

The resource usage history tracks how resources have been consumed over time by domains, projects, and users. This data is stored in time-based buckets and is used by the fair share scheduler to calculate scheduling priorities.

**Note**: All resource usage commands require **superadmin privileges**.

## Quick Start

### 1. View Domain Usage History

List domain usage buckets in a resource group:

```bash
./backend.ai resource-usage domain list --resource-group default
```

### 2. View Project Usage History

List project usage buckets filtered by domain:

```bash
./backend.ai resource-usage project list --resource-group default --domain-name default
```

### 3. View User Usage History

List user usage buckets for a specific project:

```bash
./backend.ai resource-usage user list --resource-group default --project-id <PROJECT_ID>
```

## Command Reference

### Domain Usage Commands

#### List Domain Usage Buckets

```bash
./backend.ai resource-usage domain list [OPTIONS]

Options:
  --resource-group TEXT   Filter by resource group name
  --domain-name TEXT     Filter by domain name
  --bucket-date TEXT     Filter by bucket date (YYYY-MM-DD)
  --start-date TEXT      Filter buckets from this date (inclusive)
  --end-date TEXT        Filter buckets until this date (inclusive)
  --limit INTEGER        Number of results (default: 20)
  --offset INTEGER       Starting offset for pagination
  --order-by TEXT        Sort field (bucket_date, created_at)
  --order TEXT           Sort direction (ASC, DESC, default: DESC)
  --json                 Output as JSON format
```

Example:
```bash
# List last 7 days of domain usage for default resource group
./backend.ai resource-usage domain list --resource-group default --limit 7 --order-by bucket_date --order DESC
```

### Project Usage Commands

#### List Project Usage Buckets

```bash
./backend.ai resource-usage project list [OPTIONS]

Options:
  --resource-group TEXT   Filter by resource group name
  --project-id TEXT      Filter by project ID
  --domain-name TEXT     Filter by domain name
  --bucket-date TEXT     Filter by bucket date (YYYY-MM-DD)
  --start-date TEXT      Filter buckets from this date (inclusive)
  --end-date TEXT        Filter buckets until this date (inclusive)
  --limit INTEGER        Number of results (default: 20)
  --offset INTEGER       Starting offset for pagination
  --order-by TEXT        Sort field (bucket_date, created_at)
  --order TEXT           Sort direction (ASC, DESC, default: DESC)
  --json                 Output as JSON format
```

Example:
```bash
# List project usage for a specific domain
./backend.ai resource-usage project list --resource-group default --domain-name default --limit 30
```

### User Usage Commands

#### List User Usage Buckets

```bash
./backend.ai resource-usage user list [OPTIONS]

Options:
  --resource-group TEXT   Filter by resource group name
  --project-id TEXT      Filter by project ID
  --user-uuid TEXT       Filter by user UUID
  --domain-name TEXT     Filter by domain name
  --bucket-date TEXT     Filter by bucket date (YYYY-MM-DD)
  --start-date TEXT      Filter buckets from this date (inclusive)
  --end-date TEXT        Filter buckets until this date (inclusive)
  --limit INTEGER        Number of results (default: 20)
  --offset INTEGER       Starting offset for pagination
  --order-by TEXT        Sort field (bucket_date, created_at)
  --order TEXT           Sort direction (ASC, DESC, default: DESC)
  --json                 Output as JSON format
```

Example:
```bash
# List user usage history sorted by date
./backend.ai resource-usage user list --resource-group default --order-by bucket_date --order DESC
```

## Common Workflows

### Analyze Usage Trends

**1. View weekly domain usage:**
```bash
./backend.ai resource-usage domain list --resource-group default --limit 7 --order-by bucket_date --order DESC
```

**2. Compare project usage within a domain:**
```bash
./backend.ai resource-usage project list --resource-group default --domain-name default --json | jq 'sort_by(.total_usage.mem) | reverse'
```

### Investigate High Resource Consumers

**1. Find users with high usage in a project:**
```bash
./backend.ai resource-usage user list --resource-group default --project-id <PROJECT_ID> --json
```

**2. Track usage pattern over time:**
```bash
./backend.ai resource-usage user list --resource-group default --user-uuid <USER_UUID> --limit 30 --order-by bucket_date --order ASC
```

### Export Usage Data for Analysis

```bash
# Export domain usage as JSON
./backend.ai resource-usage domain list --resource-group default --limit 1000 --json > domain_usage.json

# Export user usage as JSON
./backend.ai resource-usage user list --resource-group default --limit 1000 --json > user_usage.json
```

## Understanding Usage Data

### Usage Buckets

Each usage bucket contains:
- **bucket_date**: The date for this usage record
- **total_usage**: Raw resource usage for the period (ResourceSlot)
- **decayed_usage**: Usage with exponential decay applied (ResourceSlot)

### ResourceSlot Format

Usage data is stored as ResourceSlot with fields like:
- **cpu**: CPU core-seconds used
- **mem**: Memory byte-seconds used
- **cuda.device**: GPU device-seconds used (if applicable)

### Decay Factor

The decayed usage applies exponential decay to give more weight to recent usage:
- Recent usage has higher impact on fair share calculation
- Older usage gradually decreases in importance
- Decay half-life is configured in the scheduler settings

## Output Formats

### Text Format (Default)

```
ID: 550e8400-e29b-41d4-a716-446655440000
Resource Group: default
Domain: default
Bucket Date: 2024-01-15
Total Usage: {"cpu": "3600.0", "mem": "8589934592"}
Decayed Usage: {"cpu": "3240.0", "mem": "7730941133"}
Created: 2024-01-15T00:00:00
---
```

### JSON Format

Use `--json` flag for machine-readable output:

```bash
./backend.ai resource-usage domain list --resource-group default --json
```

## Tips

1. **Use date filters**: Narrow down results with `--start-date` and `--end-date` for specific time ranges
2. **JSON for automation**: Use `--json` flag for scripts and data analysis
3. **Sort by date**: Use `--order-by bucket_date` to see chronological trends
4. **Combine with fair-share**: Use alongside `fair-share` commands to understand scheduling priorities

## Troubleshooting

**No usage data found:**
- Usage buckets are created when sessions run in the resource group
- Check if sessions have been scheduled recently

**Permission denied:**
- Resource usage commands require superadmin privileges
- Verify your user account has superadmin role

**Empty ResourceSlot values:**
- Zero usage indicates no sessions ran during that period
- Check session history for the time range

## Related Commands

- `./backend.ai fair-share domain list`: View domain fair share factors
- `./backend.ai fair-share user list`: View user fair share factors
- `./backend.ai session list`: View current and past sessions
- `./backend.ai scaling-group list`: List available resource groups
