---
Author: Bo Keum Kim (bkkim@lablup.com)
Status: Draft
Created: 2026-01-13
Created-Version: 26.1.0
Target-Version: 26.1.0
Implemented-Version:
---

# BEP-1026: Email Notification Channel

## Motivation

Currently, Backend.AI's Notification system only supports Webhook channels. To receive email notifications, users must set up external webhook-to-email services (Zapier, IFTTT, etc.).

**Why Email Channel is needed:**
- Direct email notifications without external service dependencies
- Simpler notification setup for users who find webhook configuration difficult

## Current Design

### Notification Dispatch Flow

When a system event occurs (e.g., session started), notifications are dispatched through the following flow:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        System Event Trigger                                 │
│                    (Session started/terminated, etc.)                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ event data
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                  Manager                                    │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Event Handler                                                        │  │
│  │    1. Query enabled NotificationRules matching event type             │  │
│  │    2. For each rule, call NotificationCenter.process_rule()           │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                      │                                      │
│                                      ▼                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  NotificationCenter (src/ai/backend/manager/notification/)            │  │
│  │    1. Render message template with Jinja2                             │  │
│  │    2. Create handler based on channel_type                            │  │
│  │    3. Call handler.send(message)                                      │  │
│  │                                                                       │  │
│  │    Channel Registry:                                                  │  │
│  │    ┌─────────────────────────────────────────────────────────────┐    │  │
│  │    │  WEBHOOK → WebhookChannel (HTTP POST to configured URL)     │    │  │
│  │    └─────────────────────────────────────────────────────────────┘    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                      │                                      │
│                                      ▼                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  WebhookChannel                                                       │  │
│  │    - HTTP POST request to webhook URL                                 │  │
│  │    - Uses shared HTTP client pool                                     │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        External Webhook Endpoint                            │
│                    (Slack, Discord, custom webhook, etc.)                   │
│                                                                             │
│   ⚠️  Email notifications require external webhook-to-email service         │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Limitation**: Currently, the means of sending notifications is limited to a single webhook.

## Proposed Design

### Architecture Changes

Add `EmailChannel` to the NotificationCenter's channel registry:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        System Event / Validation Request                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Manager                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  NotificationCenter                                                   │  │
│  │    1. Render message template with Jinja2                             │  │
│  │    2. Create handler based on channel_type                            │  │
│  │    3. Call handler.send(message)                                      │  │
│  │                                                                       │  │
│  │    Channel Registry (updated):                                        │  │
│  │    ┌─────────────────────────────────────────────────────────────┐    │  │
│  │    │  WEBHOOK → WebhookChannel                                   │    │  │
│  │    │  EMAIL   → EmailChannel (new)                               │    │  │
│  │    └─────────────────────────────────────────────────────────────┘    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                      │                                      │
│                    ┌─────────────────┴─────────────────┐                    │
│                    ▼                                   ▼                    │
│  ┌──────────────────────────────┐   ┌──────────────────────────────┐        │
│  │  WebhookChannel (existing)   │   │  EmailChannel (new)          │        │
│  │    - HTTP POST to URL        │   │    - SMTP connection         │        │
│  │    - Shared HTTP client pool │   │    - TLS/STARTTLS support    │        │
│  └──────────────────────────────┘   │    - Async via executor      │        │
│                    │                └──────────────────────────────┘        │
│                    │                                   │                    │
└────────────────────│───────────────────────────────────│────────────────────┘
                     ▼                                   ▼
          ┌──────────────────┐                ┌──────────────────┐
          │  Webhook Server  │                │   SMTP Server    │
          │  (Slack, etc.)   │                │ (Gmail, etc.)    │
          └──────────────────┘                └──────────────────┘
```

### Email Channel Implementation

#### 1. EmailConfig Schema

Configuration model for email channel
This is the same as the SMTP Reporter implementation, which is also implemented using `smtplib` and an executor

```python

class EmailConfig(BaseModel):
    """Email channel configuration."""
    smtp: SMTPConnectionConfig
    message: EmailMessageConfig
    auth: SMTPAuthConfig | None = None

# Union type for config polymorphism
NotificationChannelConfigType = WebhookConfig | EmailConfig

class SMTPConnectionConfig(BaseModel):
    """SMTP server connection settings."""
    host: str                    # SMTP server hostname
    port: int = 587              # Default: submission port with STARTTLS
    use_tls: bool = True         # Enable TLS/STARTTLS
    timeout: int = 30            # Connection timeout (seconds)

class EmailMessageConfig(BaseModel):
    """Email message settings."""
    from_email: str              # Sender email address
    to_emails: list[str]         # Recipient email addresses
    subject_template: str = "Backend.AI Notification"

class SMTPAuthConfig(BaseModel):
    """SMTP authentication credentials."""
    username: str
    password: str                # Stored in database
```

#### 2. EmailChannel Class

Channel implementation using Python standard library:

```python
class EmailChannel(AbstractNotificationChannel):
    """
    Email notification channel using smtplib.

    Key design decisions:
    - Library: Python stdlib smtplib + email.mime (no external dependencies)
    - Async: asyncio.run_in_executor() for blocking SMTP operations
    - Connection: Per-send connection (no pooling for simplicity)
    - Security: TLS/STARTTLS support
    """

    async def send(self, message: NotificationMessage) -> SendResult:
        # Run blocking SMTP operations in thread pool
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._send_sync, message)

    def _send_sync(self, message: NotificationMessage) -> SendResult:
        # 1. Create SMTP connection
        # 2. Start TLS if configured
        # 3. Authenticate if credentials provided
        # 4. Build MIME message
        # 5. Send email
        # 6. Close connection
        ...
```


#### 3. Response Schema

API responses exclude sensitive password field:

```python
class EmailConfigResponse(ConfigResponse):
    """Email config response - password excluded for security."""
    smtp: SMTPConnectionConfigResponse
    message: EmailMessageConfigResponse
    auth: SMTPAuthConfigResponse | None = None

class SMTPAuthConfigResponse(BaseModel):
    username: str
    # password intentionally excluded
```

### API Changes

#### Polymorphic Config Design

The notification channel config uses Union types with `model_validator(mode="before")` for type discrimination:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Data Layer (Pydantic)                             │
│                                                                             │
│   Independent Config Models (no inheritance):                               │
│   ┌────────────────────┐    ┌────────────────────┐                          │
│   │   WebhookConfig    │    │    EmailConfig     │                          │
│   │   (BaseModel)      │    │    (BaseModel)     │                          │
│   └────────────────────┘    └────────────────────┘                          │
│                                                                             │
│   NotificationChannelConfigType = WebhookConfig | EmailConfig               │
│   (Union type - no base class needed)                                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ Request DTO uses model_validator
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Request DTO Layer (Pydantic)                           │
│                                                                             │
│   @model_validator(mode="before") converts dict → appropriate Config:       │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  channel_type: "webhook" → WebhookConfig(**config)                  │   │
│   │  channel_type: "email"   → EmailConfig(**config)                    │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ converted to
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         GraphQL Layer (Strawberry)                          │
│                                                                             │
│   Output (Union pattern):                                                   │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  config: WebhookConfigGQL | EmailConfigGQL                          │   │
│   │    - Pattern matching on config type for conversion                 │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│   Input (OneOf pattern):                                                    │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  NotificationChannelConfigInput @oneOf                              │   │
│   │    - webhook: WebhookConfigInput | null                             │   │
│   │    - email: EmailConfigInput | null     ← exactly one must be set   │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Request DTO Implementation:**

```python
class CreateNotificationChannelRequest(BaseModel):
    channel_type: NotificationChannelType
    config: WebhookConfig | EmailConfig  # Union type

    @model_validator(mode="before")
    @classmethod
    def convert_config(cls, data: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(data, dict):
            return data

        channel_type = data.get("channel_type")
        config = data.get("config")

        if isinstance(config, dict):
            match channel_type:
                case "webhook" | NotificationChannelType.WEBHOOK:
                    data["config"] = WebhookConfig(**config)
                case "email" | NotificationChannelType.EMAIL:
                    data["config"] = EmailConfig(**config)
        return data
```

**Why Union + model_validator instead of inheritance?**
- DTO classes don't benefit from inheritance (no shared fields/methods)
- `channel_type` already exists in request - use it as discriminator
- Explicit conversion logic is clearer than Pydantic's smart union discrimination
- No redundant `type` field needed in config

**Why OneOf for GraphQL Input?**
- Strawberry's `@strawberry.input(one_of=True)` ensures exactly one config type is provided
- Type-safe input validation at GraphQL schema level
- Clear API contract: webhook XOR email, not both

#### GraphQL Schema

```graphql
enum NotificationChannelType {
  WEBHOOK
  EMAIL  # New
}

# Config output - Union pattern
type WebhookConfigGQL {
  url: String!
}

type EmailConfigGQL {
  smtp: SMTPConnectionConfig!
  message: EmailMessageConfig!
  auth: SMTPAuthConfig  # password excluded for security
}

union NotificationChannelConfigGQL = WebhookConfigGQL | EmailConfigGQL

# Config input - OneOf pattern (exactly one must be provided)
input NotificationChannelConfigInput @oneOf {
  webhook: WebhookConfigInput
  email: EmailConfigInput
}

input EmailConfigInput {
  smtp: SMTPConnectionConfigInput!
  message: EmailMessageConfigInput!
  auth: SMTPAuthConfigInput
}
```

#### CLI

```bash
# Create email channel
backend.ai notification channel create \
  --name "Admin Email Alert" \
  --channel-type email \
  --config '{
    "smtp": {"host": "smtp.example.com", "port": 587},
    "message": {"from_email": "noreply@example.com", "to_emails": ["admin@example.com"]},
    "auth": {"username": "user", "password": "app-password"}
  }'

# Validate channel (send test email)
backend.ai notification channel validate <channel-id> --test-message "Test notification"
```
