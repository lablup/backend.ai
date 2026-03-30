# Notification CLI Guide

This guide covers the Backend.AI notification system CLI commands for managing notification channels and rules.

## Overview

The notification system allows you to configure webhooks that trigger when specific events occur in Backend.AI, such as:
- Session lifecycle events (started, terminated)
- Artifact download completion
- Custom events

The system consists of two main components:
- **Channels**: Webhook endpoints where notifications are sent
- **Rules**: Event-to-channel mappings with customizable message templates

## Quick Start

### 1. List Available Rule Types

Check what event types can trigger notifications:

```bash
./backend.ai notification rule types
```

This displays all available rule types with their message schemas, showing required and optional fields.

### 2. Create a Notification Channel

Create a webhook channel:

```bash
./backend.ai notification channel create "My Webhook" "https://your-webhook-url.example.com" \
  --description "Production alerts"
```

Save the channel ID from the output.

### 3. Create a Notification Rule

Link an event type to your channel with a message template:

```bash
./backend.ai notification rule create "Session Started Alert" \
  session.started \
  <CHANNEL_ID> \
  --template '{"text": "Session {{ session_id }} started"}' \
  --description "Alert on session start"
```

### 4. Verify Setup

Test your rule with sample data:

```bash
./backend.ai notification rule validate <RULE_ID> \
  --data '{"session_id": "test-123", "session_type": "interactive", "cluster_mode": "single-node", "status": "RUNNING"}'
```

## Command Reference

### Channel Commands

#### List Channels

```bash
# List all channels
./backend.ai notification channel list

# List only enabled channels
./backend.ai notification channel list --enabled-only
```

#### Get Channel Details

```bash
./backend.ai notification channel info <CHANNEL_ID>
```

#### Create Channel

```bash
./backend.ai notification channel create <NAME> <WEBHOOK_URL> [OPTIONS]

Options:
  --channel-type TEXT     Channel type (default: webhook)
  --description TEXT      Channel description
  --disabled              Create channel as disabled
```

Example:
```bash
./backend.ai notification channel create "Production Alerts" \
  "https://your-webhook-url.example.com" \
  --description "Main webhook for production alerts"
```

#### Update Channel

```bash
./backend.ai notification channel update <CHANNEL_ID> [OPTIONS]

Options:
  --name TEXT            Update channel name
  --url TEXT             Update webhook URL
  --description TEXT     Update description
  --enable               Enable the channel
  --disable              Disable the channel
```

Example:
```bash
./backend.ai notification channel update 550e8400-e29b-41d4-a716-446655440000 \
  --url "https://new.webhook.url" \
  --enable
```

#### Delete Channel

```bash
./backend.ai notification channel delete <CHANNEL_ID>
```

#### Validate Channel

Test a channel by sending a test message:

```bash
./backend.ai notification channel validate <CHANNEL_ID> --data <MESSAGE>
./backend.ai notification channel validate <CHANNEL_ID> --data-file <FILE_PATH>
```

Example:
```bash
./backend.ai notification channel validate 550e8400-e29b-41d4-a716-446655440000 \
  --data '{"text": "Test notification"}'
```

### Rule Commands

#### List Rule Types

Display all available event types with their schemas:

```bash
./backend.ai notification rule types
```

#### Get Rule Type Schema

Display the message schema for a specific rule type:

```bash
./backend.ai notification rule schema <RULE_TYPE>
```

Example:
```bash
./backend.ai notification rule schema session.started
```

#### List Rules

```bash
# List all rules
./backend.ai notification rule list

# List only enabled rules
./backend.ai notification rule list --enabled-only

# Filter by rule types
./backend.ai notification rule list --rule-types session.started --rule-types session.terminated
```

#### Get Rule Details

```bash
./backend.ai notification rule info <RULE_ID>
```

#### Create Rule

```bash
./backend.ai notification rule create <NAME> <RULE_TYPE> <CHANNEL_ID> [OPTIONS]

Options:
  --template TEXT        Jinja2 template string
  --template-file FILE   Path to template file (use '-' for stdin)
  --description TEXT     Rule description
  --disabled             Create rule as disabled

Note: Must provide either --template or --template-file (but not both)
```

Examples:

**Inline template:**
```bash
./backend.ai notification rule create "Session Started" \
  session.started \
  550e8400-e29b-41d4-a716-446655440000 \
  --template '{"text": "Session {{ session_id }} ({{ session_type }}) started"}'
```

**Template file:**
```bash
./backend.ai notification rule create "Session Started" \
  session.started \
  550e8400-e29b-41d4-a716-446655440000 \
  --template-file templates/session_started.json
```

#### Update Rule

```bash
./backend.ai notification rule update <RULE_ID> [OPTIONS]

Options:
  --name TEXT                Update rule name
  --description TEXT         Update description
  --message-template TEXT    Update template string
  --template-file FILE       Update from template file
  --enable                   Enable the rule
  --disable                  Disable the rule
```

Example:
```bash
./backend.ai notification rule update 660e8400-e29b-41d4-a716-446655440000 \
  --message-template '{"text": "Updated: Session {{ session_id }} started"}' \
  --enable
```

#### Delete Rule

```bash
./backend.ai notification rule delete <RULE_ID>
```

#### Validate Rule

Test a rule by rendering its template with sample data:

```bash
./backend.ai notification rule validate <RULE_ID> --data <JSON_DATA>
./backend.ai notification rule validate <RULE_ID> --data-file <JSON_FILE>
```

Example:
```bash
./backend.ai notification rule validate 660e8400-e29b-41d4-a716-446655440000 \
  --data '{"session_id": "sess-123", "session_type": "interactive", "cluster_mode": "single-node", "status": "RUNNING"}'
```

## Common Workflows

### Setup Session Lifecycle Notifications

**1. Create a webhook channel:**
```bash
./backend.ai notification channel create "Production Notifications" \
  "https://your-webhook-url.example.com"
```

**2. Create session started rule:**
```bash
# Save this as session_started.json
cat > session_started.json << 'EOF'
{
  "title": "Session Started",
  "session_id": "{{ session_id }}",
  "session_name": "{{ session_name or 'N/A' }}",
  "session_type": "{{ session_type }}",
  "cluster_mode": "{{ cluster_mode }}",
  "status": "{{ status }}"
}
EOF

./backend.ai notification rule create "Production Session Started" \
  session.started \
  <CHANNEL_ID> \
  --template-file session_started.json
```

**3. Create session terminated rule:**
```bash
# Save this as session_terminated.json
cat > session_terminated.json << 'EOF'
{
  "title": "Session Terminated",
  "session_id": "{{ session_id }}",
  "session_name": "{{ session_name or 'N/A' }}",
  "session_type": "{{ session_type }}",
  "termination_reason": "{{ termination_reason or 'N/A' }}"
}
EOF

./backend.ai notification rule create "Production Session Terminated" \
  session.terminated \
  <CHANNEL_ID> \
  --template-file session_terminated.json
```

### Setup Artifact Download Notifications

```bash
# Create artifact download completion rule
./backend.ai notification rule create "Artifact Downloaded" \
  artifact.download.completed \
  <CHANNEL_ID> \
  --template '{"text": "Artifact {{ artifact_name }} ({{ artifact_type }}) {{ 'successfully' if success else 'failed to be' }} downloaded from {{ registry_type }}, status: {{ status }}"}'
```

### Temporarily Disable Notifications

```bash
# Disable a specific rule
./backend.ai notification rule update <RULE_ID> --disable

# Later, re-enable it
./backend.ai notification rule update <RULE_ID> --enable
```

### Update Webhook URL

```bash
# Update the channel's webhook URL
./backend.ai notification channel update <CHANNEL_ID> \
  --url "https://new.webhook.url"
```

## Available Rule Types

### session.started

Triggered when a compute session transitions to RUNNING state.

**Available fields:**
- `session_id` (required): Session UUID
- `session_name` (optional): User-defined session name
- `session_type` (required): Session type (interactive, batch, inference, system)
- `cluster_mode` (required): Cluster mode (single-node, multi-node)
- `status` (required): Session status

**Example template:**
```json
{
  "text": "Session {{ session_id }} ({{ session_type }}) started in {{ cluster_mode }} mode"
}
```

### session.terminated

Triggered when a compute session transitions to TERMINATED state.

**Available fields:**
- `session_id` (required): Session UUID
- `session_name` (optional): User-defined session name
- `session_type` (required): Session type
- `cluster_mode` (required): Cluster mode
- `status` (required): Final status
- `termination_reason` (optional): Reason for termination

**Example template:**
```json
{
  "text": "Session {{ session_id }} terminated. Reason: {{ termination_reason or 'User requested' }}"
}
```

### artifact.download.completed

Triggered when an artifact download operation completes.

**Available fields:**
- `artifact_id` (required): Artifact UUID
- `artifact_name` (required): Artifact name
- `artifact_type` (required): Artifact type (MODEL, PACKAGE, IMAGE)
- `registry_type` (required): Registry type (HARBOR, HUGGINGFACE, RESERVOIR)
- `registry_id` (required): Registry UUID
- `version` (optional): Artifact version
- `status` (required): Artifact revision status (AVAILABLE, NEEDS_APPROVAL, FAILED)
- `success` (required): Whether the download operation succeeded (true/false)
- `digest` (optional): Artifact revision digest
- `verification_result` (optional): Verification result object

**Example template:**
```json
{
  "title": "Artifact Download {{ 'Completed' if success else 'Failed' }}",
  "artifact": "{{ artifact_name }} (v{{ version or 'latest' }})",
  "registry": "{{ registry_type }}",
  "status": "{{ status }}",
  "digest": "{{ digest or 'N/A' }}"
}
```

## Template Syntax

Templates use Jinja2 syntax for variable interpolation and logic.

**Variable substitution:**
```
{{ variable_name }}
```

**Default values:**
```
{{ session_name or 'Unnamed Session' }}
```

**Conditionals:**
```
{% if termination_reason %}Reason: {{ termination_reason }}{% endif %}
```

**Loops (for lists):**
```
{% for item in items %}
- {{ item }}
{% endfor %}
```

## Tips

1. **Test before deploying**: Always validate rules with test data before enabling them in production
2. **Use meaningful names**: Give channels and rules descriptive names for easy management
3. **Template files for complex messages**: Use `--template-file` for multi-line or complex JSON structures
4. **Disable instead of delete**: Temporarily disable rules instead of deleting them if you might need them later
5. **Check schemas**: Use `./backend.ai notification rule types` to see exactly what fields are available for each event type

## Troubleshooting

**Channel validation fails:**
- Verify the webhook URL is correct and accessible
- Check if the webhook service is operational
- Ensure the message format matches what the webhook expects

**Rule validation fails:**
- Verify the notification data matches the rule type's schema
- Check for typos in field names
- Ensure required fields are provided

**Notifications not received:**
- Verify both channel and rule are enabled
- Check channel URL is correct
- Test the channel with `./backend.ai notification channel validate`
- Check Backend.AI manager logs for errors

**Template rendering errors:**
- Validate your Jinja2 syntax
- Ensure all referenced variables exist in the rule type schema
- Test with `./backend.ai notification rule validate` before deploying
