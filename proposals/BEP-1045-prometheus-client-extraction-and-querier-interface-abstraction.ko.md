# Prometheus client 추출과 querier 인터페이스 추상화

## 동기

`ContainerUtilizationMetricService` 는 이전에 business logic 과 Prometheus 전용 질의 생성 로직을 긴밀하게 결합해 담고 있었다. 그래서 다음이 어려웠다.

1. **다른 metric 타입으로 확장**: 새 metric 원천(예: agent metric, node metric)을 추가하려면 질의 생성 로직을 중복해야 했다
2. **격리된 테스트**: service 가 HTTP 통신, 질의 문자열 생성, metric 타입 감지를 한데 섞고 있었다
3. **단일 책임 유지**: 한 클래스가 너무 많은 관심사를 처리했다

리팩터링의 목표는 다음과 같다.
- metric 식별(무엇을 질의하는가)과 질의 실행(어떻게 질의하는가)을 분리한다
- PromQL 패턴을 preset 으로 정의하는 template 기반 질의 시스템을 생성한다
- Prometheus client 가 인터페이스를 구현한 어떤 querier 와도 동작하게 한다

## 현재 설계

main branch 에는 **전용 Prometheus client 가 없다**. 모든 로직이 `ContainerUtilizationMetricService` 에 있다.

```
ContainerUtilizationMetricService
    ├── _query_label_values()                    # Direct aiohttp call
    ├── _get_query_string()                      # Query building orchestration
    ├── _parse_query_string_by_metric_spec()     # PromQL string generation
    ├── _get_metric_type()                       # Metric type detection
    ├── _get_label_values_for_query()            # Label selector building
    ├── _get_sum_by_for_query()                  # Group by clause building
    └── query_metric()                           # Direct aiohttp call with inline error handling
```

**문제:**
1. **관심사 분리 없음**: HTTP 통신, 질의 생성, business logic 이 한 service 에 모두 섞여 있다
2. **직접 aiohttp 사용**: 요청마다 새 `ClientSession` 을 생성하고 connection pooling 이 없다
3. **재사용 불가**: Prometheus 접근 로직을 다른 service 와 공유할 수 없다
4. **테스트 어려움**: 질의 생성 로직을 테스트하려면 aiohttp 내부를 mock 으로 대체해야 한다
5. **확장성 없음**: 새 metric 타입(agent, node)을 추가하려면 모든 것을 중복해야 한다

## 제안 설계

### 개요

설계는 관심사를 다음과 같이 분리한다.
- **MetricQuerier**: 질의할 metric 을 정의하는 추상 인터페이스
- **MetricPreset**: PromQL template 과 허용 placeholder 를 정의한다(다른 곳에서 정의)
- **MetricQueryInput**: 사용자가 제공하는 질의 파라미터
- **PrometheusClient**: template 을 렌더링하고 HTTP 요청을 실행한다

### MetricQuerier ABC

`MetricQuerier` 는 질의할 metric 을 정의하는 추상 기본 클래스다. metric 식별을 위한 공통 인터페이스, 즉 이름, label selector, 집계 기준 label 을 제공한다.

```python
# clients/prometheus/types.py

class MetricQuerier(ABC):
    """Abstract interface for metric query specification."""

    @abstractmethod
    def name(self) -> str:
        """Return the Prometheus metric name."""
        ...

    @abstractmethod
    def labels(self) -> dict[str, str]:
        """Return label selectors for filtering."""
        ...

    @abstractmethod
    def group_by_labels(self) -> list[str]:
        """Return labels to group by when aggregating."""
        ...
```

### ContainerMetricQuerier

`ContainerMetricQuerier` 는 container 수준 사용률 metric 의 구체 구현이다.

```python
# clients/prometheus/querier.py

@dataclass(kw_only=True)
class ContainerMetricQuerier(MetricQuerier):
    """Querier for container-level utilization metrics."""

    metric_name: str
    value_type: str
    kernel_id: UUID | None = None
    # ... other optional fields

    @override
    def name(self) -> str:
        return "backendai_container_utilization"

    @override
    def labels(self) -> dict[str, str]:
        # Build label selectors from fields
        ...

    @override
    def group_by_labels(self) -> list[str]:
        # Return labels to group by
        ...
```

### 타입 정의

```python
# clients/prometheus/types.py


@dataclass(frozen=True)
class QueryTimeRange:
    """Time range parameters for Prometheus range queries."""
    start: str
    end: str
    step: str
```

### PrometheusClient

`PrometheusClient` 는 `MetricPreset`, `MetricQuerier`, `window` 파라미터를 받아 질의를 렌더링하고 실행한다. client 는 querier 의 `name()`, `labels()`, `group_by_labels()` 로 preset template 을 채운다.

```python
# clients/prometheus/client.py

class PrometheusClient:

    _client_pool: ClientPool
    _client_key: ClientKey

    async def query_range(
        self,
        preset: MetricPreset,
        querier: MetricQuerier,
        time_range: QueryTimeRange,
        *,
        window: str = "5m",
    ) -> PrometheusQueryRangeResponse:
        """Execute a Prometheus range query."""
        query = self._render_query(preset, querier, window)
        return await self._post("/api/v1/query_range", data={
            "query": query,
            "start": time_range.start,
            "end": time_range.end,
            "step": time_range.step,
        })

    def _render_query(preset: MetricPreset, querier: MetricQuerier, window: str) -> str:
        """Simple template substitution using querier interface."""
        labels_str = ",".join(f'{k}="{v}"' for k, v in querier.labels().items())
        group_by_str = ",".join(querier.group_by_labels())

        return preset.query_template.format(
            metric_name=querier.name(),
            labels=labels_str,
            group_by=group_by_str,
            window=window,
        )
```

**PromQL 렌더링 예시:**

| Preset template | 입력 | 렌더링된 PromQL |
|---|---|---|
| `sum by ({group_by})(rate({metric_name}{{{labels}}}[{window}]))` | `labels={"endpoint": "/auth"}, group_by=["endpoint"], window="1m"` | `sum by (endpoint)(rate(backendai_api_request_count_total{endpoint="/auth"}[1m]))` |
| `{metric_name}{{{labels}}}` | `labels={"value_type": "current"}, group_by=[], window="5m"` | `backendai_container_utilization{value_type="current"}` |

### 단순화한 service 계층

`ContainerUtilizationMetricService` 는 `PrometheusClient` 에 위임하는 얇은 조정 계층이 된다.

```python
# services/metric/container_metric.py

class ContainerUtilizationMetricService:
    """Thin coordination layer - delegates to client."""

    _prometheus_client: PrometheusClient

    async def fetch_metric(self, action: ContainerMetricAction) -> ContainerMetricActionResult:
        querier = ContainerMetricQuerier(
            metric_name=action.metric_name,
            value_type=action.labels.value_type,
            kernel_id=action.labels.kernel_id,
            ...
        )
        time_range = QueryTimeRange(start=action.start, end=action.end, step=action.step)
        # Legacy: preset is hardcoded until MetricPreset system is implemented
        result = await self._prometheus_client.query_range(
            CONTAINER_METRIC_PRESET, querier, time_range, window=self._rate_interval
        )
        # ... transform result
```

## 이관과 호환성

### 하위 호환성

- **내부 API 변경**: 직접 질의 생성 메서드를 service 계층에서 제거한다
- **외부 영향 없음**: `ContainerUtilizationMetricService.fetch_metric()` 시그니처를 유지한다
- **service API 무변경**: 모든 호출자가 변경 없이 계속 동작한다

### 제거하는 타입

다음 타입을 `services/metric/types.py` 에서 제거한다.
- `UtilizationMetricType` enum 은 preset 의 질의 template 으로 대체한다
- `MetricSpecForQuery` dataclass 는 `MetricQuerier` 인터페이스로 대체한다
