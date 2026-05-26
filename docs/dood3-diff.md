# dood3 — agent on host (diff from dood2)

`dood3` 시나리오: backend.ai 의 다른 컴포넌트는 모두 k8s 위에서 그대로, **agent 만 호스트의 docker container** 로 (k8s 외) 띄움. dood2 의 agent DaemonSet 가정을 풀고, 노드 추가 시 helm 작업 없이 호스트 작업만으로 agent 를 늘릴 수 있게.

## dood2 와 차이 요약

| 항목 | dood2 | dood3 |
|---|---|---|
| agent | k8s DaemonSet pod | 호스트 docker container (`--net=host --pid=host`) |
| agent 가 보는 docker daemon | hostPath `/var/run/docker.sock` | 동일 (네트워크 모드만 host) |
| etcd / redis | cluster service DNS (`bai-etcd`, `bai-redis`) | NodePort (`192.168.0.156:32379`, `32679`) |
| manager API | ClusterIP | NodePort (`192.168.0.156:32081`) |
| etcd 의 `config/redis/addr` | `bai-redis:6379` (cluster DNS) | `192.168.0.156:32679` (NodePort) |
| 노드 추가 절차 | helm chart + label/affinity | 호스트 docker + NFS mount + agent container 실행 |
| agent.toml | helm template 으로 자동 생성 | `configs/agent/dood3.toml` template 으로 직접 배치 |
| agent advertised_rpc_addr | pod IP (자동) | `192.168.0.156:6001` (호스트 IP, 명시 필요) |

## 변경 / 추가된 파일

### 제거
- `deploy/helm/backend-ai-agent/` (chart 전체)
- `deploy/helm/values-agent-cpu.yaml`
- `deploy/helm/values-agent-gpu.yaml`

### 신규
- `configs/agent/dood3.toml` — 호스트 agent 의 reference toml
- `docs/dood_agent_host.md` — 호스트 setup 가이드
- `docs/dood3-diff.md` — 이 문서
- `deploy/helm/backend-ai-manager/templates/services-external.yaml` — etcd / redis NodePort service (옵션, `manager.exposeDepsAsNodePort` 로 게이트)

### 수정
- `deploy/helm/backend-ai-manager/templates/service.yaml` — `nodePort` 필드 conditional 지원
- `deploy/helm/values-local.yaml`:
  - `manager.service` 를 `NodePort` 로 (nodePort=32081)
  - `exposeDepsAsNodePort: true`, `etcdNodePort: 32379`, `redisNodePort: 32679`

## 발생한 이슈 (dood3 작업 중)

### I-1. agent RPC addr 가 0.0.0.0 로 publish

**증상**: `./bai admin agent search` 결과의 `network_info.addr` 가 `tcp://0.0.0.0:6001`. manager pod 가 그 주소로 RPC 호출 시도 → 자기 자신의 0.0.0.0 으로 해석되어 fail.

**원인**: agent.toml 에 `rpc-listen-addr = { host = "0.0.0.0", port = 6001 }` 만 있고 advertised 주소 미설정. agent 가 bind 주소를 그대로 publish.

**해결**: `[agent] advertised-rpc-addr = { host = "192.168.0.156", port = 6001 }` 명시. 호스트별로 IP 다르게.

### I-2. agent 의 redis 연결 실패 (cluster DNS resolve 불가)

**증상**: 호스트 agent 부팅 시 redis 연결 실패. etcd 의 `/sorna/local/config/redis/addr` 가 `bai-redis:6379` (cluster DNS) 라 호스트에서 resolve 안 됨.

**해결**: etcd 의 redis URL 을 NodePort 로 갱신.
```bash
kubectl exec bai-etcd-0 -- etcdctl put /sorna/local/config/redis/addr "192.168.0.156:32679"
```
이렇게 하면 cluster 내부 컴포넌트 (manager, storage-proxy) 도 NodePort 통해 redis 접근 — 한 번의 service 우회 hop 발생하지만 dev/lab 환경엔 무관.

### I-3. agent IPC socket path mismatch — 옛 socket-relay container 가 옛 path 가르킴

**증상**: kernel container 생성 시
```
DockerError(400, 'invalid mount config for type "bind": bind source path
  does not exist: /tmp/backend.ai/ipc/container/agent.i-ser8.sock')
```

**원인**: 옛 k8s pod agent 가 띄운 `backendai-socket-relay.i-ser8` container 가 호스트의 `/run/backend.ai/ipc/container` 를 mount 해서 거기 socket 만듦. 새 host agent 의 `ipc_base_path` default 는 `/tmp/backend.ai/ipc`. 두 path 불일치.

agent 의 `PersistentServiceContainer` 가 image 가 같으면 기존 container 재사용 — 옛 socket-relay 가 옛 path 그대로 유지됨.

**해결**: 옛 socket-relay container 강제 삭제 + agent restart → 새 path 로 재생성.
```bash
docker rm -f backendai-socket-relay.i-ser8
docker restart backend-ai-agent
```

### I-4. DooD path-equivalence 깨짐 — agent venv 가 호스트에 없음

**증상**: kernel container 생성 시
```
DockerError(400, 'invalid mount config for type "bind": bind source path
  does not exist: /opt/backend.ai/venv/lib/python3.13/site-packages/ai/backend/runner/su-exec.x86_64.bin')
```

**원인**: agent 가 자기 venv 의 runner binaries (su-exec, jail, etc.) 를 kernel container 에 bind mount. agent container 안에는 `/opt/backend.ai/venv/...` 존재하지만, kernel container 는 **호스트 docker daemon** 통해 띄워지므로 호스트에 같은 path 가 필요. agent 가 docker container 안에 있어서 호스트엔 그 venv 없음.

DooD pattern 의 핵심: agent 가 사용하는 모든 path 가 호스트의 같은 path 에 존재해야 함.

**해결**: agent image 의 `/opt/backend.ai` 를 호스트로 복사한 뒤 read-only bind mount.
```bash
docker create --name temp-agent backend.ai-agent:dev
docker cp temp-agent:/opt/backend.ai /opt/
docker rm temp-agent

# agent container 에 추가 mount
docker run ... -v /opt/backend.ai:/opt/backend.ai:ro ... backend.ai-agent:dev ...
```

진짜 정석은 호스트에 venv 를 직접 setup (pip / pants build) 하는 거지만, image 의 venv 를 그대로 mount 공유하는 게 작업량 작음.

### I-5. docker cp 의 순환 의존성

**증상**: `docker cp backend-ai-agent:/opt/backend.ai /opt/` 가 `1.54kB only` 만 복사 — 빈 디렉터리.

**원인**: 이미 `-v /opt/backend.ai:/opt/backend.ai` 마운트된 container 에서 cp 하면 container 안의 `/opt/backend.ai` = 호스트의 빈 path (mount 가 image 의 그 path 를 덮어쓴 상태). 그래서 cp 가 빈 데이터를 빈 path 로 복사.

**해결**: mount 없는 임시 container 에서 cp. 위 I-4 해결책의 `docker create` 단계가 이것.

## 검증 결과

```bash
$ docker ps --filter name=backend-ai-agent
backend-ai-agent  Up ...  k8s 외 host docker container

$ ./bai admin agent search
i-charsyam-nvidia tcp://192.168.0.104:6001
i-ser8 tcp://192.168.0.156:6001

$ ./bai session enqueue @dood3-session.json  # agent_list=[i-ser8]
$ ./bai admin session search
4af422a2-... dood3-test-5 PREPARED → RUNNING

$ docker ps | grep kernel
kernel.python.74a3d1c5-...  Up 46 seconds
kernel.python.c002c89d-...  Up 46 seconds
```

- agent 가 k8s 외에서 동작
- manager (k8s pod) ↔ agent (host docker) RPC 정상
- agent → host docker daemon 으로 kernel container 생성 정상

## 노드 추가 절차 (정리)

새 worker 노드에서:

```bash
# 1. docker daemon (이미 있다면 skip)
sudo systemctl enable --now docker

# 2. 사설 registry 신뢰
sudo tee /etc/docker/daemon.json > /dev/null <<'EOF'
{ "insecure-registries": ["192.168.0.156:5000"] }
EOF
sudo systemctl restart docker

# 3. (multi-node session 사용 시) swarm join
docker swarm join --token <worker-token> 192.168.0.156:2377

# 4. NFS mount
sudo mount -t nfs4 192.168.0.156:/ /vfroot

# 5. agent image pull
docker pull 192.168.0.156:5000/backend.ai-agent:dev
# (또는 ser8 에서 docker save | ssh node 'docker load')

# 6. venv 복사
sudo docker create --name temp-agent 192.168.0.156:5000/backend.ai-agent:dev
sudo docker cp temp-agent:/opt/backend.ai /opt/
sudo docker rm temp-agent

# 7. agent.toml (configs/agent/dood3.toml 기반, public-host / advertised-rpc-addr 만 노드 IP 로 갱신)
sudo install -m 0644 dood3.toml /etc/backend.ai/agent.toml

# 8. agent container
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
```

k8s 작업 0. helm chart 변경 0. agent 의 lifecycle 은 호스트 docker (restart=unless-stopped) 가 관리.

## 한계

- agent OS-level lifecycle (rolling restart, log aggregation, healthcheck alerting) 가 k8s 가 아닌 호스트 docker restart policy 의 책임.
- 노드별로 host 작업이 많음 — ansible / cloud-init 으로 자동화 권장.
- swarm overlay 의존 (multi-node session 사용 시) 은 dood2 의 `swarm-network-daemon` 분리 그대로 적용 가능. agent 가 host docker container 형태라도 같은 docker engine 이라 overlay attach 정상 동작.
- 진짜 host process (docker container 아닌 systemd) 로 띄우려면 호스트에 venv 직접 setup. 현재 가이드는 host docker container 까지만 — k8s 외 라는 dood3 의도 충족하면서 작업량 최소.
