# Backend.AI webserver

## Purpose

The webserver provides a web-based user interface, maintains user sessions, and proxies requests to the manager API gateway. It signs requests with the user's access key and secret key: JWT (JSON Web Token) for GraphQL and HMAC (Hash-based Message Authentication Code) for the REST API. The manager handles login processing and authentication.

## Key Responsibilities

### 1. WebUI Hosting
- Serve static WebUI assets (HTML, CSS, JavaScript)
- Provide template rendering for server-side pages
- Handle WebUI routing and navigation
- Provide a responsive web interface

### 2. Session Management
- Maintain web sessions (stored in Valkey)
- Manage the user's access key and secret key stored in sessions
- Handle session timeouts
- **Note**: the manager handles login processing and authentication

### 3. Request Signing and Proxying
- Sign requests with the user's access key and secret key
  - GraphQL requests: JWT signature
  - REST API requests: HMAC signature
- Forward signed API requests to the manager
- Stream API responses
- Support WebSocket proxying

### 4. Security
- CORS (Cross-Origin Resource Sharing) handling
- User input sanitization
- Rate limiting

## Entry Points

The webserver has one entry point that receives and processes user requests.

### 1. REST API (WebUI and Proxy)

**Framework**: aiohttp (async HTTP server)

**Port**: 8080 (default)

**Key Features**:
- Session-based authentication (Valkey)
- Request signing and proxying to the manager API (JWT/HMAC)

**Processing Flow**:

#### Login Flow
```
Browser → POST /auth/login → Webserver → Manager API (authenticate)
                                    ↓
                              Session created in Valkey
                                    ↓
                          Session cookie sent to Browser
```

#### API Request Proxy Flow
```
Browser → API Request + Session Cookie → Webserver
                                            ↓
                                 Retrieve access/secret key from Valkey session
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
│  - Session management (Valkey)  │
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
│   Session Manager (Valkey)          │  ← Session storage
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
- **Session ID**: unique identifier stored in cookies
- **User ID**: associated user in the manager
- **Access key**: user's API access key
- **Created/expires**: session timestamps
- **Data**: additional session data (preferences and so on)

Session Lifecycle:
1. The user logs in through the manager API
2. The manager returns the access key and secret key
3. The webserver creates a session in Valkey and stores the access key and secret key
4. The webserver sends a session cookie to the browser
5. Subsequent requests include the session cookie
6. The webserver retrieves the access key and secret key from the session and signs requests (GraphQL: JWT, REST API: HMAC)
7. The webserver proxies signed requests to the manager
8. The session expires after the timeout or logout

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
6. Webserver creates session in Valkey and stores keys
   ↓
7. Session cookie is sent to browser
   ↓
8. User is redirected to main page
```

### Request Proxying

Session-based requests are proxied to the manager:

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
- `Authorization`: HMAC signature (REST API requests, based on the access key and secret key)
- `X-BackendAI-Version`: API version
- `X-Forwarded-For`: proxy chain

### Session Storage (Valkey)

Session data is stored in Valkey:
- **Key**: `websession:{session_id}`
- **Value**: JSON-encoded session data
- **TTL**: session timeout (for example, 1 hour)

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
- Set the appropriate CORS headers
- Support preflight OPTIONS requests
- Restrict allowed methods and headers

### Rate Limiting
Rate limiting prevents brute force attacks:
- **Limit**: limited number of requests per access key
- **Response**: HTTP 429 Too Many Requests
- **Tracking**: Valkey-based counter per access key

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
- Valkey connection information

**Security Settings**:
- Session timeout and secret
- Rate limiting configuration
- CORS configuration

## Infrastructure Dependencies

### Required Infrastructure

#### Valkey (Session Storage)
- **Purpose**:
  - Store web session data
  - Validate session cookies
  - Manage session timeouts
- **Halfstack Port**: 8111 (host) → 6379 (container)
- **Key Patterns**:
  - `websession:{session_id}` - Web session data

#### Manager API Connection
- **Purpose**:
  - Forward login requests and receive the access key and secret key
  - Proxy JWT (GraphQL) or HMAC (REST API) signed requests
  - Retrieve user information
- **Protocol**: HTTP/HTTPS
- **Halfstack Port**: 8091 (manager)
- **Note**: the manager handles authentication; the webserver adds signatures

#### etcd (Global Configuration)
- **Purpose**:
  - Retrieve global configuration
  - Auto-discover the manager address
- **Halfstack Port**: 8121 (host) → 2379 (container)

### Optional Infrastructure (Observability)

#### Prometheus (Metrics Collection)
- **Purpose**:
  - Session management metrics
  - Request processing time
  - Proxy error tracking
- **Exposed Endpoint**: `http://localhost:8090/metrics`
- **Key Metrics**:
  - `backendai_api_request_count`: total API requests
  - `backendai_api_request_duration_sec`: request processing time

#### Loki (Log Aggregation)
- **Purpose**:
  - Session creation/termination events
  - Request signing and proxy events
  - Security violation events
  - Proxied request tracking
- **Log Labels**:
  - `user_id`: user identifier
  - `event`: event type (session_create, proxy_request and so on)
  - `status`: success or failure

### SSL/TLS Configuration

**Development Environment**: HTTP mode (port 8090)
**Production Environment**: HTTPS mode (requires an SSL certificate and key, and enforces HSTS (HTTP Strict Transport Security))

### Security Configuration

**Session Management**: Session timeout and Valkey-based session storage configuration
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

#### WebUI Access
- Web browser: http://localhost:8090
- Default login: admin@lablup.com / wJalrXUt

## Template Rendering

The webserver uses Jinja2 for server-side rendering to serve login pages and other pages.

## Metrics and Monitoring

### Prometheus Metrics

The webserver component exposes Prometheus metrics at the `/metrics` endpoint for monitoring WebUI and API proxy performance.

#### API Metrics

Metrics related to WebUI and authentication HTTP request processing.

**`backendai_api_request_count`** (Counter)
- **Description**: total number of HTTP requests received by the webserver
- **Labels**:
  - `method`: HTTP method (GET, POST, PUT, DELETE, PATCH)
  - `endpoint`: request endpoint path (for example, "/", "/api/auth/login")
  - `domain`: error domain (empty if successful)
  - `operation`: error operation (empty if successful)
  - `error_detail`: error details (empty if successful)
  - `status_code`: HTTP response status code (200, 400, 500 and so on)
- Track session-based request signing (JWT/HMAC) and manager proxy requests

**`backendai_api_request_duration_sec`** (Histogram)
- **Description**: HTTP request processing time in seconds
- **Labels**: same as `backendai_api_request_count`
- **Buckets**: [0.001, 0.01, 0.1, 0.5, 1, 2, 5, 10, 30] seconds
- Measure WebUI response time and proxy performance

### Prometheus Query Examples

The following examples show common Prometheus queries for webserver metrics. Counter metrics use the `_total` suffix, and Histogram metrics use the `_bucket`, `_sum` and `_count` suffixes in actual queries.

**Important notes:**
- When using `increase()` or `rate()`, the time range must be at least 2-4x longer than the Prometheus scrape interval to get reliable data. If the time range is too short, metrics may not appear or may show incomplete data.
- The default Prometheus scrape interval is typically 15s-30s.
- **Time range selection trade-offs**:
  - Shorter ranges (for example, `[1m]`): detect changes faster with more granular data, but are more sensitive to noise and short-term fluctuations
  - Longer ranges (for example, `[5m]`): smoother graphs with reduced noise, better for identifying trends, but slower to detect sudden changes
  - For real-time alerting: use shorter ranges such as `[1m]` or `[2m]`
  - For dashboards and trend analysis: use longer ranges such as `[5m]` or `[10m]`

#### Web Request Monitoring

**Web Request Rate by Endpoint**

Monitor the web request rate by endpoint. It shows how frequently users access different pages and APIs. It helps understand traffic patterns and popular features.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups"}[1m])) by (method, endpoint, status_code)
```

**Failed Web Requests (4xx and 5xx)**

Track failed web requests (4xx and 5xx errors). It helps identify user errors and server issues.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", status_code=~"[45].."}[5m])) by (endpoint, status_code)
```

**Authentication Failures**

Monitor authentication failures (login errors). They can indicate brute force attempts or user issues.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", endpoint="/api/auth/login", status_code!="200"}[5m]))
```

#### Web Request Latency

**P95 Web Request Latency**

Calculate the 95th percentile (P95) web request latency by endpoint. It shows the response times experienced by users. It helps identify slow pages to optimize the user experience.

```promql
histogram_quantile(0.95,
  sum(rate(backendai_api_request_duration_sec_bucket{service_group="$service_groups"}[5m])) by (le, endpoint)
)
```

**Average Request Duration**

Calculate the average request duration per endpoint. It gives an overview of page load times.

```promql
sum(rate(backendai_api_request_duration_sec_sum{service_group="$service_groups"}[5m])) by (endpoint)
/
sum(rate(backendai_api_request_duration_sec_count{service_group="$service_groups"}[5m])) by (endpoint)
```

**Slow Requests (> 1 second)**

Monitor slow requests (> 1 second). It identifies performance issues that affect the user experience.

```promql
sum(rate(backendai_api_request_duration_sec_bucket{service_group="$service_groups", le="1.0"}[5m])) by (endpoint)
```

#### Session Management

**Login Request Rate**

Monitor the login request rate. It shows how frequently users log in.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", endpoint="/api/auth/login"}[5m]))
```

**Successful Logins**

Track successful logins. It shows the authentication success rate and detects issues.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", endpoint="/api/auth/login", status_code="200"}[5m])) by (status_code)
```

**Failed Logins**

Track failed logins. It helps identify authentication problems.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", endpoint="/api/auth/login", status_code!="200"}[5m])) by (status_code)
```

**Logout Request Rate**

Monitor the logout request rate. It shows active session management patterns.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", endpoint="/api/auth/logout"}[5m]))
```

#### Proxy Performance

**Manager API Proxy Request Rate**

Monitor the manager API proxy request rate. It shows how much traffic is proxied to the manager.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", endpoint=~"/api/.*"}[5m])) by (endpoint)
```

**P95 Proxy Request Duration**

Track the proxy request duration. It measures the overhead of request signing and proxying.

```promql
histogram_quantile(0.95,
  sum(rate(backendai_api_request_duration_sec_bucket{service_group="$service_groups", endpoint=~"/api/.*"}[5m])) by (le, endpoint)
)
```

**Proxy Errors**

Monitor proxy errors. It identifies issues with request signing or manager communication.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", endpoint=~"/api/.*", status_code=~"5.."}[5m])) by (endpoint, error_detail)
```

#### Static Assets

**Static Asset Request Rate**

Monitor the static asset request rate. It shows how frequently the webserver serves UI assets (CSS, JS and images).

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", endpoint=~"/static/.*"}[5m])) by (endpoint)
```

**Static Asset 404 Errors**

Track static asset 404 errors. It identifies missing or broken asset references.

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

## Related documents

- [Manager component](../manager/README.md) - API gateway
- [Overall architecture](../README.md) - system-wide architecture
