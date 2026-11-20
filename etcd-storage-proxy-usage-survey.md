# 스토리지 프록시의 etcd 사용 전수 조사

스토리지 프록시 본체가 etcd에서 읽고 쓰는 키 전부.
플러그인(`StoragePluginContext`, `StorageArtifactVerifierPluginContext`, webapp 플러그인)은 범위에서 제외했다.
`volumes/ddn`은 플러그인이 아니라 in-tree 볼륨 백엔드라 포함한다.

관련 문서: `etcd-agent-config-survey.md` (에이전트 측), `etcd-manager-usage-survey.md`

## 스코프

`config/loaders.py:54-57`.

| 스코프 | 접두사 |
|---|---|
| GLOBAL | `""` |
| NODE | `nodes/storage/{storage_proxy.node_id}` |

**NODE 접두사에 쓰는 코드가 없다.** 아래 읽기는 전부 기본 `MERGED` 스코프라 매번 존재하지 않는 `nodes/storage/{id}/...`를 먼저 조회한 뒤 GLOBAL로 떨어진다.

## 설정 로더

**없다.** 설정은 TOML 단독이고 etcd는 런타임 직접 조회로만 쓴다.
매니저의 `LoaderChain` + `EtcdConfigWatcher`에 해당하는 것이 없으므로 etcd 값이 `StorageProxyUnifiedConfig`의 타입 필드로 들어오지 않고, 재적용도 되지 않는다. (BA-7794가 이 문제를 다룬다.)

## 읽기

| 키 | 위치 | 용도 |
|---|---|---|
| `config/redis` (prefix) | `dependencies/infrastructure/redis_config.py:29` | valkey 클라이언트 · 메시지 큐 · 서비스 디스커버리 |
| `config/redis` (prefix) | `migration.py:236` | `check_and_upgrade`. 같은 값을 **trafaret `redis_config_iv`로 따로 검증**한다 |
| `volumes/_mount` | `api/manager.py:1450,1500` | 마운트 prefix |
| `config/watcher/file-io-timeout` | `api/manager.py:1501` | watcher 호출 타임아웃 |
| `ddn/main-project-id` | `volumes/ddn/__init__.py:67` | DDN EXAScaler 프로젝트 id 카운터 |
| `ai/backend/service_discovery/**` | `dependencies/system/service_discovery.py:74` | 서비스 레지스트리 |

## 쓰기

| 키 | 위치 | 계기 |
|---|---|---|
| `ddn/main-project-id` | `volumes/ddn/__init__.py:72` | 쿼타 스코프 생성 시 카운터 증가 |
| `ai/backend/service_discovery/**` | register / heartbeat / unregister | |

**설정은 쓰지 않는다.** 쓰기가 이 둘뿐이다.

## 눈에 띄는 것

- **`ddn/main-project-id`에 경합이 있다.** `_read_main_project_id()`(`volumes/ddn/__init__.py:66-72`)가 `get` → `int(val)` → `put(val+1)`을 수행하는데 CAS도 락도 없다. `AsyncEtcd.replace()`가 compare-and-swap을 제공하지만 쓰지 않는다. 쿼타 스코프를 동시에 생성하면 **두 스코프가 같은 프로젝트 id를 받는다.**
- **NODE 스코프가 선언만 되어 있다.** 에이전트의 SGROUP과 같은 패턴이다. 쓰는 쪽이 없으므로 모든 읽기가 헛조회를 한 번씩 더 한다.
- **`config/redis`가 두 스키마로 검증된다.** `redis_config.py:29`는 pydantic `RedisConfig`, `migration.py:236`은 trafaret `redis_config_iv`. 같은 etcd 값에 대해 두 검증 경로가 일치하지 않는다.
- `volumes/_mount`와 `config/watcher/file-io-timeout`은 에이전트도 같은 키를 읽는다. 전자는 BA-7655가 DB로 이관 중이고, BA-7794는 이 둘을 명시적으로 범위에서 제외했다.
