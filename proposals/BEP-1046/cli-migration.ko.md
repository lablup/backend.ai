# CLI 설정 마이그레이션 세부 사항

> 상위 문서: [BEP-1046](../BEP-1046-unified-service-discovery.md)

## CLI 사용법

기존 설정에서 새 `[service-discovery.endpoints]` section 을 자동 생성하는 CLI 도구를 제공한다.

```bash
# Usage — structured as subcommands under config migrate
# Extensible structure for future config migrations
$ backend.ai ag config migrate service-discovery -i agent.toml
$ backend.ai mgr config migrate service-discovery -i manager.toml
$ backend.ai storage config migrate service-discovery -i storage-proxy.toml

# Options
  -i, --input PATH     Existing config file path
  -o, --output PATH    Output file (stdout if omitted)
  --append             Append directly to existing file
  --dry-run            Preview without changes (default)
  --force              Execute without confirmation
```

## 매핑 규칙

기존 설정 field 를 `(role, scope, protocol)` tuple 로 매핑하는 컴포넌트별 규칙을 코드에 정의한다.

```python
# Agent mapping rules
AGENT_MAPPING_RULES = [
    MappingRule(source="agent.advertised-rpc-addr",
                fallback="agent.rpc-listen-addr",
                role="rpc", scope="cluster", protocol="zmq"),
    MappingRule(source="agent.service.announce-internal-addr",
                fallback="agent.service.service-addr",
                role="metrics", scope="cluster", protocol="http"),
    MappingRule(source="agent.service.announce-internal-addr",
                role="metrics", scope="container", protocol="http"),
]

# Storage Proxy mapping rules
STORAGE_MAPPING_RULES = [
    MappingRule(source="manager.announce-addr",
                fallback="manager.service-addr",
                role="api", scope="cluster", protocol="http"),
    MappingRule(source="client.service-addr",
                role="client-api", scope="cluster", protocol="http"),
    MappingRule(source="manager.announce-internal-addr",
                role="client-api", scope="container", protocol="http"),
]

# Manager mapping rules
MANAGER_MAPPING_RULES = [
    MappingRule(source="manager.service-addr",
                role="api", scope="cluster", protocol="http"),
]
```

## 출력 예시

```
$ backend.ai ag config migrate service-discovery -i agent.toml

# Detected existing config fields:
#   agent.rpc-listen-addr = 0.0.0.0:6001
#   agent.advertised-rpc-addr = 10.0.1.5:6001
#   agent.service.service-addr = 0.0.0.0:6002
#   agent.service.announce-internal-addr = host.docker.internal:6002
#
# Generated [service-discovery] section:

[service-discovery]

[[service-discovery.endpoints]]
role = "rpc"
scope = "cluster"
address = "10.0.1.5"
port = 6001
protocol = "zmq"

[[service-discovery.endpoints]]
role = "metrics"
scope = "cluster"
address = "host.docker.internal"
port = 6002
protocol = "http"

[[service-discovery.endpoints]]
role = "metrics"
scope = "container"
address = "host.docker.internal"
port = 6002
protocol = "http"
```
