# Backend.AI Webserver

## Purpose

The Webserver provides a web-based user interface, maintains user sessions, and proxies requests signed with JWT (for GraphQL) or HMAC (for REST API) using the user's access key and secret key to the Manager API gateway. Login processing and authentication are all handled by the Manager.

## Key Responsibilities

### 1. Web UI Hosting
- Serve static web UI assets (HTML, CSS, JavaScript)
- Provide template rendering for server-side pages
- Handle web UI routing and navigation
- Provide responsive web interface

### 2. Session Management
- Maintain web sessions (Redis-based)
- Manage user's access key and secret key stored in sessions
- Handle session timeouts
- **Note**: Login processing and authentication are handled by Manager

### 3. Request Signing and Proxying
- Sign requests using user's access key/secret key
  - GraphQL requests: JWT signature
  - REST API requests: HMAC signature
- Forward signed API requests to Manager
- Stream API responses
- Support WebSocket proxying

### 4. Security
- CORS (Cross-Origin Resource Sharing) handling
- User input sanitization
- Rate limiting

## Entry Points

Webserver has 1 entry point to receive and process user requests.

### 1. REST API (Web UI + Proxy)

**Framework**: aiohttp (async HTTP server)

**Port**: 8080 (default)

**Key Features**:
- Session-based authentication (Redis)
- Request signing and proxying to Manager API (JWT/HMAC)

**Processing Flow**:

#### Login Flow
```
Browser → POST /auth/login → Webserver → Manager API (authenticate)
                                    ↓
                              Session created in Redis
                                    ↓
                          Session cookie sent to Browser
```

#### API Request Proxy Flow
```
Browser → API Request + Session Cookie → Webserver
                                            ↓
                                 Retrieve access/secret key from Redis session
                                            ↓
                                 Sign request (GraphQL: JWT, REST: HMAC)
                                            ↓
                                 Proxy to Manager API
                                            ↓
                                 Manager processes request
                                            ↓
                                 Response returned to Browser
```

**Integrated Architecture**:

```
┌─────────────┐
│   Browser   │
│  (Web UI)   │
└──────┬──────┘
       │
       ▼ Session Cookie + API Request
┌─────────────────────────────────┐
│      Webserver (Port 8080)      │
│  - Serve static assets          │
│  - Session management (Redis)   │
│  - Request signing (JWT/HMAC)   │
│  - Proxy to Manager             │
└──────┬──────────────────────────┘
       │
       ▼ Signed API Request (JWT/HMAC)
┌─────────────────────────────────┐
│    Manager API (Port 8081)      │
│  - Verify signature             │
│  - Process request              │
│  - Return response              │
└─────────────────────────────────┘
```

## Architecture

```
┌─────────────────────────────────────┐
│     Static Assets (static/)         │  ← HTML, CSS, JS
├─────────────────────────────────────┤
│    Templates (templates/)           │  ← Jinja2 templates
├─────────────────────────────────────┤
│  Authentication (auth.py)           │  ← Session management, JWT/HMAC signing
├─────────────────────────────────────┤
│   Session Manager (Redis)           │  ← Session storage
├─────────────────────────────────────┤
│     Proxy (proxy.py)                │  ← Request forwarding
└─────────────────────────────────────┘
```

## Directory Structure

```
web/
├── static/              # Static web assets
│   ├── css/            # Stylesheets
│   ├── js/             # JavaScript files
│   └── images/         # Images and icons
├── templates/           # Jinja2 templates
├── config/              # Configuration
├── cli/                 # CLI commands
├── auth.py              # Session management and request signing
├── proxy.py             # API proxy
├── security.py          # Security utilities
├── response.py          # Response helpers
├── stats.py             # Statistics tracking
├── server.py            # Main server entry point
└── template.py          # Template rendering
```

## Core Concepts

### Web Sessions
Web sessions track authenticated users:
- **Session ID**: Unique identifier stored in cookies
- **User ID**: Associated user in Manager
- **Access key**: User's API access key
- **Created/expires**: Session timestamps
- **Data**: Additional session data (preferences, etc.)

Session Lifecycle:
1. User logs in through Manager API
2. Manager returns access key and secret key
3. Webserver creates session in Redis and stores access/secret keys
4. Session cookie is sent to browser
5. Subsequent requests include session cookie
6. Webserver retrieves access/secret key from session and signs requests (GraphQL: JWT, REST API: HMAC)
7. Signed requests are proxied to Manager
8. Session expires after timeout or logout

### Authentication Flow

```
1. User visits web UI
   ↓
2. Webserver serves login page
   ↓
3. User submits credentials
   ↓
4. Webserver forwards login request to Manager API
   ↓
5. Manager authenticates and returns access key and secret key
   ↓
6. Webserver creates session in Redis and stores keys
   ↓
7. Session cookie is sent to browser
   ↓
8. User is redirected to main page
```

### Request Proxying

Session-based requests are proxied to Manager:

```
1. Browser sends API request with session cookie
   ↓
2. Webserver retrieves user's access key and secret key from session
   ↓
3. Webserver signs request with access key/secret key
   - GraphQL requests: JWT signature
   - REST API requests: HMAC signature
   ↓
4. Signed request is forwarded to Manager
   ↓
5. Manager verifies signature and processes request
   ↓
6. Webserver returns response to browser
```

Proxied Request Headers:
- `X-BackendAI-Token`: JWT token (GraphQL requests)
- `Authorization`: HMAC signature (REST API requests, based on access key/secret key)
- `X-BackendAI-Version`: API version
- `X-Forwarded-For`: Proxy chain

### Session Storage (Redis)

Session data is stored in Redis:
- **Key**: `websession:{session_id}`
- **Value**: JSON-encoded session data
- **TTL**: Session timeout (e.g., 1 hour)

Example session data:
```json
{
  "user_id": "user@example.com",
  "access_key": "AKIAIOSFODNN7EXAMPLE",
  "created_at": "2025-10-28T12:00:00Z",
  "last_accessed": "2025-10-28T12:30:00Z",
  "preferences": {
    "theme": "dark",
    "language": "en"
  }
}
```

## Security Features

### CORS Configuration
- Allow cross-origin requests from trusted domains
- Set appropriate CORS headers
- Support preflight OPTIONS requests
- Restrict allowed methods and headers

### Rate Limiting
Request limiting to prevent brute force attacks:
- **Limit**: Limited number of requests per access key
- **Response**: HTTP 429 Too Many Requests
- **Tracking**: Redis-based counter per access key

### Input Sanitization
- HTML escape user input
- Email format validation
- Path sanitization
- Injection attack prevention

## Configuration

See `configs/webserver/halfstack.conf` for configuration file examples.

### Key Configuration Items

**Basic Settings**:
- Listen address and port
- Session timeout and secret
- Manager API endpoint
- Redis connection information

**Security Settings**:
- Session timeout and secret
- Rate limiting configuration
- CORS configuration

## Infrastructure Dependencies

### Required Infrastructure

#### Redis (Session Storage)
- **Purpose**:
  - Store web session data
  - Validate session cookies
  - Manage session timeouts
- **Halfstack Port**: 8111 (host) → 6379 (container)
- **Key Patterns**:
  - `websession:{session_id}` - Web session data

#### Manager API Connection
- **Purpose**:
  - Forward login requests and receive access key/secret key
  - Proxy JWT (GraphQL) or HMAC (REST API) signed requests
  - Retrieve user information
- **Protocol**: HTTP/HTTPS
- **Halfstack Port**: 8091 (Manager)
- **Note**: Authentication is handled by Manager, Webserver only adds signatures

#### etcd (Global Configuration)
- **Purpose**:
  - Retrieve global configuration
  - Auto-discover Manager address
- **Halfstack Port**: 8121 (host) → 2379 (container)

### Optional Infrastructure (Observability)

#### Prometheus (Metrics Collection)
- **Purpose**:
  - Session management metrics
  - Request processing time
  - Proxy error tracking
- **Exposed Endpoint**: `http://localhost:8090/metrics`
- **Key Metrics**:
  - `backendai_api_request_count` - Total API requests
  - `backendai_api_request_duration_sec` - Request processing time

#### Loki (Log Aggregation)
- **Purpose**:
  - Session creation/termination events
  - Request signing and proxy events
  - Security violation events
  - Proxied request tracking
- **Log Labels**:
  - `user_id` - User identifier
  - `event` - Event type (session_create, proxy_request, etc.)
  - `status` - Success/failure

### SSL/TLS Configuration

**Development Environment**: HTTP mode (port 8090)
**Production Environment**: HTTPS mode (requires SSL certificate and key, HSTS enforced)

### Security Configuration

**Session Management**: Session timeout and Redis-based session storage configuration
**Rate Limiting**: API request limiting
**CORS Configuration**: Allowed origins, methods, and credentials

### Halfstack Configuration

**Recommended**: Use the `./scripts/install-dev.sh` script for development environment setup.

#### Starting Development Environment
```bash
# Setup development environment via script (recommended)
./scripts/install-dev.sh

# Start Webserver
./backend.ai web start-server
```

#### Web UI Access
- Web browser: http://localhost:8090
- Default login: admin@lablup.com / wJalrXUt

## Template Rendering

Webserver uses Jinja2 for server-side rendering to serve login pages and more.

## Metrics and Monitoring

### Prometheus Metrics

The Webserver component exposes Prometheus metrics at the `/metrics` endpoint for monitoring web UI and API proxy performance.

#### API Metrics

Metrics related to web UI and authentication HTTP request processing.

**`backendai_api_request_count`** (Counter)
- **Description**: Total number of HTTP requests received by the Webserver
- **Labels**:
  - `method`: HTTP method (GET, POST, PUT, DELETE, PATCH)
  - `endpoint`: Request endpoint path (e.g., "/", "/api/auth/login")
  - `domain`: Error domain (empty if successful)
  - `operation`: Error operation (empty if successful)
  - `error_detail`: Error details (empty if successful)
  - `status_code`: HTTP response status code (200, 400, 500, etc.)
- Track session-based request signing (JWT/HMAC) and Manager proxy requests

**`backendai_api_request_duration_sec`** (Histogram)
- **Description**: HTTP request processing time in seconds
- **Labels**: Same as `backendai_api_request_count`
- **Buckets**: [0.001, 0.01, 0.1, 0.5, 1, 2, 5, 10, 30] seconds
- Measure web UI response time and proxy performance

### Prometheus Query Examples

The following examples demonstrate common Prometheus queries for Webserver metrics. Note that Counter metrics use the `_total` suffix and Histogram metrics use `_bucket`, `_sum`, `_count` suffixes in actual queries.

**Important Notes:**
- When using `increase()` or `rate()` functions, the time range must be at least 2-4x longer than your Prometheus scrape interval to get reliable data. If the time range is too short, metrics may not appear or show incomplete data.
- Default Prometheus scrape interval is typically 15s-30s
- **Time range selection trade-offs**:
  - Shorter ranges (e.g., `[1m]`): Detect changes faster with more granular data, but more sensitive to noise and short-term fluctuations
  - Longer ranges (e.g., `[5m]`): Smoother graphs with reduced noise, better for identifying trends, but slower to detect sudden changes
  - For real-time alerting: Use shorter ranges like `[1m]` or `[2m]`
  - For dashboards and trend analysis: Use longer ranges like `[5m]` or `[10m]`

#### Web Request Monitoring

**Web Request Rate by Endpoint**

Monitor web request rate by endpoint. This shows how frequently users access different web pages and APIs. Use this to understand web traffic patterns and popular features.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups"}[1m])) by (method, endpoint, status_code)
```

**Failed Web Requests (4xx and 5xx)**

Track failed web requests (4xx and 5xx errors). This helps identify user errors and server issues.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", status_code=~"[45].."}[5m])) by (endpoint, status_code)
```

**Authentication Failures**

Monitor authentication failures (login errors). This can indicate brute force attempts or user issues.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", endpoint="/api/auth/login", status_code!="200"}[5m]))
```

#### Web Request Latency

**P95 Web Request Latency**

Calculate P95 web request latency by endpoint. This shows response times experienced by users. Use this to identify slow pages and optimize user experience.

```promql
histogram_quantile(0.95,
  sum(rate(backendai_api_request_duration_sec_bucket{service_group="$service_groups"}[5m])) by (le, endpoint)
)
```

**Average Request Duration**

Calculate average request duration per endpoint. This provides a simple overview of page load times.

```promql
sum(rate(backendai_api_request_duration_sec_sum{service_group="$service_groups"}[5m])) by (endpoint)
/
sum(rate(backendai_api_request_duration_sec_count{service_group="$service_groups"}[5m])) by (endpoint)
```

**Slow Requests (> 1 second)**

Monitor slow requests (> 1 second). This identifies performance issues affecting user experience.

```promql
sum(rate(backendai_api_request_duration_sec_bucket{service_group="$service_groups", le="1.0"}[5m])) by (endpoint)
```

#### Session Management

**Login Request Rate**

Monitor login request rate. This shows how frequently users are logging in.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", endpoint="/api/auth/login"}[5m]))
```

**Successful Logins**

Track successful logins. This helps monitor authentication success rate and detect issues.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", endpoint="/api/auth/login", status_code="200"}[5m])) by (status_code)
```

**Failed Logins**

Track failed logins. This helps identify authentication problems.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", endpoint="/api/auth/login", status_code!="200"}[5m])) by (status_code)
```

**Logout Request Rate**

Monitor logout request rate. This shows active session management patterns.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", endpoint="/api/auth/logout"}[5m]))
```

#### Proxy Performance

**Manager API Proxy Request Rate**

Monitor Manager API proxy request rate. This shows how much traffic is being proxied to the Manager.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", endpoint=~"/api/.*"}[5m])) by (endpoint)
```

**P95 Proxy Request Duration**

Track proxy request duration. This measures the overhead of request signing and proxying.

```promql
histogram_quantile(0.95,
  sum(rate(backendai_api_request_duration_sec_bucket{service_group="$service_groups", endpoint=~"/api/.*"}[5m])) by (le, endpoint)
)
```

**Proxy Errors**

Monitor proxy errors. This identifies issues with request signing or Manager communication.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", endpoint=~"/api/.*", status_code=~"5.."}[5m])) by (endpoint, error_detail)
```

#### Static Assets

**Static Asset Request Rate**

Monitor static asset request rate. This shows how frequently UI assets (CSS, JS, images) are being served.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", endpoint=~"/static/.*"}[5m])) by (endpoint)
```

**Static Asset 404 Errors**

Track static asset 404 errors. This identifies missing or broken asset references.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", endpoint=~"/static/.*", status_code="404"}[5m])) by (endpoint)
```

### Logs
- Session creation/expiration events
- Request signing and proxy events
- Proxied request tracking
- Security violations

## Development

See [README.md](./README.md) for development setup instructions.

## Related Documentation

- [Manager Component](../manager/README.md) - API Gateway
- [Overall Architecture](../README.md) - System-wide architecture
