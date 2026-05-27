# Backend.AI k8s-control-plane-and-native-agent 설치 매뉴얼

`k8s-control-plane-and-native-agent` 시나리오: control plane (manager / storage-proxy / webserver / appproxy / apollo-router / 부수 etcd·redis·postgres) 는 모두 **k8s** 위에 helm umbrella chart 로 설치하고, **agent 만 호스트의 docker container** 로 띄움.

관련 문서:
- `docs/k8s-control-plane-and-native-agent-diff.md` — dood2 대비 변경 / 알려진 이슈 I-1~I-5
- `docs/k8s-control-plane-and-native-agent-host.md` — agent 호스트 셋업 디테일 (이 문서의 §4 와 중복)

## 0. 사전 조건

| 항목 | 비고 |
|---|---|
| k8s 클러스터 | 1 노드 이상. 본 가이드는 `ser8` (192.168.0.156) 를 swarm-manager 노드로 가정 |
| helm 3.x | `helm version` 으로 확인 |
| Docker Swarm | swarm-manager 가 k8s 클러스터의 한 노드에 있어야 함. swarm 가입은 §4 에서 |
| 사설 docker registry | 본 가이드는 `192.168.0.156:5000` 가정 (HTTP, insecure). 사내 Harbor 등도 가능 — chart values 에서 image.repository 만 갈아끼우면 됨 |
| NFS 서버 | `/vfroot` 공유. 본 가이드는 `192.168.0.156:/` 가정 |
| 컴포넌트 이미지들 | 사설 registry 에 5 개 image (`backend.ai-manager / agent / storage-proxy / appproxy / webserver`, 모두 `:dev` 태그) push 돼 있어야 함. **없다면 §0.1 참조** |

### 노드 라벨 / taint (한 번만)

control plane 컴포넌트들이 swarm-manager 노드에 pin 되도록:
```bash
kubectl label  node ser8 backendai.io/dedicated=swarm-manager --overwrite
kubectl taint  node ser8 backendai.io/dedicated=swarm-manager:NoSchedule --overwrite

# 확인
kubectl describe node ser8 | grep -E "Taints|backendai.io"
```

## 0.1. 컴포넌트 이미지 빌드 + 푸시 (registry 에 없으면 1 회)

`k8s-control-plane-and-native-agent` 의 helm chart 는 사설 registry 에 backend.ai image 5 종 (`manager / agent / storage-proxy / appproxy / webserver`, 모두 `:dev` 태그) 이 있다고 가정합니다. main 에 머지되기 전이라 공개 image 가 없고 — 이 repo 의 `docker/` 아래 Dockerfile 들로 직접 빌드해야 합니다.

**전체 빌드 절차는 별도 문서로 분리됨 → [`docs/build-images.md`](./build-images.md)**.

핵심만 요약:

```bash
# 1) LFS 자산 동기화 (agent 빌드의 silent failure 방지)
git lfs install && git lfs pull

# 2) 신형 (manager / agent / storage-proxy)
docker build -f docker/manager/Dockerfile        -t backend.ai-manager:dev        .
docker build -f docker/agent/Dockerfile          -t backend.ai-agent:dev          .
docker build -f docker/storage-proxy/Dockerfile  -t backend.ai-storage-proxy:dev  .

# 3) 구형 (appproxy / webserver) — pants 로 wheel 먼저 빌드 후 docker build
./scripts/build-wheels.sh
PKGVER=$(./py -c "import packaging.version,pathlib; print(str(packaging.version.Version(pathlib.Path('VERSION').read_text())))")
docker build -f docker/backend.ai-appproxy-coordinator.dockerfile \
  --build-arg PYTHON_VERSION=3.13-slim --build-arg PKGVER=$PKGVER \
  -t backend.ai-appproxy:dev .
docker build -f docker/backend.ai-webserver.dockerfile \
  --build-arg PYTHON_VERSION=3.13-slim --build-arg PKGVER=$PKGVER \
  -t backend.ai-webserver:dev .

# 4) 사설 registry (예: 192.168.0.156:5000) 로 tag + push
REG=192.168.0.156:5000
for img in backend.ai-{manager,agent,storage-proxy,appproxy,webserver}; do
  docker tag $img:dev $REG/$img:dev && docker push $REG/$img:dev
done
```

> appproxy 는 coordinator/worker 양쪽이 같은 image 를 씁니다 (entrypoint 인자만 다름).
>
> air-gapped 환경, kernel image mirror, troubleshooting, Dockerfile 스타일 차이 (신형 vs 구형) 등 상세는 [`build-images.md`](./build-images.md) 참조.

## 1. k8s control plane 설치 (umbrella helm chart)

### 1-1. sub-chart 패키징

umbrella chart 가 7 개 sub-chart 를 `file://` 로 참조하므로 한 번 packing 필요:
```bash
helm dependency update deploy/helm/backend-ai
ls deploy/helm/backend-ai/charts/
# backend-ai-manager-0.2.0.tgz, backend-ai-storage-proxy-0.1.0.tgz, ... 7개
```

### 1-2. install

```bash
helm install bai deploy/helm/backend-ai \
  -n backend-ai --create-namespace \
  -f deploy/helm/backend-ai/values-local.yaml
```

> ⚠️ **`--wait` 옵션 절대 사용하지 말 것** — Helm 3 의 `--wait` 는 *비-hook 리소스 (Deployment/StatefulSet) ready → post-install hook 실행* 순서로 동작. 본 chart 는 manager / appproxy-coordinator Deployment 가 `wait-for-schema` / `wait-for-appproxy-schema` initContainer 로 post-install hook Job (schema-migrate, db-init) 완료를 기다리는 구조 → `--wait` 시 **circular dependency 로 영구 deadlock**. 그냥 `helm install` 로 즉시 반환받고, post-install hook 들 (synchronous) 이 알아서 끝남.

> **release name 은 반드시 `bai`** — sub-chart 들이 manager 가 만든 service 명 (`bai-etcd`, `bai-redis`, `bai-postgres`, `bai-backend-ai-manager`, …) 을 가정한 cross-reference 가 있어서, 다른 name 으로 install 시 webserver 의 redis / apollo-router 연결이 깨짐.

### 1-3. 설치 진행 순서 (helm 이 자동으로 처리)

| weight | 리소스 | 비고 |
|---|---|---|
| - | Secret / ConfigMap | manager / 각 서비스 |
| - | StatefulSet etcd / postgres / redis | manager chart 의 deps.yaml |
| post-install 0 | Job `bai-backend-ai-manager-schema-migrate` | `alembic upgrade head` (manager DB) |
| post-install 1 | Job `bai-backend-ai-manager-etcd-seed` | 글로벌 config + storage-proxy 등록 |
| post-install 2 | Job `bai-backend-ai-manager-fixture-populate` | 기본 user / group / **default scaling-group** |
| post-install 3 | Job `bai-backend-ai-appproxy-coordinator-db-init` | `appproxy` DB 생성 + alembic + `scaling_groups.default.wsproxy_*` 갱신 |
| - | Deployment manager / storage-proxy / webserver / appproxy / apollo-router | 위 Job 완료 후 살아남 |

> 📌 **storage-proxy / webserver / appproxy-worker 의 초기 CrashLoop (RESTARTS 2~3) 는 정상** — 이들은 hook 아닌 Deployment 라 즉시 시작되는데 etcd-seed (weight 1) 가 redis addr 키 를 etcd 에 박기 *전* 에 부팅 시도 → `RedisTarget must have an address` 등으로 fail → backoff 재시작. seed 완료 후 다음 restart 에서 self-heal. `kubectl get pod` 의 RESTARTS 카운트로만 흔적이 남고 STATUS 는 결국 Running 으로 안정화. 진짜 문제면 RESTARTS 가 5+ 로 계속 오름 — 그때만 로그 확인.

### 1-4. 검증

```bash
kubectl get pod -n backend-ai
# 모두 Ready / Completed 인지 확인

kubectl get svc -n backend-ai | grep NodePort
# bai-backend-ai-manager        NodePort  ...  8081:32081/TCP
# bai-etcd-external             NodePort  ...  2379:32379/TCP
# bai-redis-external            NodePort  ...  6379:32679/TCP
# bai-backend-ai-webserver      NodePort  ...  8090:30890/TCP
# bai-backend-ai-appproxy-coordinator  NodePort  ...  10200:30200/TCP

# manager API health
curl -sf http://192.168.0.156:32081/ && echo OK

# webserver UI
# 브라우저로 http://192.168.0.156:30890
```

## 2. agent 가 보는 redis 주소 (values 로 선언)

host 의 agent 는 cluster DNS 를 resolve 못 하므로 `bai-redis:6379` 가 아닌 외부 도달 가능한 주소 (NodePort / LB) 가 필요합니다. **`deploy/helm/backend-ai/values-local.yaml` 의 `manager.redisExternalAddr` 한 줄** 로 처리:

```yaml
backend-ai-manager:
  manager:
    redisExternalAddr: "192.168.0.156:32679"   # redis NodePort 와 일치
```

etcd-seed Job 이 매 install/upgrade 마다 이 값을 `config/redis/addr` 로 박아주므로:
- 사람이 `etcdctl put` 할 필요 없음
- helm upgrade 시 reset 되는 drift 없음
- IP 바뀌면 values 만 수정 후 `helm upgrade` — 끝

```bash
# 확인
kubectl exec -n backend-ai bai-etcd-0 -- etcdctl get /sorna/local/config/redis/addr
# /sorna/local/config/redis/addr
# 192.168.0.156:32679
```

값이 비어 있으면 (`redisExternalAddr: ""`) cluster DNS (`bai-redis:6379`) 가 seed 됨 — 순수 k8s-안-만 시나리오 와 backward compatible.

## 3. (옵션) 사설 image registry 등록

agent 가 어떤 registry 의 image 를 pull 할지 manager 가 알려주는 메타 — 이미 manager 가 default 로 docker hub 만 알고 있는 상태라면, Harbor 등을 추가 등록:

```bash
# 예: cr.backend.ai 형식의 lablup registry 또는 사내 Harbor
./bai admin etcd put config/docker/registry/cr.backend.ai/ "https://cr.backend.ai"
./bai admin etcd put config/docker/registry/cr.backend.ai/type docker
./bai admin etcd put config/docker/registry/cr.backend.ai/project stable
./bai admin etcd rescan-images cr.backend.ai
```

**클러스터 1회**. 호스트마다 할 일 아님.

## 4. agent 설치 (호스트별 반복)

각 worker 호스트에서 아래 4-1 ~ 4-5 를 수행. k8s-control-plane-and-native-agent 의 핵심: **agent 만 호스트, k8s 밖**.

### 4-1. 호스트 사전 준비

```bash
# docker (이미 있으면 skip)
sudo systemctl enable --now docker

# 사설 registry 신뢰 — agent 가 호스트 docker 로 kernel image pull
sudo tee /etc/docker/daemon.json > /dev/null <<'EOF'
{ "insecure-registries": ["192.168.0.156:5000"] }
EOF
sudo systemctl restart docker

# Harbor 등 credential 필요한 registry
docker login harbor.example.com -u <user> -p <pass>

# NFS mount — storage-proxy 와 같은 share 봐야 함
sudo mount -t nfs4 192.168.0.156:/ /vfroot
echo '192.168.0.156:/  /vfroot  nfs4  defaults,_netdev  0 0' | sudo tee -a /etc/fstab

# 방화벽
# - agent RPC 6001 (manager pod -> agent)
# - agent service 6003 (health / debug)
# - kernel container port range 30000-31000
sudo ufw allow 6001/tcp
sudo ufw allow 6003/tcp
sudo ufw allow 30000:31000/tcp
```

### 4-2. (multi-node session 사용 시) Docker Swarm join

```bash
# swarm-manager (ser8) 에서 token 발급
docker swarm join-token worker
# join 명령 복사

# worker 호스트에서
docker swarm join --token <SWARM-WORKER-TOKEN> 192.168.0.156:2377

# swarm-manager 에서 확인
docker node ls
```

multi-node session 안 쓰면 swarm join 불필요.

### 4-3. agent image 와 venv 준비

```bash
# image pull
docker pull 192.168.0.156:5000/backend.ai-agent:dev

# DooD path-equivalence 위해 venv 를 호스트로 복사
#   - agent 는 자기 venv 의 runner binary (su-exec, jail 등) 를 kernel container 에 bind mount
#   - kernel container 는 호스트 docker daemon 으로 띄워지므로 호스트에도 같은 path 가 있어야 함
sudo docker create --name temp-agent 192.168.0.156:5000/backend.ai-agent:dev
sudo docker cp temp-agent:/opt/backend.ai /opt/
sudo docker rm temp-agent
```

### 4-4. agent.toml 배치

`configs/agent/k8s-control-plane-and-native-agent.toml` 을 베이스로, **host IP 3 군데만** 갈아끼움:

| 필드 | 값 | 비고 |
|---|---|---|
| `[agent] advertised-rpc-addr.host` | **이 호스트 IP** | manager pod 가 콜백할 주소 |
| `[agent] public-host` | **이 호스트 IP** | 동일 |
| `[container] advertised-host` | **이 호스트 IP** | kernel container 외부 노출 IP |
| `[etcd] addr.host` | `192.168.0.156` | 모든 호스트 동일 (k8s NodePort entry IP) |
| `[etcd] addr.port` | `32379` | 모든 호스트 동일 |

```bash
# 예: 호스트 IP 가 192.168.0.104 인 노드
sed -e 's|host = "192.168.0.156", port = 6001|host = "192.168.0.104", port = 6001|' \
    -e 's|public-host = "192.168.0.156"|public-host = "192.168.0.104"|' \
    -e 's|advertised-host = "192.168.0.156"|advertised-host = "192.168.0.104"|' \
    configs/agent/k8s-control-plane-and-native-agent.toml | sudo tee /etc/backend.ai/agent.toml >/dev/null
```

(`[etcd]` 의 `192.168.0.156:32379` 는 그대로 — 모든 호스트가 같은 control plane 을 봄.)

### 4-5. agent container 기동

```bash
sudo mkdir -p /var/lib/backend.ai /tmp/backend.ai

sudo docker run -d --name backend-ai-agent \
  --restart=unless-stopped --net=host --pid=host \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /vfroot:/vfroot \
  -v /var/lib/backend.ai:/var/lib/backend.ai \
  -v /tmp/backend.ai:/tmp/backend.ai \
  -v /opt/backend.ai:/opt/backend.ai:ro \
  -v /etc/backend.ai/agent.toml:/etc/backend.ai/agent.toml:ro \
  192.168.0.156:5000/backend.ai-agent:dev \
  ag start-server --config /etc/backend.ai/agent.toml

# 로그 확인
docker logs -f backend-ai-agent
```

healthy 상태가 되면 manager 가 agent 를 등록.

## 5. 전체 검증

```bash
# agent 등록 확인 — 각 호스트가 자기 IP:6001 로 등록되어야
./bai admin agent search

# 결과 예:
# i-charsyam-nvidia  tcp://192.168.0.104:6001  ALIVE
# i-ser8             tcp://192.168.0.156:6001  ALIVE

# 세션 생성
./bai session create python --name test1

# kernel container 가 해당 agent 의 호스트 docker 위에 떠야 함
ssh <agent-host> "docker ps | grep kernel"
```

## 6. 노드 추가 절차 (요약)

agent 만 늘리는 거라 helm 작업 0:

```bash
# 새 호스트에서 §4 의 4-1 ~ 4-5 반복
# (host IP 만 다르게)
```

ansible / cloud-init 으로 자동화 권장.

## 7. Troubleshooting

자주 만나는 이슈는 `docs/k8s-control-plane-and-native-agent-diff.md` §발생한 이슈 (I-1 ~ I-5) 참조:

- **I-1**: agent RPC addr 가 0.0.0.0 으로 publish → `advertised-rpc-addr` 명시 누락
- **I-2**: agent 가 redis 연결 실패 → §2 의 etcd redis addr 덮어쓰기 누락
- **I-3**: socket-relay container path mismatch → 옛 `backendai-socket-relay.i-<host>` container 강제 삭제
- **I-4**: venv path-equivalence 깨짐 → §4-3 의 `/opt/backend.ai` 호스트 복사 누락
- **I-5**: `docker cp` 가 빈 디렉터리 → mount 없는 임시 container 에서 cp

## 8. 구성 다이어그램

```
┌───────────────────── k8s cluster (ser8 등) ─────────────────────┐
│                                                                 │
│  Deployment            StatefulSet         Job(post-install)    │
│  ─ manager              ─ etcd              ─ etcd-seed         │
│  ─ storage-proxy        ─ postgres          ─ schema-migrate    │
│  ─ webserver            ─ redis             ─ fixture-populate  │
│  ─ appproxy-coord                                               │
│  ─ appproxy-worker                                              │
│  ─ apollo-router                                                │
│  ─ (옵션) swarm-network-daemon                                  │
│                                                                 │
│       │ NodePort: 32081 (manager), 32379 (etcd),                │
│       │           32679 (redis),   30890 (webui),               │
│       │           30200 (appproxy)                              │
└───────┼─────────────────────────────────────────────────────────┘
        │
        │ host network
        ▼
┌──────────── host 1 (ser8) ────────────┐   ┌──── host N (worker) ────┐
│  docker container: backend-ai-agent   │   │  docker container: ...  │
│   ├─ --net=host --pid=host            │   │                         │
│   ├─ mount /var/run/docker.sock       │   │  (동일 구조)            │
│   ├─ mount /vfroot (NFS)              │   │                         │
│   ├─ mount /opt/backend.ai (venv)     │   │                         │
│   └─ ag start-server                  │   │                         │
│                                       │   │                         │
│  host docker daemon                   │   │  host docker daemon     │
│   ├─ kernel.python.xxxxx              │   │   ├─ kernel.python.yy   │
│   └─ kernel.python.yyyyy              │   │   └─ ...                │
└───────────────────────────────────────┘   └─────────────────────────┘
```
