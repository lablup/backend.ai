# 스토리지 성능 지표 캐싱과 관측성

## 관련 이슈

- JIRA: BA-4012 (Epic)
  - BA-4013: Valkey 캐시 계층
  - BA-4014: 백그라운드 갱신과 관측성
  - BA-4015: Prometheus 지표 노출
  - BA-4016: API 수정

## 동기

현재 `/volume/performance-metric` API 는 요청마다 외부 스토리지 백엔드 API(NetApp, VAST, PureStorage, GPFS 등)를 직접 호출한다. 그래서 다음 문제가 있다.

1. **사용자 경험 저하**: 외부 API 가 느리거나 불안정하면 API 응답이 지연되거나 실패해 사용자 경험이 나빠진다
2. **외부 시스템 지연 전파**: 외부 시스템이 느릴 때마다 우리 API 호출도 지연된다
3. **관측성 부족**: 스토리지 시스템을 모니터링하기 어렵다
4. **이력 없음**: 현재 값만 조회할 수 있고 시계열 데이터가 없다

## 현재 설계

현재 `get_performance_metric` API 흐름:

```
Client Request
    ↓
API Handler (manager.py:580-603)
    ↓
volume.get_performance_metric()  # Direct external API call
    ↓
Response
```

volume 구현마다 외부 API 를 직접 호출한다.

- PureStorage: `purity_client.get_nfs_metric()`
- VAST: `api_client.get_cluster_info()`
- NetApp: `netapp_client.get_volume_by_id()`

## 제안 설계

### 아키텍처 개요

인메모리 캐시 없이 Valkey 캐시만 사용한다. 캐시가 없거나 Valkey 가 실패하면 외부 API 를 직접 호출한다.

```
┌─────────────────────────────────────────────────────────────┐
│                VolumeStatsObserver                           │
│  (Periodic background task - 10 second interval)            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   Volume 1  │    │   Volume 2  │    │   Volume N  │     │
│  │ get_perf_*  │    │ get_perf_*  │    │ get_perf_*  │     │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘     │
│         │                  │                  │             │
│         ▼                  ▼                  ▼             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Redis Cache (TTL: 30s)                  │   │
│  │         storage:perf_metric:{volume_name}           │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                   │
│         ├──────────────────┐                               │
│         ▼                  ▼                               │
│  ┌───────────┐      ┌───────────┐                          │
│  │Prometheus │      │Prometheus │                          │
│  │  Gauges   │      │ Counters  │                          │
│  │ (BA-4015) │      │ (BA-4014) │                          │
│  └───────────┘      └───────────┘                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   API Handler   │
                    │   (BA-4016)     │
                    │ Redis lookup →  │
                    │ fallback to API │
                    └─────────────────┘
```

### 파일 구조

```
src/ai/backend/storage/
├── volumes/
│   ├── stats/
│   │   ├── __init__.py
│   │   ├── types.py           # CachedFSPerfMetric, VolumeStatsObserverOptions
│   │   ├── observer.py        # VolumeStatsObserver (periodic observation)
│   │   └── state.py           # VolumeStatsState (cache lookup + fallback)
│   └── ...
└── ...
```

### 핵심 타입 정의(types.py)

```python
@dataclass
class VolumeStatsObserverOptions:
    """Volume stats observer configuration."""
    observe_interval: float = 10.0   # Observation interval (seconds)
    timeout_per_volume: float = 5.0  # Per-volume timeout (seconds)
    cache_ttl: float = 30.0          # Redis cache TTL (seconds)


@dataclass(frozen=True)
class CachedFSPerfMetric:
    """Cached performance metric with metadata."""
    volume_name: str
    metric: FSPerfMetric
    observed_at: datetime  # Actual observation timestamp
```

### VolumeStatsObserver(observer.py)

AbstractObserver 를 참조해 주기 관측을 처리한다.

```python
class VolumeStatsObserver:
    """Periodically observes performance metrics for all active volumes and stores in Redis."""

    @property
    def name(self) -> str:
        return "volume_stats"

    async def observe(self) -> None:
        """Observe metrics for all volumes and store in Redis."""
        ...

    def observe_interval(self) -> float:
        return self._options.observe_interval

    @classmethod
    def timeout(cls) -> float | None:
        return 30.0
```

### VolumeStatsState(state.py)

캐시 조회와 외부 API fallback 을 처리한다.

```python
class VolumeStatsState:
    """Volume stats state lookup. Redis cache first, then external API call."""

    async def get_performance_metric(
        self,
        volume_name: str,
    ) -> CachedFSPerfMetric:
        """
        Get performance metric.
        1. Try Redis cache lookup
        2. On cache miss or Redis failure, call external API directly
        3. Store external API result in Redis (suppress failures)
        """
        ...
```

### Prometheus 운영 지표(observer.py 내부)

BA-4014 에서 구현할 운영 지표:

```python
# Counter: Observation attempt count (success/failure)
# name: backendai_storage_volume_stats_observe_total
# labels: volume, status (success|failure)

# Histogram: Observation duration
# name: backendai_storage_volume_stats_observe_duration_seconds
# labels: volume
# buckets: [0.1, 0.5, 1, 2, 5, 10, 30]
```

### 설정(config/unified.py)

`StorageProxyConfig` 에 추가한다.

```python
volume_stats_observe_interval: float = 10.0  # Observation interval (seconds)
volume_stats_observe_timeout: float = 5.0    # Per-volume timeout (seconds)
volume_stats_cache_ttl: float = 30.0         # Redis cache TTL (seconds)
```

## 에러 처리 전략

1. **volume 별 실패 격리**: volume 마다 별도 Valkey key 를 두므로 실패가 격리된다
2. **TTL 기반 만료**: `is_stale` field 대신 Valkey TTL 로 캐시 유효성을 관리한다
3. **timeout**: volume 당 5초 timeout 이 전체 loop 의 차단을 방지한다
4. **loop 연속성**: Observer loop 는 독립적으로 실행되고 예외가 나도 계속된다

## 마이그레이션, 호환성

### 하위 호환성

- 기존 `/volume/performance-metric` API 응답 형식을 유지한다
- `observed_at` field 만 추가한다(BA-4016)

### 호환성을 깨는 변경

없다.

## 구현 계획

구현 순서(의존성 기준):

### 1단계: BA-4014 주기 관측 task

1. `volumes/stats/types.py` 생성
   - `VolumeStatsObserverOptions`
   - `CachedFSPerfMetric`

2. `volumes/stats/observer.py` 생성
   - `VolumeStatsObserver` class
   - Prometheus Counter, Histogram

3. `volumes/stats/state.py` 생성
   - `VolumeStatsState` class(캐시 조회와 fallback)

4. `config/unified.py` 수정
   - 설정 field 추가

5. `context.py` 수정
   - `RootContext` 에 observer, state field 추가

6. `server.py` 수정
   - Observer 초기화와 수명 주기 관리

### 2단계: BA-4015 Prometheus 성능 지표

Observer 가 관측한 데이터를 Prometheus Gauge 로 노출한다.

- `backendai_storage_volume_iops_read{volume}`
- `backendai_storage_volume_iops_write{volume}`
- `backendai_storage_volume_throughput_bytes_read{volume}`
- `backendai_storage_volume_throughput_bytes_write{volume}`
- `backendai_storage_volume_latency_usec_read{volume}`
- `backendai_storage_volume_latency_usec_write{volume}`
- `backendai_storage_volume_metric_last_updated_timestamp{volume}`

### 3단계: BA-4013 Valkey 캐시 계층

Valkey 캐시는 1단계에서 이미 구현한다. 추가 작업이 거의 없거나 필요 없다.

- 캐시 key: `storage:perf_metric:{volume_name}`
- TTL: 30초

### 4단계: BA-4016 API 수정

API 는 VolumeStatsState 를 통해 데이터를 반환한다.

- Valkey 캐시 hit: 캐시 데이터와 `observed_at` 을 반환한다
- Valkey 캐시 miss 또는 실패: 외부 API 를 직접 호출한다

## 열린 질문

1. **Leader election**: storage-proxy 인스턴스가 여러 개면 각 인스턴스가 독립적으로 관측한다. Leader election 은 이후 개선으로 남긴다.

## 참고

- [AbstractObserver](../src/ai/backend/common/observer/types.py) - Observer 패턴 참조
- [HealthProbe 구현](../src/ai/backend/common/health_checker/probe.py) - 주기 task 패턴 참조
