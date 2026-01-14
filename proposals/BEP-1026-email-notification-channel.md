---
Author: Bo Keum Kim (bkkim@lablup.com)
Status: Draft
Created: 2026-01-13
Created-Version: 26.1.0
Target-Version: 26.1.0
Implemented-Version: 26.1.0
---

# BEP-1026: Email Notification Channel

## Motivation

Currently, Backend.AI's Notification system only supports Webhook channels. To receive email notifications, users must set up external webhook-to-email services (Zapier, IFTTT, etc.).

**Why Email Channel is needed:**
- Direct email notifications without external service dependencies
- Simpler notification setup for users who find webhook configuration difficult

## Current Design

### System Architecture

The current notification system consists of two main flows: **Channel/Rule Management** (CRUD operations) and **Notification Dispatch** (actual message sending).

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Client (WebUI / CLI)                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
            ┌──────────────────┬──────────────────┬──────────────────┐
            │                  │                  │                  │
            ▼                  ▼                  ▼                  ▼
     GraphQL Mutation    GraphQL Query        REST API          CLI Command
    (create/update/      (list/get)      (/notifications/*)   (via Client SDK)
         delete)
            │                  │                  │                  │
            └──────────────────┴──────────────────┴──────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Manager                                        │
│  ┌────────────────────────────────┐  ┌────────────────────────────────┐     │
│  │  GraphQL API Layer             │  │  REST API Layer                │     │
│  │  (api/gql/notification/)       │  │  (api/notification/)           │     │
│  │    - Channel, Rule types       │  │    - /notifications/* routes   │     │
│  │    - Query/Mutation resolvers  │  │    - Pydantic DTOs             │     │
│  └────────────────────────────────┘  └────────────────────────────────┘     │
│                       │                          │                          │
│                       └────────────┬─────────────┘                          │
│                                    │                                        │
│                                    ▼                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Service Layer (src/ai/backend/manager/services/notification/)        │  │
│  │    - Action-Processor pattern                                         │  │
│  │    - CRUD operations for channels and rules                           │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                      │                                      │
│                                      ▼                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Repository Layer (src/ai/backend/manager/repositories/notification/) │  │
│  │    - Database access abstraction                                      │  │
│  │    - Creator/Updater patterns                                         │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                      │                                      │
│                                      ▼                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Data Layer                                                           │  │
│  │    - Models: NotificationChannelRow (channel_type + JSON config)      │  │
│  │    - Domain: NotificationChannelData, WebhookConfig                   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

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
class NotificationChannelConfig:
    pass

class WebhookConfig(NotificationChannelConfig):
    url: str

class EmailConfig(NotificationChannelConfig):
    """Email channel configuration."""
    smtp: SMTPConnectionConfig
    message: EmailMessageConfig
    auth: SMTPAuthConfig | None = None

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

The notification channel config uses polymorphism at multiple layers:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Data Layer (Pydantic)                             │
│                                                                             │
│   NotificationChannelConfig (abstract base)                                 │
│          ▲                                                                  │
│          │ extends                                                          │
│   ┌──────┴──────┐                                                           │
│   │             │                                                           │
│ WebhookConfig  EmailConfig                                                  │
│                                                                             │
│   NotificationChannelConfigType = WebhookConfig | EmailConfig               │
│   (Union type for Pydantic's smart union discrimination)                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ converted to
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         GraphQL Layer (Strawberry)                          │
│                                                                             │
│   Output (Interface pattern):                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  NotificationChannelConfigGQL (interface)                           │   │
│   │    - channel_type: NotificationChannelType  ← discriminator field   │   │
│   │          ▲                                                          │   │
│   │          │ implements                                               │   │
│   │   ┌──────┴──────┐                                                   │   │
│   │   │             │                                                   │   │
│   │ WebhookConfigGQL  EmailConfigGQL                                    │   │
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

**Why Interface for Output?**
- GraphQL clients can query common fields (`channel_type`) across all config types
- Type-specific fields are available via inline fragments (`... on EmailConfigGQL`)
- `channel_type` serves as discriminator field for client-side type narrowing

**Why OneOf for Input?**
- Strawberry's `@strawberry.input(one_of=True)` ensures exactly one config type is provided
- Type-safe input validation at GraphQL schema level
- Clear API contract: webhook XOR email, not both

#### GraphQL Schema

```graphql
enum NotificationChannelType {
  WEBHOOK
  EMAIL  # New
}

# Config output - Interface pattern with discriminator
interface NotificationChannelConfigGQL {
  channelType: NotificationChannelType!
}

type WebhookConfigGQL implements NotificationChannelConfigGQL {
  channelType: NotificationChannelType!
  url: String!
}

type EmailConfigGQL implements NotificationChannelConfigGQL {
  channelType: NotificationChannelType!
  smtp: SMTPConnectionConfig!
  message: EmailMessageConfig!
  auth: SMTPAuthConfig
}

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
