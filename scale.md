# Scale Services 동작 분석

## 개요

`scale_services()` 메서드는 추론(inference) 서비스의 자동 스케일링을 담당합니다. Model Serving 엔드포인트의 레플리카 수를 동적으로 조정하여 부하에 따라 세션을 생성하거나 제거합니다.

## 주요 구성 요소

### 1. Endpoint
- Model Serving을 위한 서비스 엔드포인트
- `replicas`: 목표 레플리카 수
- `lifecycle_stage`: 엔드포인트 생명주기 상태
- `retries`: 스케일링 재시도 횟수

### 2. Routing
- 엔드포인트와 실제 세션을 연결하는 라우팅 정보
- `status`: HEALTHY, UNHEALTHY, PROVISIONING 등의 상태
- 각 라우팅은 하나의 세션과 매핑됨

### 3. AutoScaling Rules
- 엔드포인트별 자동 스케일링 규칙
- 메트릭 소스: KERNEL, INFERENCE_FRAMEWORK
- 비교 연산자와 임계값 설정

## 동작 흐름

### 1. 자동 스케일링 규칙 적용
```python
await execute_with_retry(lambda: self.schedule_repository.autoscale_endpoints())
```
- 설정된 오토스케일링 규칙에 따라 엔드포인트의 `replicas` 값 업데이트
- 메트릭 기반으로 스케일 업/다운 결정

### 2. 좀비 라우트 정리
```python
rowcount = await self.schedule_repository.clean_zombie_routes()
```
- 세션은 종료되었지만 라우팅은 남아있는 경우 정리

### 3. 스케일링 대상 결정

#### 엔드포인트 종료 처리
```python
if (endpoint.lifecycle_stage == EndpointLifecycle.DESTROYING 
    and len(active_routings) == 0):
    endpoints_to_mark_terminated.add(endpoint)
```
- DESTROYING 상태이고 활성 라우팅이 없으면 종료 대상으로 마킹

#### 스케일 다운 (축소)
```python
if len(active_routings) > replicas:
    destroy_count = len(active_routings) - replicas
    routes_to_destroy += sorted(
        [route for route in active_routings 
         if route.status in endpoint.terminatable_route_statuses],
        key=lambda r: r.status == RouteStatus.UNHEALTHY
    )[:destroy_count]
```
- 현재 활성 라우팅 수가 목표 레플리카 수보다 많은 경우
- UNHEALTHY 상태의 라우팅을 우선적으로 제거 대상으로 선택

#### 스케일 업 (확장)
```python
elif len(active_routings) < replicas:
    if endpoint.retries > SERVICE_MAX_RETRIES:
        continue
    create_count = replicas - len(active_routings)
    endpoints_to_expand[endpoint] = create_count
```
- 현재 활성 라우팅 수가 목표 레플리카 수보다 적은 경우
- 재시도 횟수가 한계를 초과하지 않은 경우만 확장

### 4. 스케일 다운 실행

```python
for session in target_sessions_to_destroy:
    try:
        await self.registry.destroy_session(
            session,
            forced=True,
            reason=KernelLifecycleEventReason.SERVICE_SCALED_DOWN,
        )
    except (GenericForbidden, SessionNotFound):
        already_destroyed_sessions.append(session.id)
```
- 제거 대상 라우팅에 연결된 세션들을 강제 종료
- 이미 종료된 세션은 별도로 추적

### 5. 스케일 업 실행

```python
for endpoint, expand_count in endpoints_to_expand.items():
    endpoint_create_data.append((endpoint, expand_count))
created_routes = await self.schedule_repository.create_routing_rows(endpoint_create_data)

for route_id in created_routes:
    await self.event_producer.anycast_event(RouteCreatedAnycastEvent(route_id))
```
- 필요한 수만큼 새로운 라우팅 생성
- `RouteCreatedAnycastEvent` 이벤트 발생
- 이 이벤트를 받은 다른 컴포넌트가 실제 세션 생성

### 6. 정리 작업

```python
await self.schedule_repository.destroy_terminated_endpoints_and_routes(
    endpoints_to_mark_terminated, already_destroyed_sessions
)

await self.schedule_repository.delete_appproxy_endpoints_readonly(
    endpoints_to_mark_terminated, self.registry
)
```
- 종료된 엔드포인트와 라우팅 정보 DB에서 삭제
- AppProxy의 읽기 전용 엔드포인트 정보도 삭제

## 주요 특징

### 1. 이벤트 기반 세션 생성
- 스케일 업 시 직접 세션을 생성하지 않고 `RouteCreatedAnycastEvent` 발생
- 다른 컴포넌트가 이벤트를 받아 실제 세션 생성 수행
- 비동기적이고 느슨하게 결합된 아키텍처

### 2. 우선순위 기반 제거
- UNHEALTHY 상태의 라우팅을 우선적으로 제거
- 건강한 세션은 가능한 유지

### 3. 재시도 제한
- `SERVICE_MAX_RETRIES`를 초과한 엔드포인트는 더 이상 확장하지 않음
- 무한 재시도 방지

### 4. 트랜잭션 분리
- 자동 스케일링 규칙 적용과 실제 스케일링 작업이 분리됨
- 각 단계별로 독립적인 실패 처리 가능

## 상태 흐름

### 엔드포인트 생명주기
```
CREATED → READY → DESTROYING → TERMINATED
```

### 라우팅 상태
```
PROVISIONING → HEALTHY ↔ UNHEALTHY → (제거)
```

## 지표 수집

```python
await self._update_scheduler_mark(
    ScheduleType.SCALE_SERVICES,
    {
        "down": dump_json_str([str(s.id) for s in target_sessions_to_destroy]),
        "up": dump_json_str([str(e.id) for e in endpoints_to_expand.keys()]),
        "finish_time": datetime.now(tzutc()).isoformat(),
    },
)
```
- 스케일 업/다운된 세션과 엔드포인트 ID 기록
- 실행 시간 추적

## 잠재적 문제점

1. **세션 종료 대기**
   - TODO 주석: "Update logic to not to wait for sessions to actually terminate"
   - 현재는 세션이 실제로 종료될 때까지 대기

2. **스케일 업 실패 처리**
   - 라우팅은 생성했지만 세션 생성이 실패하는 경우
   - 다음 스케일링 주기에서 감지 및 재시도

3. **동시성 이슈**
   - 여러 매니저가 동시에 스케일링을 수행할 경우
   - 분산 락이 필요할 수 있음