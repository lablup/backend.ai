# Backend.AI on k8s (DooD) — 트러블슈팅 노트

`docs/dood2` 브랜치에서 backend.ai 전체 스택을 k8s 위에 올리며 부딪힌 문제와 해결 과정의 기록.

## 환경 개요

| 항목 | 값 |
|---|---|
| **노드** | charsyam-gen1 (control-plane), ser8 / charsyam-nvidia (worker) |
| **runtime** | containerd 2.2.0 (ser8) / 1.7.28 (others) |
| **k8s** | v1.34.1 |
| **CNI** | (existing) |
| **storage** | local-path-provisioner + ser8 의 NFS server 컨테이너 (bai-nfs) → `/vfroot` |
| **registry** | ser8 의 docker container `registry:2` (192.168.0.156:5000) |

### 컴포넌트 배치

```
[k8s pod]                              [ser8 호스트 docker daemon]
─────────                              ──────────────────────────
bai (manager, postgres, redis, etcd)   bai-nfs (NFS server)
bai-sp (storage-proxy)                 registry:2
bai-agent / bai-agent-gpu              (build cache 의 dev image들)
bai-webserver
bai-router (Apollo Router)
bai-appproxy-coordinator
bai-appproxy-worker (hostNetwork)
coordinator-proxy (nginx CORS proxy)
agent (DaemonSet) ── docker.sock ─► kernel.python.* (호스트 docker 안)
```

핵심: **kernel container 는 k8s pod 가 아니라 호스트 docker daemon 의 일반 container** (DooD = Docker out of Docker).

---

## 1. 인프라 / 노드 셋업

### 1.1 사설 registry — 노드 containerd 가 HTTPS 시도

**문제**: ser8 에 `registry:2` 컨테이너로 사설 registry 띄움 (192.168.0.156:5000). 다른 노드에서 `ctr -n k8s.io images pull` 시 `http: server gave HTTP response to HTTPS client`.

**원인**: containerd 가 기본적으로 모든 registry 를 HTTPS 로 시도. 우리 registry 는 HTTP only.

**해결**: 각 노드에 `hosts.toml` 추가:
```bash
sudo mkdir -p /etc/containerd/certs.d/192.168.0.156:5000
sudo tee /etc/containerd/certs.d/192.168.0.156:5000/hosts.toml > /dev/null <<EOF
server = "http://192.168.0.156:5000"

[host."http://192.168.0.156:5000"]
  capabilities = ["pull", "resolve"]
EOF
```

### 1.2 containerd 2.x — hosts.toml 무시

**문제**: ser8 의 containerd 2.2.0 은 위 hosts.toml 작성 후에도 여전히 HTTPS 시도.

**원인**: containerd 2.x 가 `[plugins."io.containerd.transfer.v1.local"]` 이라는 새 transfer plugin 으로 image pull. 그 plugin 의 `config_path = ""` (빈 문자열) 라 `/etc/containerd/certs.d` 를 못 읽음. legacy `[plugins."io.containerd.grpc.v1.cri".registry]` 의 `config_path` 만 설정했었음.

**해결**: `config.toml` 의 transfer plugin 의 `config_path` 도 갱신 후 containerd restart:
```bash
sudo sed -i 's|config_path = ""|config_path = "/etc/containerd/certs.d"|' /etc/containerd/config.toml
sudo systemctl restart containerd
```

### 1.3 ctr 명령은 hosts.toml 자동 안 봄

**문제**: `ctr -n k8s.io images pull 192.168.0.156:5000/...` 가 HTTPS 시도하며 실패. hosts.toml + transfer config 다 맞췄는데도.

**원인**: `ctr` CLI 는 containerd client 라이브러리를 직접 호출. `--hosts-dir` 옵션 명시 안 하면 hosts.toml 자동 lookup 안 함. **kubelet 의 CRI image pull 은 자동 lookup** 하므로 실제 운영에는 무관.

**해결 / 검증**: `crictl pull` (kubelet 과 같은 CRI 경로) 으로 검증:
```bash
sudo crictl pull 192.168.0.156:5000/backend.ai-agent:dev
```

### 1.4 노드 docker daemon — insecure-registries 누락

**문제**: kernel scheduling 시도 시 `DockerError(500, 'http: server gave HTTP response to HTTPS client')` — agent 가 호스트 docker daemon (DooD) 을 통해 image pull 시도.

**원인**: containerd 만 설정하고 호스트 docker daemon 의 `/etc/docker/daemon.json` 은 안 건드림. agent 의 kernel image pull 은 docker daemon 경로.

**해결**:
```bash
sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{ "insecure-registries": ["192.168.0.156:5000"] }
EOF
sudo systemctl restart docker
```

### 1.5 노드 추가 후 stuck 된 provisioner

**문제**: helm install 시 PVC 들이 모두 `Pending` (WaitForFirstConsumer 후 ExternalProvisioning 단계에서 멈춤).

**원인**: `local-path-provisioner` pod 가 charsyam-nvidia 에 떠 있었는데, 그 노드의 containerd restart 영향으로 pod 의 watch loop 가 stale (`dial tcp 10.96.0.1:443: no route to host`).

**해결**: provisioner pod 삭제 → kubelet 이 새 pod 띄움 → 정상 동작.

---

## 2. 이미지 빌드 / 배포

### 2.1 manager / agent / sp dev image 만들기

**문제**: helm chart values 의 `image.repository = backend.ai-agent` 같은 `dev` 태그가 사설 registry 에 없음.

**해결 흐름**:
1. ser8 의 docker 에 이미 `backend.ai-{agent,manager,storage-proxy}:dev` 가 존재
2. retag → `localhost:5000/backend.ai-X:dev` → push (docker daemon 은 `localhost` 는 자동 insecure)
3. values 의 `repository` 를 `192.168.0.156:5000/backend.ai-X` 로 갱신

### 2.2 코드 변경분만 빠르게 반영하는 patch image

**문제**: pants build 가 길어서 (10–15 분) 매번 풀빌드 비효율.

**해결**: 호스트에서 `pants package src/ai/backend/agent:dist` 등으로 wheel 만 빌드 → patch Dockerfile 로 base image 위에 wheel layer 만 추가:
```dockerfile
FROM backend.ai-agent:dev
USER root
COPY dist/backend_ai_agent-*.whl /tmp/
RUN /opt/backend.ai/venv/bin/pip install --force-reinstall /tmp/*.whl
USER backendai
```
5 초 안에 새 image. webserver / appproxy / manager 도 같은 패턴으로 26.4.4rc6 으로 업그레이드.

### 2.3 `pullPolicy: IfNotPresent` 캐시

**문제**: 새 image push 후 helm upgrade + pod restart 했는데도 옛 image digest 그대로 사용.

**원인**: `IfNotPresent` 이고 tag (`dev`) 가 같으니 노드 containerd 가 캐시 사용.

**해결**: `pullPolicy: Always` 로 변경 + rollout restart. 또는 매번 tag 다르게.

---

## 3. helm chart 작성

기존 `docs/dood` 브랜치엔 manager / agent / storage-proxy chart 만 있고 webserver / app-proxy / apollo-router 가 없음. 신규 작성.

| 컴포넌트 | 위치 |
|---|---|
| webserver | `deploy/helm/backend-ai-webserver/` |
| apollo-router | `deploy/helm/backend-ai-apollo-router/` (with `files/supergraph.graphql`) |
| appproxy-coordinator | `deploy/helm/backend-ai-appproxy-coordinator/` |
| appproxy-worker | `deploy/helm/backend-ai-appproxy-worker/` |
| coordinator-proxy (nginx) | `/tmp/coordinator-proxy.yaml` (raw manifest) |

### 3.1 webserver — redis config 형식

**문제**: webserver 가 `RedisTarget must have an address for standalone mode` 로 죽음.

**원인**: 우리가 만든 conf 에 `redis.host = "..."` / `redis.port = ...` 형식. backend.ai-web 은 `[session.redis] addr = "host:port"` 형식 기대.

**해결**: `[session.redis]` 섹션 + `addr = "bai-redis:6379"` + 별도 `[session.redis.redis_helper_config]`.

### 3.2 webserver — redis password 불일치

**문제**: `WRONGPASS: invalid username-password pair`.

**해결**: manager chart 의 secret `redis-password` (`local-dev-redis`) 와 동일하게 webserver secret 갱신 후 **rollout restart** (helm upgrade 가 secret 변경에는 자동 rollout 트리거 안 함).

### 3.3 coordinator — config 누락 필드

**문제**: 부팅 시 `3 validation errors for ServerConfig: db.type / secrets / permit_hash`.

**원인**: backend.ai-appproxy-coordinator config schema 가 `db.type = "postgresql"` 필수, `[secrets]` / `[permit_hash]` 별도 섹션 필요. 처음에 빠뜨림.

**해결**: configmap 에 모두 추가.

### 3.4 coordinator — DB schema 미생성 (`circuits` table missing)

**문제**: coordinator 가 부팅 후 `UndefinedTableError: relation "circuits" does not exist`.

**원인**: chart 에 schema migration job 추가 안 함. 빈 DB 그대로.

**해결**: 수동 alembic 실행.
```bash
kubectl cp configs/app-proxy-coordinator/halfstack.alembic.ini <pod>:/tmp/alembic.ini
# alembic.ini 의 sqlalchemy.url 만 우리 환경으로 sed
kubectl exec <pod> -- /opt/backend.ai/venv/bin/backend.ai app-proxy-coordinator \
  -f /etc/backend.ai/coordinator.toml schema oneshot -f /tmp/alembic.ini
```

### 3.5 worker — `bind_port_range` 가 kubelet 포트와 충돌

**문제**: hostNetwork=true 인 worker 가 `OSError: [Errno 98] address already in use ('0.0.0.0', 10248)`.

**원인**: 우리가 처음 set 한 `bind_port_range = [10205, 10300]` 안에 kubelet 의 healthz(10248) / kube-proxy(10249) / kubelet API(10250) 가 모두 포함됨.

**해결**: `bind_port_range = [10301, 10400]` 로 옮김.

### 3.6 worker — config 의 list / tuple 형식

**문제**:
- `accepted_traffics = "interactive,inference"` → "Input should be a valid list"
- `bind_port_range = "10205,10300"` → "Input should be a valid tuple"

**원인**: TOML 의 array 형식 필요.

**해결**:
```toml
accepted_traffics = ["interactive", "inference"]
bind_port_range = [10301, 10400]
```

### 3.7 worker — taint / toleration

**문제**: hostNetwork + nodeSelector ser8 적용 후 Pending — `untolerated taint {backendai.io/dedicated: swarm-manager}`.

**해결**: deployment template 에 `tolerations` 블록 + values 에:
```yaml
tolerations:
  - key: backendai.io/dedicated
    operator: Equal
    value: swarm-manager
    effect: NoSchedule
```

### 3.8 worker — rolling update 시 hostPort 충돌

**문제**: helm upgrade 시 새 ReplicaSet pod 가 `didn't have free ports` 로 Pending. 옛 pod 가 host port 점유 중.

**원인**: hostNetwork=true + maxSurge=1 (default) → 두 pod 가 같은 hostPort 충돌.

**해결 (임시)**: `kubectl scale rs <old-rs> --replicas=0` 으로 옛 RS 강제 종료. 영구 해결은 deployment strategy 를 `Recreate` 로.

---

## 4. 데이터 / fixture 셋업

manager chart 의 `fixture-populate` job 이 `bootstrap-fixture.json` + `resource-slot-types.json` 만 load. 나머지 fixture 는 수동 populate 필요.

### 4.1 keypair 누락 — `Access key not found in HMAC`

**원인**: bootstrap-fixture 의 user 들은 `main_access_key: null`. keypair table 자체가 빈 상태.

**해결**:
```bash
kubectl cp fixtures/manager/example-keypairs.json <manager-pod>:/tmp/keys.json
kubectl exec <manager-pod> -- backend.ai mgr -c /etc/backend.ai/manager.toml fixture populate /tmp/keys.json
```

### 4.2 main_access_key link 누락 — `No such User keypair`

**원인**: keypair 는 등록됐지만 user.main_access_key 가 여전히 null.

**해결**: `example-set-user-main-access-keys.json` 추가 populate.

### 4.3 container registry 누락

**문제**: kernel image scan 안 됨. `./bai admin image search` 빈 결과.

**원인**: bootstrap-fixture 에 container_registries 안 들어감.

**해결**: 자체 registry fixture JSON 작성 + populate + `backend.ai mgr image rescan <registry_name>`:
```json
{
  "container_registries": [{
    "id": "<uuid>",
    "registry_name": "192.168.0.156:5000",
    "url": "http://192.168.0.156:5000",
    "type": "docker",
    "project": "stable"
  }]
}
```

`type=local` 은 manager pod 의 localhost docker 를 보려 해서 우리 환경에서 동작 안 함 (manager pod 안에 docker daemon 없음).

### 4.4 etcd 의 vfolder types 누락 — "user-owned vfolder is not allowed"

**원인**: `etcd:/sorna/local/volumes/_types/` 가 비어있어서 manager 의 `_check_ownership_allowed` 가 모든 ownership type 거부.

**해결**:
```bash
kubectl exec bai-etcd-0 -- etcdctl put /sorna/local/volumes/_types/user 1
kubectl exec bai-etcd-0 -- etcdctl put /sorna/local/volumes/_types/group 1
```

### 4.5 keypair_resource_policies — vfolder host 미허용

**문제**: `'create-vfolder' Not allowed in vfolder host('proxy1:volume1')`.

**원인**: default policy 의 `allowed_vfolder_hosts` = `{local:volume1: [...]}` (옛 host 이름). 우리 storage-proxy 는 `proxy1:volume1`.

**해결**:
```sql
UPDATE keypair_resource_policies SET allowed_vfolder_hosts = '{"proxy1:volume1": ["create-vfolder", "modify-vfolder", "delete-vfolder", "mount-in-session", "upload-file", "download-file", "invite-others", "set-user-specific-permission"]}'::jsonb WHERE name = 'default';
```

### 4.6 domains.allowed_docker_registries

**문제**: session 생성 시 `unknown alias or disallowed registry`.

**원인**: `default` domain 의 `allowed_docker_registries = {cr.backend.ai, index.docker.io}`. 우리 사설 registry 누락.

**해결**:
```sql
UPDATE domains SET allowed_docker_registries = array_append(allowed_docker_registries, '192.168.0.156:5000') WHERE name = 'default';
```

### 4.7 scaling_groups.wsproxy_addr — 옛 wsproxy 가리킴

**문제**: session start-service 시 manager 가 옛 wsproxy 의 default URL `http://127.0.0.1:5050` 호출 → connection refused.

**원인**: manager 코드는 새 app-proxy 와 옛 wsproxy 가 같은 `wsproxy_addr` / `wsproxy_api_token` column 사용 (HTTP-level interface 호환). 우리 환경에서는 그 값이 옛 default 그대로.

**해결**:
```sql
UPDATE scaling_groups SET
  wsproxy_addr = 'http://192.168.0.156:30201',  -- nginx CORS proxy 앞단
  wsproxy_api_token = 'CHANGE-ME-COORDINATOR-API-TOKEN'
WHERE name = 'default';
```

---

## 5. manager / webserver 버전 mismatch

**문제**: webserver 로 vfolder 생성 시도 → manager log 에 `Unknown type 'CreateVFolderV2Input'`, `Cannot query field 'createVfolderV2'`.

**원인**:
- 기존 manager image 가 26.4.0rc1 (graphene legacy schema 만).
- 우리가 새로 빌드한 webserver 가 26.4.4rc6 (새 `createVfolderV2` mutation 호출).
- 두 버전의 GraphQL schema 가 다름.

**해결 1: manager 도 26.4.4rc6 으로 업그레이드** — patch image 패턴.

**해결 2: schema migration** — manager upgrade 후 routings.health_check column 등 새 컬럼 누락으로 manager 500 에러. 수동 `alembic upgrade head`:
```bash
kubectl exec <manager-pod> -- /opt/backend.ai/venv/bin/alembic -c /etc/backend.ai/alembic.ini upgrade head
```
chart 의 `schema-migrate` job 은 "Detected an existing database" 라며 자동 적용 안 함 (major upgrade 가정).

---

## 6. Apollo Router (GraphQL supergraph)

backend.ai 의 새 v2 는 graphene legacy schema 와 strawberry v2 schema 가 공존. 두 schema 의 통합은 Apollo Router 라는 별도 GraphQL gateway 가 담당.

### 6.1 webserver UI 가 새 mutation 호출하는데 받는 schema 는 legacy

**문제**: `Unknown type 'CreateVFolderV2Input'`. manager 안에 strawberry schema 가 있는데도 호출 안 됨.

**원인**: manager 의 endpoint:
- `/admin/gql` → graphene legacy schema
- `/admin/gql/strawberry` → strawberry v2 schema

webserver 는 항상 `/admin/gql` 로만 보냄. 둘을 통합하는 게 Apollo Router 의 supergraph.

**해결**: Apollo Router pod + supergraph.graphql ConfigMap. supergraph 파일은 manager repo 의 `docs/manager/graphql-reference/supergraph.graphql` 사용, URL hardcode (`host.docker.internal:8091`) 만 우리 k8s service DNS 로 patch.

```yaml
supergraph:
  listen: 0.0.0.0:4000
  path: /admin/gql
health_check:
  listen: 0.0.0.0:4000  # 같은 port 에 함께 listen 가능
  path: /health
  enabled: true
```
webserver config 의 `[apollo_router] enabled = true` + `endpoint = "http://bai-router-backend-ai-apollo-router..."` + `health_check_probe_path = "/health"`.

### 6.2 webserver 의 CORS assertion 충돌

**문제**: webserver 가 router 응답을 받으면 `AssertionError: hdrs.ACCESS_CONTROL_ALLOW_ORIGIN not in response.headers`.

**원인**: router 가 CORS header 추가 + webserver 의 aiohttp_cors 미들웨어가 또 추가 = duplicate.

**해결**: router config 의 `cors:` 섹션 제거 (webserver 가 cors 책임).

---

## 7. App-Proxy (외부 접근)

### 7.1 manager → coordinator 인증 401

**문제**: manager log 에 `Unauthorized access`, coordinator log 에 `Credential/signature mismatch`.

**원인**: manager 가 보낸 `X-BackendAI-Token` 헤더 (scaling_groups.wsproxy_api_token) 와 coordinator 의 `secrets.api_secret` 값을 맞췄음에도 401. 명확한 원인 미파악 (manager 캐싱 또는 인증 로직 분기).

**해결 (임시)**: coordinator config 에 `allow_unauthorized_configure_request = true` — dev 환경용.

### 7.2 worker URL 이 cluster 내부 DNS

**문제**: UI 가 받은 URL 이 `http://bai-appproxy-worker-...svc.cluster.local:10201` → browser 가 resolve 못 함, "Failed to fetch".

**해결**: worker 를 `hostNetwork: true` + `advertised_host: "192.168.0.156"` + `[proxy_worker.port_proxy] advertised_host = "192.168.0.156"`.

### 7.3 coordinator advertise URL 도 cluster 내부

**문제**: manager 가 coordinator 의 `/status` 응답 받아서 `advertise_address` 를 client 에게 전달. 그 값이 `http://0.0.0.0:10200`.

**원인**: `proxy_coordinator.advertised_addr` 와 `proxy_coordinator.announce_addr` 가 **다른 옵션**. 우리는 announce_addr (service-discovery 용) 만 set 하고, **advertised_addr (client/worker 가 보는 URL)** 안 했음. fallback = bind_addr (0.0.0.0).

**해결**: `advertised_addr = { host = "192.168.0.156", port = 30201 }` 추가.

### 7.4 cross-origin fetch — CORS preflight 실패

**문제**: webserver UI (`:30890`) 에서 coordinator (`:30200`) 직접 fetch → browser preflight (OPTIONS) → coordinator 가 `405 Method Not Allowed`.

**원인**: coordinator 의 aiohttp_cors 설정이 `/v2/proxy/*` 같은 path 의 OPTIONS 안 받음.

**해결**: nginx reverse proxy (`coordinator-proxy`) 를 coordinator 앞단에 두고 CORS preflight 처리:
```nginx
location / {
  if ($request_method = OPTIONS) {
    add_header 'Access-Control-Allow-Origin' '*';
    add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, PATCH, OPTIONS';
    ...
    return 204;
  }
  proxy_hide_header 'Access-Control-Allow-Origin';  # coordinator 가 추가하는 거 hide
  add_header 'Access-Control-Allow-Origin' '*' always;
  proxy_pass http://coordinator-service:10200;
}
```
NodePort 30201 로 노출 + DB 의 `wsproxy_addr` 와 coordinator 의 `advertised_addr` 둘 다 nginx URL 로.

### 7.5 CORS header 중복 — 200 OK 인데 browser 가 차단

**문제**: nginx 통과 후 응답 200 OK 인데 browser inspector 에서 에러.

**원인**: 응답에 `Access-Control-Allow-Origin: *` 가 두 번 (nginx + coordinator).

**해결**: nginx 의 `proxy_hide_header` 로 coordinator 의 CORS 헤더 숨기고 nginx 만 추가.

### 7.6 worker port_proxy.advertised_host 누락

**문제**: 위 6.x 다 해결 후 다음 URL `http://0.0.0.0:10301/` — worker port_proxy 의 advertise.

**원인**: `proxy_worker.port_proxy.advertised_host` 가 별도 옵션. set 안 함.

**해결**: worker config 에 추가:
```toml
[proxy_worker.port_proxy]
bind_host = "0.0.0.0"
advertised_host = "192.168.0.156"
bind_port_range = [10301, 10400]
```

---

## 8. Storage / vfolder

### 8.1 manager 의 vfs-storage list 가 빈 결과

**증상**: `./bai vfs-storage list-all` = `[]`.

**원인**: manager DB 의 storage entry 가 빈 상태. agent log 에 `assuming use of storage-proxy since vfolder mount path is not configured in etcd`.

**현재 상태**: storage-proxy 자체는 정상 (service-discovery 등록, `/vfroot/volume1` 발견), etcd 에 proxy info 도 자동 등록 (`/sorna/local/volumes/proxies/proxy1`). 다만 manager DB 의 vfs-storage 등록은 추가 fixture 작업 필요 (vfolder 동작 자체에는 4.5 의 keypair_resource_policies 갱신으로 충분).

### 8.2 NFS 구조 — 실제 storage 위치

```
/vfroot (ser8 호스트)
  └─ NFS mount: 192.168.0.156:/  (nfs4)
                                  ↑
                                  bai-nfs 컨테이너 (호스트 docker 안의 nfs-server-alpine)

storage-proxy pod
  └─ hostPath: /vfroot  → 호스트의 NFS mount 그대로
       └─ /vfroot/volume1/<user_uuid>/  ← vfolder 데이터
```

SPoF: ser8 의 `bai-nfs` 컨테이너 단일. 죽으면 전체 vfolder I/O 중단.

---

## 9. 외부 노출 / NodePort 매핑

| 컴포넌트 | 노출 | 용도 |
|---|---|---|
| webserver | NodePort 30890 → 8090 | 사용자 UI |
| coordinator (nginx) | NodePort 30201 → nginx 8080 → coordinator 10200 | App proxy URL (CORS proxy 경유) |
| appproxy-worker | hostNetwork (ser8), 10201 + 10301-10400 | 실제 traffic proxy |
| manager | (port-forward) 18081 → 8081 | dev CLI 용 (`./bai`) |

---

## 10. Multi-node — 알려진 결손

검증한 건 **사실상 ser8 단일 노드**. charsyam-nvidia 의 agent-gpu pod 는 떠 있지만 실제 GPU session 시도 시 첫 단계부터 fail.

### 10.1 첫 fail point — 노드의 docker daemon 정지

`agent_list: ["i-charsyam-nvidia"]` 로 session 강제 schedule 시 agent log:
```
DockerError(900, 'Cannot connect to Docker Engine via unix:///run/docker.sock')
```

DooD 가정 — 모든 worker 노드에 별도 docker daemon 필요. k8s 자체는 containerd 만으로 동작하지만 backend.ai 의 docker-backend agent 는 호스트 docker daemon 사용. charsyam-nvidia 에 docker 는 설치되어 있지만 service 가 stopped 상태였음.

**파생 문제 1 — daemon.json JSON syntax 깨짐**: 사용자가 안내대로 heredoc 으로 `/etc/docker/daemon.json` 만들 때 zsh 의 quote 처리 차이로 invalid character. docker.service 가 시작 시 daemon.json parse 실패로 즉시 exit. `'EOF'` (single-quote) 형식 또는 직접 편집기 사용.

**파생 문제 2 — agent pod 가 stale socket FD**: docker daemon 다시 시작 후에도 agent pod 가 옛 socket FD 사용해서 connection refused 지속. **agent pod 재시작** 필요 (`kubectl delete pod ...`). 그 다음 session schedule 정상.

검증 결과: 위 두 단계 처리 후 charsyam-nvidia 로 session 3개 schedule 됐고 모두 **RUNNING**.

### 10.2 새 worker 노드 추가 시 체크리스트

| 항목 | 명령 |
|---|---|
| docker daemon | `sudo apt install docker-ce` + `sudo systemctl enable --now docker` |
| insecure-registries | `/etc/docker/daemon.json` 의 `insecure-registries` 에 사설 registry + `restart docker` |
| containerd hosts.toml | `/etc/containerd/certs.d/<registry>/hosts.toml` |
| containerd 2.x | `[plugins."io.containerd.transfer.v1.local"]` 의 `config_path` |
| NFS mount | `/etc/fstab` 에 `192.168.0.156:/ /vfroot nfs4 ...` 또는 수동 mount |
| kernel image cache | (선택) `docker pull 192.168.0.156:5000/stable/python:...` 미리 |
| (GPU 노드) nvidia-container-runtime | `runtimeClassName: nvidia` 사용 시 |
| app-proxy worker | 노드별 advertised_host 다르므로 노드마다 별도 helm release 또는 DaemonSet 화 |

### 10.3 manager 의 ser8 고정 — 진짜 이유는 swarm leader

**Single-node session (`cluster_size = 1`)** 의 경우:
- kernel container 가 per-node `bridge` network (172.17.x.x) 사용
- 노드 간 직접 통신 없음, host port publish 만
- backend.ai 가 swarm api 안 씀
- 즉 swarm 없어도 single-node session 은 동작

**Multi-node session (`cluster_size > 1`)** 의 경우:
- `src/ai/backend/manager/network/overlay.py` 가 docker swarm overlay network 사용
- manager 가 직접 `docker.networks.create({"Driver": "overlay", "Attachable": True})` 호출
- Overlay network 는 docker swarm **manager(leader)** 만 create 가능
- swarm 미초기화 시 명시적 에러: `"Docker Swarm is not enabled on this system. ... 'docker swarm init'"`

**결론**: backend.ai 의 multi-node session 은 **manager 가 swarm leader 노드의 docker daemon 에 접근 가능해야** 함. 즉 우리 환경의 `values-local.yaml: nodeSelector: ser8` 는 우연이 아니라 **multi-node session 의 명시적 요구사항**.

`backendai.io/dedicated=swarm-manager` taint 도 운영자가 manager pod 를 swarm leader 노드에 묶기 위한 의도된 label.

### 10.3.1 Multi-node kernel 통신 메커니즘

- Single-node session: kernel 의 service port → host port publish → app-proxy worker 가 `<agent_node_ip>:<host_port>` 로 traffic forwarding
- Multi-node session: manager 가 swarm overlay network 1개 create (`Attachable: True`) → 두 노드 agent 가 자기 docker daemon 의 kernel container 를 그 overlay 에 join → 같은 L2 network 라 kernel 간 직접 IP 통신 가능

후자 때문에 manager **반드시 swarm leader 노드**.

### 10.4 NFS multi-node 마운트

storage-proxy 가 `/vfroot` hostPath 마운트. 그게 NFS mount 라서 NFS client 가 깔린 노드면 같은 데이터 공유. ser8 의 호스트는 자기 docker container (`bai-nfs`) 를 자기 자신이 `192.168.0.156:/` 로 nfs4 mount.

다른 노드에서 같은 NFS server 를 mount 하면 multi-node 에서 vfolder 공유 가능. 단 NFS server (ser8 docker container) 가 SPoF.

### 10.5 app-proxy worker — 노드별 다른 advertised_host

worker 가 hostNetwork + `port_proxy.advertised_host = "192.168.0.156"` 로 hardcode. 다른 노드에서 띄우면 그 노드 IP 로 advertised_host 달라야. helm chart 의 values 를 노드별 다르게 release 하거나, DaemonSet + downward API 로 nodeIP 주입.

### 10.6 Swarm leader 노드 장애 시 복구 옵션

ser8 가 swarm leader + manager + storage + registry 다 갖고 있어서 장애 시 영향 큼. 옵션:

**옵션 1: Swarm HA** — swarm manager 를 3개 이상 (raft quorum). manager pod 의 nodeSelector 대신 affinity 로 "swarm-manager label 의 노드 중 어디든". swarm raft 가 자동 leader election → k8s 가 manager pod reschedule. 추가로 storage / registry / NFS 도 HA 필요.

**옵션 2: Multi-node session 포기** — `cluster_size = 1` 만 사용. manager 위치 자유. 가장 단순. Jupyter / vscode 같은 single-kernel 워크로드만 쓰면 충분.

**옵션 3: Remote docker daemon** — swarm leader 의 docker daemon 을 `tcp://leader:2376` + TLS 로 노출, manager 가 `DOCKER_HOST` env 로 원격 접근. leader 바뀌면 endpoint 추적 필요 (leader-aware proxy 또는 dns 갱신). 보안 risk 증가.

**옵션 4 (근본): Backend 교체** — containerd-backend (native API + cilium CNI) 또는 k8s-backend (kernel 이 k8s Pod) 로 마이그레이션. swarm 의존 제거. 작업량 가장 큼. backend.ai 의 장기 방향이기도 함 — 이 브랜치 (`docs/dood2`) 의 docker-backend 정리 다음 단계.

**옵션 5 (이 브랜치에서 구현/검증함): RPC 분리** — 다음 11 section.

---

## 11. Swarm overlay network 책임 분리 (RPC plugin)

`옵션 5` 의 실제 구현. manager 의 swarm-leader 의존성을 별도 daemon 으로 추출.

### 11.1 구조

```
[manager pod — 어디든]              [swarm-network-daemon — swarm-manager 라벨 노드만]
─────────────────                   ─────────────────────────
manager                              hostPath: /var/run/docker.sock
 │ RpcOverlayNetworkPlugin           │
 │   create_network() ──HTTP RPC────►│ POST /networks → docker.networks.create(Driver=overlay)
 │   destroy_network() ──────────────►│ DELETE /networks/{name} → network.delete()
 │                                   │ 인증: X-Auth-Token (shared bearer)
 └─ 호스트 docker.sock 접근 불필요    └─ swarm api 호출 (overlay create 는 swarm manager 만 가능)
```

### 11.2 변경 파일

| 파일 | 역할 |
|---|---|
| `src/ai/backend/manager/network/rpc.py` | 새 plugin (`RpcOverlayNetworkPlugin`), HTTP client only |
| `src/ai/backend/manager/BUILD` | entry-point 추가 (`rpc_overlay`) |
| `deploy/helm/backend-ai-swarm-network-daemon/` | 새 chart (single-file Python aiohttp daemon, ConfigMap 으로 ship) |
| `deploy/helm/backend-ai-swarm-network-daemon/files/daemon.py` | daemon 본체 — aiohttp + aiodocker, hostPath docker.sock |
| `deploy/helm/backend-ai-manager/templates/configmap-manager-toml.yaml` | `[network.inter-container] default-driver = "rpc_overlay"` |
| `deploy/helm/values-local.yaml` | manager nodeSelector 를 `backendai.io/dedicated=swarm-manager` label 기반으로 (host-fixed 아닌) |

### 11.3 plugin config (etcd)

`config/plugins/network_manager/rpc_overlay/` 아래:
- `endpoint` = `http://bai-swarm-net-backend-ai-swarm-network-daemon.backend-ai.svc.cluster.local:7700`
- `auth_token` = shared bearer

설정 명령:
```bash
kubectl exec bai-etcd-0 -- etcdctl put \
  /sorna/local/config/plugins/network_manager/rpc_overlay/endpoint \
  "http://bai-swarm-net-backend-ai-swarm-network-daemon.backend-ai.svc.cluster.local:7700"
kubectl exec bai-etcd-0 -- etcdctl put \
  /sorna/local/config/plugins/network_manager/rpc_overlay/auth_token \
  "CHANGE-ME-SWARM-NETWORK-TOKEN"
```

### 11.4 검증 결과 (2026-05-26)

**1단계 — 동일 노드** (ser8 에 둘 다):
```
a1f8cce2-... multinode-cluster-1 RUNNING mode=MULTI_NODE size=2
docker network ls → bai-multinode-a1f8cce2-... overlay swarm
```

**2단계 — 분리 검증** (manager 와 daemon 다른 노드):
```bash
# 두 번째 노드에 swarm-manager 라벨 추가
$ kubectl label node charsyam-nvidia backendai.io/dedicated=swarm-manager

# ser8 cordon → manager pod 강제 다른 노드 schedule
$ kubectl cordon ser8
$ kubectl delete pod -n backend-ai -l app.kubernetes.io/name=backend-ai-manager

# 결과
$ kubectl get pod -n backend-ai -o wide | grep -E "manager-|swarm-net"
bai-backend-ai-manager-7b86cf7bc9-fwktc       1/1 Running  charsyam-nvidia   # ← swarm WORKER 노드
bai-swarm-net-...-24pvl                       1/1 Running  ser8              # ← swarm leader 노드

# manager 가 swarm worker 노드에서 multi-node session 정상 처리
$ ./bai session enqueue @multi-cluster.json
$ ./bai admin session search
a710f590-... multinode-cluster-2 RUNNING mode=MULTI_NODE size=2
```

- 진짜 분리 성공: manager 위치가 swarm leader 와 무관해도 동작
- ser8 죽어도 daemon 만 다른 swarm-manager 라벨 노드로 reschedule, manager 영향 없음
- swarm overlay network 정상 생성, multi-node kernel 두 개가 같은 overlay 에 attach

### 11.5 HA 시나리오

| 시나리오 | 동작 |
|---|---|
| ser8 (현재 swarm leader + daemon) 죽음 | swarm 의 raft 가 다른 swarm-manager 노드를 leader 로 election. daemon pod 도 k8s 가 swarm-manager 라벨 노드로 reschedule. manager 는 영향 없음 (k8s service DNS 가 새 pod 으로 자동 routing). |
| manager pod 죽음 | k8s 가 swarm-manager 라벨 노드 중 어디든 reschedule (현재는 ser8 뿐이지만 라벨 추가하면 즉시 확장). daemon endpoint 는 service DNS 라 변경 없음. |
| daemon pod 죽음 | k8s 가 같은 노드 또는 다른 swarm-manager 라벨 노드에 새 pod. manager 의 plugin client 가 HTTP 재시도. |

### 11.6 trade-off

- **장점**: manager HA 가능, manager 가 stateless service 처럼 동작.
- **추가 컴포넌트**: 1개 (daemon pod). 작은 single-file 서비스라 운영 부담 작음.
- **인증**: shared bearer token. mTLS 또는 k8s ServiceAccount JWT 로 강화 가능 (현재 미구현).
- **MTU / 추가 옵션**: 현재 plugin config 는 endpoint + token 만. mtu 같은 옵션은 daemon env 또는 daemon config 로 (manager 의 옛 overlay plugin 의 mtu 옵션 호환은 추후 작업).

---

## 12. scaling 평가

| 컴포넌트 | scaling |
|---|---|
| agent | ✅ DaemonSet — 노드 추가 = agent 자동 추가 |
| kernel | ✅ scheduler 가 agent 들 사이 분산 |
| manager / coordinator | ⚠️ valkey leader election 존재, 다중 시험 안 됨 |
| webserver / apollo-router | ✅ stateless replica |
| **appproxy-worker** | ❌ hostNetwork + 외부 advertised_host 라 노드별 1개 |
| **storage-proxy / bai-nfs** | ❌ SPoF |
| postgres / redis / etcd | ❌ stateful, 단일 replica |

새 worker 노드 추가 시 수동 작업 (containerd config + docker daemon insecure-registries + restart) 가 자동화 안 됨 — DaemonSet init container 로 묶을 수 있지만 미구현.

---

## 부록 — 자주 쓴 디버그 명령

```bash
# 컴포넌트 상태
kubectl get pod -n backend-ai
helm list -n backend-ai

# manager / coordinator / worker 로그
kubectl logs -n backend-ai -l app.kubernetes.io/component=manager --tail=50
kubectl logs -n backend-ai -l app.kubernetes.io/name=backend-ai-appproxy-coordinator --tail=50
kubectl logs -n backend-ai -l app.kubernetes.io/name=backend-ai-appproxy-worker --tail=50

# etcd
kubectl exec bai-etcd-0 -- etcdctl get --prefix /sorna/local

# postgres
kubectl exec bai-postgres-0 -- psql -U backendai -d backendai -c "SELECT ..."

# fixture populate
kubectl cp <local>.json backend-ai/<manager-pod>:/tmp/x.json
kubectl exec <manager-pod> -- backend.ai mgr -c /etc/backend.ai/manager.toml fixture populate /tmp/x.json

# alembic upgrade head (manager)
kubectl exec <manager-pod> -- /opt/backend.ai/venv/bin/alembic -c /etc/backend.ai/alembic.ini upgrade head

# 사설 registry 상태
curl http://192.168.0.156:5000/v2/_catalog

# coordinator status (advertise_address 확인)
curl http://192.168.0.156:30201/status
```
