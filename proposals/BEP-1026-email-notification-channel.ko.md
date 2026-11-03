# BEP-1026: 이메일 알림 채널

## 동기

현재 Backend.AI 의 notification 시스템은 webhook 채널만 지원한다. 이메일 알림을 받으려면 사용자가 Zapier, IFTTT 같은 외부 webhook-to-email 서비스를 따로 구성해야 한다.

**이메일 채널이 필요한 이유:**
- 외부 서비스에 의존하지 않고 이메일 알림을 바로 보낸다
- webhook 구성이 어려운 사용자도 알림을 더 간단하게 설정할 수 있다

## 현재 설계

### 알림 전달 흐름

시스템 event 가 발생하면(예: session 시작) 다음 흐름으로 알림을 전달한다:

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

**한계**: 현재 알림을 보내는 수단은 webhook 하나로 제한된다.

## 제안 설계

### 구조 변경

NotificationCenter 의 channel registry 에 `EmailChannel` 을 추가한다:

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

### 이메일 채널 구현

#### 1. EmailConfig Schema

이메일 채널의 설정 model 이다. `smtplib` 와 executor 로 구현한 SMTP Reporter 구현과 같다.

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

Python 표준 라이브러리로 구현한 채널이다:

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

API 응답에서 민감한 password field 는 제외한다:

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

### API 변경

#### 다형 설정 설계

알림 채널 설정은 Union type 과 `model_validator(mode="before")` 로 type 을 판별한다:

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

**요청 DTO 구현:**

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

**상속 대신 Union 과 model_validator 를 사용하는 이유:**
- DTO class 는 상속으로 얻을 것이 없다(공유하는 field 나 method 가 없다)
- 요청에 `channel_type` 이 이미 있으므로 판별자로 사용한다
- 명시적인 변환 로직이 Pydantic 의 smart union 판별보다 분명하다
- 설정에 중복되는 `type` field 가 필요 없다

**GraphQL Input 에 OneOf 를 사용하는 이유:**
- Strawberry 의 `@strawberry.input(one_of=True)` 가 설정 type 을 정확히 하나만 받도록 보장한다
- GraphQL schema 수준에서 type-safe 한 입력 검증을 한다
- API 계약이 분명하다: webhook XOR email 이며 둘 다 설정할 수 없다

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
