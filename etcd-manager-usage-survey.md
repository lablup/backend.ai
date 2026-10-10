# 매니저의 etcd 사용 전수 조사

매니저 본체와 `src/ai/backend/manager/BUILD`에 선언된 내장 플러그인이 etcd에서 읽고 쓰는 키 전부.
`plugins/` 디렉터리의 외부 플러그인은 범위에서 제외했다.

관련 문서: `etcd-agent-config-survey.md` (에이전트 측), `etcd-storage-proxy-usage-survey.md`

## 스코프

**GLOBAL 전용**이다. `AsyncEtcd.create_from_config`(`common/etcd.py:348-351`)가 `{ConfigScopes.GLOBAL: ""}`만 넣고
`# TODO: provide a way to specify other scope prefixes` 주석이 붙어 있다. 매니저는 SGROUP·NODE 스코프를 쓰지 않는다.

## 설정 로더

`dependencies/config/provider.py:63-80`, `cli/context.py:150-154`. 뒤가 앞을 덮는다.

| prefix | 주체 | 결과 |
|---|---|---|
| `config/` 전체 | `LegacyEtcdLoader.load()` (`:43`) | `ManagerUnifiedConfig` 최상위로 머지 |
| `volumes/` 전체 | `LegacyEtcdVolumesLoader.load()` (`:172`) | `volumes` 섹션 |
| `ai/backend/config/common` | `EtcdConfigLoader` | 전 컴포넌트 공통 |
| `ai/backend/config/manager` | `EtcdConfigLoader` | 매니저 전용 |
| `ai/backend/config` | `EtcdConfigWatcher` (watch) | 변경 시 설정 전체 재검증 |
| `config/redis` | `LegacyEtcdLoader(etcd, config_prefix="config/redis")` (`cli/context.py:198`) | CLI가 valkey 클라이언트를 만들 때만 |

## 읽기 — 개별 키

| 키 | 위치 | 용도 |
|---|---|---|
| `config/api/allow-origins` | `legacy_etcd_loader.py:159` | CORS |
| `config/resource_slots` (prefix) | `legacy_etcd_loader.py:107` | 알려진 슬롯 타입 |
| `config/agent/max-container-count` | `repositories/scheduler/repository.py:334` | 스케줄링 상한 |
| `config/api/resources/group_resource_visibility` | `repositories/resource_preset/repository.py:239` | check-presets 노출 여부 |
| `config/idle/app-streaming-packet-timeout` | `services/stream/service.py:165` | 앱 스트리밍 타임아웃 |
| `config/plugins/accelerator/cuda/quantum_size` | `api/gql_legacy/scaling_group.py:569` | `ScalingGroup` GQL 필드 |
| `volumes/_types` (prefix) | `legacy_etcd_loader.py:124` | 허용 vfolder 타입 |
| `volumes/_mount` | `services/vfolder/services/vfolder.py:884` | 마운트 prefix |
| `volumes/proxies/{proxy}` (prefix) | `cli/etcd.py:336,369` | CLI sftp scaling group 조회 |
| `manager/status` | `legacy_etcd_loader.py:145`, watch `:151` | 매니저 상태 |
| `manager/announcement`, `/message`, `/enabled` | `services/manager_admin/service.py:101-104` | 공지 (legacy 단일 키 fallback 포함) |
| `nodes/manager` (prefix) | `legacy_etcd_loader.py:141` | **호출자 없음 — 죽은 리더** |
| `nodes/agents/{id}/ip`, `/watcher_port` | `services/vfolder/services/vfolder.py:872`, `services/agent/service.py:119` | watcher 접속 정보 |
| `ai/backend/service_discovery/**` | `ETCDServiceDiscovery.discover`, `get_service_group` | 서비스 레지스트리 |

## 쓰기

| 키 | 위치 | 계기 |
|---|---|---|
| `nodes/manager/{instance_id}` = `"up"` | `register_myself` (`legacy_etcd_loader.py:78`) ← `api/rest/etcd/lifecycle.py:24` | 기동 (pidx 0만) |
| 같은 키 삭제 | `deregister_myself` (`legacy_etcd_loader.py:85`) | 종료 |
| `manager/status` | `update_manager_status` (`legacy_etcd_loader.py:102`) | 상태 전이 |
| `config/resource_slots/{slot}` | `update_resource_slots` (`legacy_etcd_loader.py:99`) ← `repositories/agent/repository.py:142` | 에이전트가 새 슬롯 타입을 보고할 때 |
| `manager/announcement/*` | `atomic_replace_prefixes` (`services/manager_admin/service.py:134`) | 공지 갱신. 서브트리를 원자적으로 교체해 legacy 단일 키까지 함께 제거 |
| `ai/backend/config/{service}` | `api/gql_legacy/service_config.py:216` | `modify_service_config` mutation |
| `ai/backend/service_discovery/**` | register / heartbeat / unregister / `sync_model_service_routes` | |
| **임의 키** | `services/etcd_config/service.py:177-187` | REST `POST /config/set`, `POST /config/delete` (superadmin) |
| **임의 키** | `cli/etcd.py:57,85,117-119,185,192` | `mgr etcd put / put-json / move / delete` |
| `volumes/proxies/{proxy}/sftp_scaling_groups` | `cli/etcd.py:340,373` | CLI |
| `config/docker/registry` | alembic `1d42c726d8a3:318` | **downgrade 시에만** (upgrade는 PSQL로 이관 후 prefix 삭제) |

## 락

| 키 | 위치 |
|---|---|
| `ai/backend/config/lock/modify_service_config` | `EtcdLock` (`api/gql_legacy/service_config.py:191,205`) |
| `str(LockID)` | `manager.distributed-lock = "etcd"`일 때 전역 타이머 락 (`dependencies/domain/distributed_lock.py:75`) |

## 내장 플러그인

각 플러그인 컨텍스트는 init 시 `config/plugins/{group_key}/{plugin_name}/`를 읽고 같은 prefix를 watch한다
(`common/plugin/__init__.py:177`, `:201-206`). `group_key`는 `backendai_(\w+)_v\d+`의 캡처 그룹이다.

| 컨텍스트 | 생성 위치 | group_key |
|---|---|---|
| `WebappPluginContext` | `server.py:86` | `webapp` |
| `HookPluginContext` | `dependencies/plugins/hook.py:42` | `hook` |
| `NetworkPluginContext` | `dependencies/plugins/network.py:35` | `network_manager` |
| `ManagerErrorPluginContext` | `dependencies/plugins/monitoring.py:50` | `error_monitor` |
| `ManagerStatsPluginContext` | `dependencies/plugins/monitoring.py:80` | `stats_monitor` |
| `EventDispatcherPluginContext` | `dependencies/plugins/event_dispatcher.py:37` | `event_dispatcher` |

내장 플러그인은 `src/ai/backend/manager/BUILD:161-173`에 선언된 7개다. dev 환경에서는 BUILD 파일이 entrypoint 스캔 대상이다 (`plugin/entrypoint.py:84-95`).

| etcd prefix | 구현 | 키 |
|---|---|---|
| `config/plugins/hook/totp/` | `plugin/totp/hook:TOTPHook` | `issuer`, `forced`, `totp_registration_url`, `token_secret`, `token_lifetime` (`totp/config.py:8-30`) |
| `config/plugins/webapp/totp/` | `plugin/totp/webapp:TOTPWebapp` | 위와 동일 스키마 |
| `config/plugins/hook/openid/` | `plugin/openid/hook:OIDCHookPlugin` | `secret` |
| `config/plugins/webapp/openid/` | `plugin/openid/webapp:OIDCWebAppPlugin` | `secret`, `login_uri`, `openid/{well_known,authorization_endpoint,token_endpoint,jwks_uri,client_id,client_secret,group_mapping,group_order}` (`openid/config.py:10-61`) |
| `config/plugins/hook/auth_keypair/` | `plugin/keypair/hook:KeypairAuthHookPlugin` | 아래 참조 |
| `config/plugins/webapp/auth_keypair/` | `plugin/keypair/webapp:KeypairAuthWebAppPlugin` | `auth_token_name` (기본 `"sToken"`, `keypair/hook.py:28-30`) |
| `config/plugins/network_manager/overlay/` | `network/overlay:OverlayNetworkPlugin` | `mtu` (기본 1500, `network/overlay.py:15-17`) |

`error_monitor`, `stats_monitor`, `event_dispatcher` 그룹에는 내장 플러그인이 없다. 컨텍스트는 뜨지만 prefix가 비어 있다.

### 핫 리로드가 동작한다

내장 플러그인은 `config_watch_enabled`를 재정의하지 않으므로 기본값 `True`이고, `update_plugin_config()`가 실제로 타입 설정을 재구축한다.

| 플러그인 | 동작 |
|---|---|
| `openid/webapp.py:220-222`, `openid/hook.py:41-43` | `OIDCWebAppConfig` / `OIDCHookConfig` 재생성 |
| `totp/hook.py:57-61` | `TOTPConfig` 재생성 + `_token_parser`의 secret·lifetime 갱신 |
| `keypair/{webapp,hook}.py` | `self.plugin_config` 교체 |

OIDC 엔드포인트와 클라이언트 시크릿, TOTP 토큰 시크릿은 재시작 없이 바뀐다.
에이전트 측 플러그인이 전부 `pass`인 것과 반대다 (`etcd-agent-config-survey.md` 참조).

### keypair 플러그인은 서로 다른 두 키를 읽는다

`keypair/webapp.py:36`(`login` 핸들러)과 `keypair/hook.py:126`(`authorize`)이 요청마다 다음을 수행한다.

```python
shared_config = await config_provider.legacy_etcd_config_loader.load()   # get_prefix("config") 전체
plugin_config = nmget(shared_config, "plugins.webapp.keypair_auth")      # keypair/utils.py:12
```

| 읽는 값 | 실제 etcd 경로 | 위치 |
|---|---|---|
| `auth_token_name` | `config/plugins/webapp/auth_keypair/` (`self.plugin_config`) | `hook.py:128` |
| `secret`, `login_uri` | `config/plugins/webapp/keypair_auth/` (`nmget`) | `webapp.py:54-55` |
| `secret` | `config/plugins/webapp/keypair_auth/` (`nmget`) | `hook.py:137` |

entrypoint 이름은 `auth_keypair`인데 코드가 찾는 경로는 `keypair_auth`로 뒤집혀 있다. 두 키를 모두 채워야 하고, 한쪽만 채우면 `KeyError`로 로그인이 깨진다.

`nmget` 경로는 어떤 컨텍스트의 watch prefix에도 걸리지 않는다. 대신 요청마다 `config/` 전체 prefix를 etcd에서 다시 읽는다.

## 눈에 띄는 것

- **`get_manager_nodes_info()`가 죽은 리더다** (`legacy_etcd_loader.py:140`). 호출자가 없다. 같은 `nodes/manager` prefix는 에이전트의 `detect_manager()`(`agent/server.py:519,522`)가 실제로 읽는다.
- **임의 키 쓰기 표면이 둘이고 스키마 검증이 없다** — REST `/config/{set,delete}`와 `mgr etcd` CLI. 오타 하나가 unknown-field 경고로만 남는다. `config/api/resources/group_resource_visibility`(snake) 대 스키마 별칭(kebab) 류의 불일치가 조용히 생기는 경로다.
- **다른 컴포넌트 네임스페이스의 키를 직접 읽는다** — `config/agent/max-container-count`(에이전트는 파싱조차 하지 않음), `config/plugins/accelerator/cuda/quantum_size`(에이전트 가속기 플러그인 설정). 후자는 리소스 그룹별 GQL 필드로 노출되지만 실제로는 전역 단일 값이다 (BA-5692).
