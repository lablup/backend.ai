# ROUTER frontend 모드: LLM 인퍼런스 게이트웨이 통합

## 관련 이슈

- JIRA: TBD
- GitHub: [lablup/continuum-router#748](https://github.com/lablup/continuum-router/pull/748)
  (이 제안과 짝을 이루는 worker 쪽 설계 문서:
  `docs/en/architecture/appproxy-worker.md`)

## 동기

Backend.AI 는 세 개념으로 이뤄진 층으로 모델을 서비스한다. 복제본, 리비전, 오토스케일링을 가진 **배포 엔드포인트**(`EndpointRow`)가 있고, 각각 `kernel_host:kernel_port` 로 접근하는 하나 이상의 **복제본 세션**(`RoutingRow`)이 있으며, proxy worker 에서 엔드포인트를 복제본에 묶고 `traffic_ratio` 로 부하를 분산하는 App Proxy **circuit** 이 있다.

지금은 각 엔드포인트를 *자기* frontend slot, 곧 전용 wildcard 서브도메인이나 port 에 게시하고, 엔드포인트별 JWT 인 *배포 토큰*(`EndpointTokenRow`)을 사용한다. 이 모양은 투명하고 단순하지만, cluster 수준 LLM 인퍼런스에 빈틈을 남긴다.

- **단일 표면이 없다.** 배포마다 base URL 이 다르다. 클라이언트가 주소 하나를 가지고 모델을 이름으로 고르는 방식, 모든 OpenAI 호환 SDK 가 기대하는 방식을 사용할 수 없다.
- **모델 추상화가 없다.** 사용자는 *모델* 이 아니라 *배포* 를 참조한다. 두 리비전을 A/B 테스트하거나 한 모델을 여러 자원 그룹에 나눠 서비스하려고, 배포 엔드포인트 여럿이 뒷받침하는 모델 이름 하나를 게시하는 일급 수단이 없다.
- **키 관리가 없다.** 배포 토큰은 배포 하나에 대한 접근을 부여한다. 소비자가 cluster 전체에서 *어떤 모델* 을 보고 사용할 수 있는지 범위를 정하는 API 키 수단이 없다.
- **LLM 을 인식하는 데이터 플레인이 없다.** 기본 worker 는 바이트를 전달한다. 프로토콜 변환(OpenAI ↔ Anthropic ↔ Gemini), fallback chain, 응답 caching, prefix/KV cache 를 인식하는 라우팅에는 인퍼런스 트래픽을 이해하는 L7 router 가 필요하다.

[Continuum Router](https://github.com/lablup/continuum-router)가 바로 그 데이터 플레인을 제공한다. 이 제안은 그것을 새 종류의 App Proxy worker 로 실행하는 Backend.AI 쪽 지원을 추가한다. **ROUTER frontend 모드**에서는 worker 가 자기 단일 엔드포인트에 대한 **바인딩 주소 하나**를 갖고, slot 관리를 모두 건너뛰며, API 키로 검사한 요청의 `model` 이름이 주소 지정 키가 된다. App Proxy coordinator 는 계속 제어 플레인이고, Backend.AI Manager 는 router 가 게시하는 내용을 정의하는 **키, 모델, service mapping** 의 관리 인터페이스를 얻는다.

## 현재 설계

### Frontend 모드와 slot

`FrontendMode`(`src/ai/backend/appproxy/common/types.py`)에 값이 둘 있다.

```python
class FrontendMode(enum.StrEnum):
    WILDCARD_DOMAIN = "wildcard"
    PORT = "port"
```

worker 는 등록할 때 slot 공간(`wildcard_domain` 또는 `port_range`)을 알린다. app proxy coordinator 는 `add_circuit()` 에서 circuit 마다 slot 하나(생성한 서브도메인이나 port)를 할당하고, `Circuit.get_endpoint_url()` 이 그 slot 으로 배포별 URL 을 만든다. `Worker._calculate_available_slots()` 는 wildcard 면 `-1`, port 모드면 범위 크기를 반환한다.

### 배포 토큰

Manager 는 app proxy coordinator 를 통해 엔드포인트별 JWT 를 발급하고(`POST /v2/endpoints/{endpoint_id}/token` → `Circuit.generate_jwt()`, cluster 전체 `jwt_secret` 을 사용하는 HS256), `EndpointTokenRow` 에 저장한다. 기본 worker 는 circuit 마다 bearer 를 검증한다. 이것이 배포 API 의 배포 토큰(`services/deployment/service.py` 의 `create_access_token`)이고, 정확히 배포 하나에 대한 접근을 부여한다.

### app proxy coordinator → worker 전파

두 방식이 있다(`src/ai/backend/appproxy/coordinator/types.py:CircuitManager`).

- **Legacy(aiohttp worker) 모드.** circuit 변경을 Valkey Pub/Sub event 로 브로드캐스트하고 **엔티티별 전체 상태**를 담는다(`AppProxyCircuitCreatedEvent` / `…RouteUpdatedEvent` / `…RemovedEvent`). circuit 생성은 **첫** worker ack 을 최대 15초 기다리고(`initialize_legacy_circuit`, timeout 이면 `E10001` 발생), route 변경과 제거는 fire-and-forget 이다. worker 는 시작할 때 한 번만 circuit snapshot 을 가져온다(`src/ai/backend/appproxy/worker/server.py:worker_registration_ctx`).
- **Traefik 모드.** app proxy coordinator 가 각 circuit 의 전체 원하는 상태를 etcd 에 쓰고(`atomic_replace_prefixes`), leader 로 선출된 `reconcile_traefik_routes` task 가 30초마다 모든 circuit 을 다시 게시하고 고아를 제거한다. 명시적으로 "전파 event 를 놓쳤을 때(coordinator 재시작이나 일시적 Valkey 문제 등) 대비하는 안전망"이다.

이 제안이 재사용할 비대칭성에 주목한다. 프로토콜에는 **app proxy coordinator 가 worker 로 접속하는 경로가 없고**(event 와 pull 뿐), 버전 chain 대신 **엔티티별 전체 상태** payload 로 멱등성을 얻으며, 더 새로운 Traefik 경로는 손실 있는 event 를 **주기적 set-diff 조정**으로 원하는 상태에 맞춰 보정한다.

## 제안 설계

### 용어

이 제안은 기존의 고객에게 보이는 자격 증명 옆에 두 번째 인퍼런스 자격 증명을 추가한다. 혼동을 피하려고 둘의 이름을 다음과 같이 정하고 글 전체에서 일관되게 사용한다.

- **배포 토큰**: *기존* 자격 증명이다. app proxy coordinator 를 통해 발급해 `EndpointTokenRow` 에 저장하는 배포별 JWT 이고(배포 API 의 배포 토큰), **이 제안은 이름도 변경하지 않고 동작도 변경하지 않으며**, WILDCARD/PORT frontend 에서 오늘과 똑같이 동작한다.
- **모델 API 키**: *새* 자격 증명이다. Manager 가 생성하는 불투명한 `sk-…` 형태 key 이고, RBAC 에서 유도한 허용 모델 집합을 가지며, OpenAI 호환 SDK 가 API 키를 기대하는 방식 그대로 ROUTER 모드 worker 에 제시된다.

이름의 근거는 다음과 같다. "access key" 는 의도적으로 피한다. 플랫폼 keypair 의 AK 절반(`access_key`/`secret_key`)을 이미 의미하기 때문이다. "router … key" 는 피한다. 데이터 플레인 구성 요소 이름을 드러내고, 모델 serving 의 기존 route/routing 용어(`RoutingRow`, `route_info`)와 겹치기 때문이다. "모델 API 키"는 범위(모델)를 이름에 담고, 사용자가 SDK 에 붙여 넣는 `sk-…` 문자열을 이미 일컫는 이름과 맞는다. 내부 식별자(`router_api_keys` 테이블, `/v2/routers/*` 경로, event 이름)는 ROUTER frontend 모드를 계속 참조해도 된다. 사용자에게 보이는 표면(GraphQL/CLI/WebUI/문서)만 *모델 API 키* 라는 용어를 사용한다.

### 개요

```text
   Backend.AI Manager ──(key–model–service mappings)──► AppProxy Coordinator
        │  user creates deployments,                        │ persists desired state
        │  defines models & API keys                        │ (PostgreSQL); schedules
        ▼                                                   │ circuits; broadcasts
   deployment endpoints (replica sessions)                  │ events (Redis Pub/Sub)
                                                            ▼
   client ── POST /v1/chat/completions ──► continuum-router worker
             Authorization: Bearer <key>     (frontend_mode = router,
             {"model": "llama-4-chat", …}     one address, no slots)
                                                │
                                                ▼  weighted selection
                                       replica sessions (kernels)
```

worker 에서 두 단계 계층 라우팅을 한다. API 키가 보이는 **모델** 의 범위를 정하고, 모델이 하나 이상의 **배포 엔드포인트** 로 이어지며(각 mapping 은 나뉜 `ratio` 를 가진다), 각 엔드포인트는 circuit 의 `route_info` 로 복제본 세션을 찾고 `ratio × traffic_ratio` 로 가중한다. Manager 는 사용자에게 배포별 URL 대신 **(base URL, 모델 이름, API 키)** 세 값을 제공한다.

### 요청 경로와 책임 분리

LLM 인퍼런스 요청은 mapping 계층 셋을 거쳐 해석되고, stack 의 다른 부분이 각 계층을 맡는다.

```text
API key ──(1: visibility)──► model ──(2: publication)──► endpoint(s) ──(3: replicas)──► replica session
        enforced by the router      defined in the Manager,           maintained by the core
        at request time             delivered via the coordinator     (autoscaling, health checks)
```

1. **key → 모델**(router). router 가 key 를 인증하고 모델 목록과 사용을 key 의 허용 모델 집합으로 제한한다. router 는 구체화된 목록을 *강제* 할 뿐 권한을 스스로 평가하지 않는다.
2. **모델 → 엔드포인트**(App Proxy). 어떤 배포 엔드포인트가 어떤 비율로 한 모델을 서비스하는지를 정하는 게시 mapping 을 app proxy coordinator 에 저장하고 아래에서 설명하는 방식으로 router 에 전달한다.
3. **엔드포인트 → 복제본 세션**(core). 각 엔드포인트의 복제본 집합은 circuit 의 `route_info` 이고, Manager 의 `RoutingRow` 상태에서 공급되어 기존 circuit route 변경 event 로 router 에 흐른다.

계층은 **사용자가 구성하는 계층**과 **시스템이 유지하는 계층**으로 나뉜다.

| Mapping 계층 | 소유자 | 방식 |
|---|---|---|
| 키 생성과 발급 | **사용자** | WebUI / API / CLI 를 통한 명시적 동작이다. Manager 가 모델 API 키를 발급하고 key 소유자와 함께 저장한다. |
| 모델 → 엔드포인트 mapping | **사용자** | WebUI / API / CLI 로 게시를 명시적으로 관리한다. 모델 이름, 뒷받침할 엔드포인트, 분할 비율(A/B 테스트, 자원 그룹 균형)을 고른다. |
| 키 → 모델 가시성 | **시스템** | RBAC 에서 유도한다. Manager 가 key 소유자의 scope(게시된 모델에 대한 도메인과 프로젝트 권한)에서 key 의 허용 모델 집합을 계산하고, 발급 시 더 좁힐 수 있으며, RBAC 부여나 게시가 변경될 때마다 다시 계산해 다시 전파한다. 수동 목록 관리가 없다. |
| 엔드포인트 → 복제본 세션 | **시스템** | 배포 스케일링과 헬스 체크가 계속 갱신한다. `RoutingRow` 변경이 circuit `route_info` 로, 다시 route 변경 event 로 router 에 흐르고 사용자 동작이 없다. |

달리 말하면 사용자는 *무엇을 게시하고 누구에게 key 를 주는지* 를 정하고, 시스템은 *key 가 무엇을 볼 수 있는지* 와 *실제로 무엇이 트래픽을 서비스하는지* 를 시간에 따라 맞게 유지한다. 따라서 app proxy coordinator 와 router 에 전달하는 `allowed_models` 값(각각 제안 설계의 전파 절과 REST API 절 참고)은 Manager 가 RBAC 상태에서 계산한 **materialized view** 다. 사용자의 권한이 변경되면 Manager 가 다시 계산한 집합으로 `PUT /v2/routers/{authority}/api-keys/{key_id}` 를 다시 보내고, 평소 전파 경로가 그것을 적용한다.

### 1. Common: `FrontendMode.ROUTER`

```python
class FrontendMode(enum.StrEnum):
    WILDCARD_DOMAIN = "wildcard"
    PORT = "port"
    ROUTER = "router"  # new
```

`WorkerRequestModel` 이 선택 field 하나를 얻는다.

```python
traffic_port: int | None  # ROUTER mode: advertised data-plane port
                          # (an LB may front the worker); defaults to api_port
```

모드별 등록 검증은 다음과 같다. ROUTER 는 `port_range` 도 `wildcard_domain` 도 필요 없고(둘 다 null 이어야 한다) `traffic_port` 를 받는다. 기존 모드는 변경되지 않는다.

### 2. app proxy coordinator: slot 없는 circuit

- ROUTER worker 에 대해 `Worker._calculate_available_slots()` 가 무제한(`-1`)을 반환하고, `occupied_slots` 계산을 건너뛴다.
- `add_circuit()` 이 서브도메인과 port 할당을 건너뛴다. ROUTER circuit 은 `port = None` **이면서** `subdomain = None` 으로 생성된다.
- `Circuit.get_endpoint_url()` 에 ROUTER 분기를 추가해 worker 의 단일 광고 base URL(`hostname` + `traffic_port`, scheme 은 `tls_advertised` 에서)을 반환한다. 그 worker 의 모든 circuit 에 같은 URL 이다.
- ROUTER circuit 에서 `open_to_public` 은 무시한다(API 키가 접근을 검사한다). `allowed_client_ips` 는 worker 가 계속 적용한다.
- HA: 여러 router node 가 하나의 `authority` 아래 등록하고(기존 `nodes` counter 의미), 보통 외부 L4 LB 뒤에 두며 그 주소가 광고하는 `hostname` 이 된다. app proxy coordinator 는 authority 의 모든 node 에 같은 circuit 과 mapping 을 전달한다.

### 3. app proxy coordinator: 원하는 상태 저장

worker authority 별로 범위가 정해진 새 테이블 둘이 있고, mutation 이 일어나면 같은 트랜잭션에서 authority 별 단조 증가 `revision` 을 올린다.

```text
router_models:
    id UUID PK
    worker_authority str  (indexed)
    model_name str
    mappings JSONB        # [{"endpoint_id": UUID, "ratio": float}]
    created_at / updated_at
    UNIQUE (worker_authority, model_name)

router_api_keys:
    id UUID PK
    worker_authority str  (indexed)
    key_id str            # manager-side identifier
    token str             # opaque key material (see Security)
    allowed_models JSONB  # ["model-a", "model-b"]
    expires_at datetime | None
    rate_limit int | None
    created_at / updated_at
    UNIQUE (worker_authority, key_id)
```

app proxy coordinator 는 반드시 저장해야 한다. router worker 의 runtime 상태는 설계상 in-memory 이므로, router node 가 (다시) 등록할 때마다 app proxy coordinator 가 전체 mapping 과 key 집합을 재생할 수 있어야 한다.

### 4. app proxy coordinator: manager 스코프 REST API(신규)

기존 `/v2/endpoints` 계열처럼 공유 `X-BackendAI-Token` 으로 인증한다.

| 메서드와 경로 | 용도 |
|---|---|
| `GET /v2/routers/{authority}/models` | 모델 mapping 목록 |
| `PUT /v2/routers/{authority}/models/{model}` | upsert: `{mappings: [{endpoint_id, ratio}]}` |
| `DELETE /v2/routers/{authority}/models/{model}` | 모델 게시 취소 |
| `GET /v2/routers/{authority}/api-keys` | 키 목록(가림 처리) |
| `PUT /v2/routers/{authority}/api-keys/{key_id}` | upsert: `{token, allowed_models, expires_at, rate_limit}` |
| `DELETE /v2/routers/{authority}/api-keys/{key_id}` | 키 해지 |

**사전 배포(proactive-deploy) 의미.** mutation 호출마다 (1) PostgreSQL 에 저장하고 authority 의 `revision` 을 올리며, (2) 대응 event 를 브로드캐스트하고(아래 참고), (3) **첫** worker ack 을 최대 15초 기다린 뒤(`initialize_legacy_circuit` 과 같은 방식) 반환한다. 모든 node 를 기다리지 않고, 복제본 세션 상태가 이 호출을 차단하지 않는다. ack 이 timeout 이어도 호출은 **성공**하고(저장된 상태가 기준이고 pull 조정이 수렴을 보장한다), 응답은 전파가 지연됐다고 표시한다.

### 5. app proxy coordinator: worker 스코프 snapshot 엔드포인트(신규)

```text
GET /api/worker/{worker_id}/router-config
→ {revision, models: [...], api_keys: [...]}
```

router worker 는 등록할 때(전체 in-memory 상태 복원)와 조정 timer 마다 이것을 가져오고, **set-diff** 로 조정한다. `reconcile_traefik_etcd_state` 와 같은 방식이며 worker 쪽으로 옮겼다. 불투명한 `revision` 덕분에 바뀐 것이 없는 poll 은 값싼 no-op 이 된다.

### 6. app proxy coordinator: 새 Pub/Sub event

기존 `events_all-appproxy` bus 에 event 다섯 개를 추가하고, 기존 envelope 과 관례를 따른다. 들어오는 event 는 각각 **정확히 한 엔티티의 전체 새 상태**나 그 삭제를 담는다. 멱등이고 last-writer-wins 이며 버전 chain 이 없다.

| Event | 방향 | args |
|---|---|---|
| `appproxy_router_model_updated_event` | → worker | `(authority, model_json)`: 전체 mapping 상태 |
| `appproxy_router_model_removed_event` | → worker | `(authority, model_name)` |
| `appproxy_router_key_updated_event` | → worker | `(authority, key_id)`: **알림만, token 없음** |
| `appproxy_router_key_removed_event` | → worker | `(authority, key_id)`: 즉시 적용 |
| `appproxy_worker_router_config_applied_event` | ← worker(ack) | `(authority, kind, id)` |

**key 재료는 event bus 를 타지 않는다.** mapping event 는 전체 payload 를 담지만(mapping 에 비밀은 없다), key event 는 id 만 담은 알림이다. worker 는 인증된 `router-config` snapshot 으로 key 재료를 가져온다. circuit event 도 이미 이 공유 bus 를 지나지만 kernel 주소만 담고 자격 증명은 담지 않는다. 이 설계는 그 성질을 유지한다.

app proxy coordinator 는 **두** 동작 모드 모두에서 ROUTER worker 에 이 event 를 낸다. Traefik/etcd 경로는 기본 circuit 에만 적용되고 ROUTER worker 에는 신호를 보내지 않는다.

### 7. Manager: key, 모델, service mapping 관리

Manager 는 **기준 값이자 유일한 사용자 대면 표면**이다.

- **모델 게시.** 게시한 모델 이름을 하나 이상의 배포 엔드포인트와 분할 비율로 잇고 router authority 를 대상으로 하는 새 엔티티다. GraphQL mutation 과 query, CLI, WebUI 로 노출한다. 엔드포인트 lifecycle 과 통합한다. 엔드포인트를 종료하면 어떤 게시에서든 그 엔드포인트를 제거한다(그 엔드포인트를 제외한 mapping 을 다시 게시한다).
- **모델 API 키.** 발급은 사용자가 시작하는 동작이다(WebUI / API / CLI). Manager 가 key 재료(불투명한 `sk-…` 형태 token)를 발급하고 key 소유자인 사용자나 프로젝트, 만료와 함께 저장한다. 배포 토큰 패턴(`EndpointTokenRow`)을 엔드포인트 스코프에서 모델 스코프로 확장했다. 발급, 목록, 교체, 해지는 Manager 동작이다.
- **RBAC 에서 유도한 모델 가시성.** key 의 `allowed_models` 집합은 자유 형식 목록이 *아니다*. Manager 가 key 소유자의 RBAC scope(게시된 모델에 대한 도메인과 프로젝트 권한)에서 계산하고, 발급 시 더 좁힐 수 있으며, 추가한 값 또는 외부에서 지정한 값을 처리한다. key 소유자의 부여나 게시 집합이 변경될 때마다 `/v2/routers/*` 로 다시 계산해 다시 전파한다("요청 경로와 책임 분리" 참고).
- **전파.** Manager 는 router 와 직접 통신하지 않는다. app proxy coordinator 의 `/v2/routers/*` API 를 호출하고(`manager/clients/appproxy/client.py` 에 해당 메서드를 추가한다), app proxy coordinator 가 위에서 설명한 대로 저장하고 전파한다.
- **접근 정보 계약.** ROUTER 게시에 연결된 배포의 사용자에게 보이는 접근 정보는 배포별 URL 과 배포 토큰 대신 (게이트웨이 base URL, 모델 이름, 모델 API 키)가 된다.

### 8. 실패 모델

| 실패 | 결과 |
|---|---|
| Valkey 중단 | event 가 유실된다. manager 호출은 ack timeout 을 표시하고 성공한다. worker 는 주기적 snapshot pull(`reconcile_interval`)로 수렴한다 |
| 변경 중 worker node 중단 | 다시 등록할 때 snapshot pull 로 전체를 재생한다 |
| app proxy coordinator 가 worker 에 접속할 수 없음(NAT/Kubernetes) | 문제되지 않는다. 프로토콜은 worker 에 접속하지 않는다 |
| 두 신호 모두 유실 | 주기적 set-diff pull 이 `reconcile_interval` 안에 복구한다 |
| fan-out 도중 app proxy coordinator 재시작 | 원하는 상태가 PostgreSQL 에 있다. pull 조정이 수렴한다 |

해지의 한계는 다음과 같다. key 제거 알림을 놓친 node 는 다음 pull 에서 수렴하므로, 그 node 의 최악 해지 창은 worker 의 `reconcile_interval`(Continuum Router 쪽 기본 15초)이다.

### 9. 보안

- 제어 플레인 REST(manager→app proxy coordinator, worker→app proxy coordinator)는 모두 공유 `X-BackendAI-Token` 인증을 유지한다.
- key 재료는 Manager 와 app proxy coordinator 에 저장되고 router 에서는 메모리에 있으며, Valkey 를 지나지 않는다. 두 HTTP 구간은 TLS 나 신뢰 네트워크로 운영해야 하고, key 값을 log 에 남기지 않아야 하며, 목록은 가림 처리한다.
- 배포 토큰(`Circuit.generate_jwt` / `EndpointTokenRow`)은 ROUTER circuit 에 **사용하지 않는다**. 모델 API 키가 데이터 플레인 자격 증명을 대신한다. 기존 배포 토큰은 WILDCARD/PORT circuit 에서 변경되지 않고 계속 동작한다.

## 이전과 호환

### 하위 호환

- 모든 변경은 additive 다. 새 enum 값, 새 선택 등록 field, 새 테이블, 새 API 경로, 새 event 타입이다. 기존 WILDCARD/PORT worker, 기존 circuit, 배포 토큰, Traefik 경로는 변경되지 않는다.
- ROUTER worker 는 이 제안 이전의 app proxy coordinator 에 등록할 수 없다(등록 검증이 알 수 없는 `frontend_mode` 값을 거부한다). 이것이 의도한 버전 검사다.
- `SerializableCircuit` 소비자는 `frontend_mode == "router"` 이면서 `port` 와 `subdomain` 이 둘 다 null 인 경우를 견뎌야 한다. 기존 worker 는 이미 `target_worker_authority` 로 event 를 필터링하므로 ROUTER circuit 을 보지 않는다.

### 깨지는 변경

기존 배포에는 없다. 엔드포인트 URL 을 보여 주는 WebUI/CLI 흐름에는 ROUTER 로 게시한 배포를 위한 새 표시 경로(base URL + 모델 이름 + key)가 필요하고, 이는 additive 다.

## 구현 계획

1. **1단계: common + coordinator core**: `FrontendMode.ROUTER`, `traffic_port`, 등록 검증, slot 을 건너뛰는 `add_circuit()`, `get_endpoint_url()` 의 ROUTER 분기.
2. **2단계: 원하는 상태 + API**: `router_models` / `router_api_keys` 테이블(appproxy DB 용 alembic migration 포함), authority 별 `revision`, `/v2/routers/*` manager 스코프 API, `/api/worker/{id}/router-config` worker 스코프 snapshot.
3. **3단계: 전파**: event 다섯 개, mutation handler 의 첫 ack 사전 배포 연결, 등록 시 재생.
4. **4단계: manager 표면**: 모델 게시와 모델 API 키 엔티티, GraphQL/CLI, appproxy client 메서드, 엔드포인트 lifecycle hook, WebUI 접근 정보 표시.
5. **5단계: 종단 간 검증**: `appproxy` 기능으로 빌드한 Continuum Router worker 를 대상으로 통합 테스트를 한다(worker 쪽 추적: lablup/continuum-router#748 과 그 구현 Epic).

## 열린 질문

- **authority 스코프의 세분화.** mapping 과 key 는 router authority 별로 범위가 정해진다. 게시 하나가 Manager 동작 하나로 여러 authority(예: region 별 하나)를 대상으로 하는 방안과 그 조합을 호출자에게 맡기는 방안 사이의 선택에 대한 결정이 필요하다.
- **key 보관 강화.** app proxy coordinator 는 재생을 지원하려고 key 재료를 평문으로 저장한다. Manager 와 app proxy coordinator 가 HMAC 이나 hash 만 저장하고 평문은 발급 시 한 번만 보여 주는 방식을 택하는지에 대한 결정이 필요하다. 그 대가는 router 가 값 대신 hash 를 맞춰야 하거나, 재생할 때마다 다시 발급해야 한다.
- **엄격한 해지 선택지.** `reconcile_interval` 로 제한되는 해지 창이 모든 tenant 에 충분한지와, key 삭제에 모든 ALIVE node 확인 모드를 선택적으로 둘 필요가 있는지에 대한 결정이 필요하다.
- **오토스케일링과의 상호 작용.** mapping 비율은 정적이다. 배포 전략 handler(BEP-1049)가 같은 `/v2/routers/*` API 로 비율을 동적으로(예: canary 승격) 조정할 수 있어야 하는지에 대한 결정이 필요하다.

## 참고

- [Continuum Router: AppProxy Worker Mode design](https://github.com/lablup/continuum-router/pull/748)
  (`docs/en/architecture/appproxy-worker.md`): 이 설계의 worker 쪽 절반이다. 두 단계 라우팅 구현, 가중치 구성, key 강제, worker 의 조정 loop 를 다룬다.
- [BEP-1005: Unified AppProxy](BEP-1005-unified-appproxy.md): 장기 통합 방향이다. 이 제안은 현재 app proxy coordinator/worker 분리 안에 머물고 그 방향과 호환된다.
- [BEP-1006: Service Deployment Strategy](BEP-1006-service-deployment-strategy.md),
  [BEP-1049: Deployment Strategy Handler](BEP-1049-deployment-strategy-handler.md): 이 제안이 기반으로 하는 배포와 복제본 lifecycle.
- [BEP-1008: RBAC](BEP-1008-RBAC.md),
  [BEP-1012: RBAC](BEP-1012-RBAC.md),
  [BEP-1048: RBAC Entity-Relationship Model](BEP-1048-RBAC-entity-relationship-model.md): key → 모델 가시성을 유도하는 스코프와 권한 모델.
- `src/ai/backend/appproxy/coordinator/types.py`(`CircuitManager`): 이 제안이 방식을 재사용하는 기존 전파 메커니즘.
