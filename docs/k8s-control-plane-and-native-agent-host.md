# Backend.AI agent on host (k8s-control-plane-and-native-agent)

`k8s-control-plane-and-native-agent` 시나리오: backend.ai 의 다른 컴포넌트 (manager, storage-proxy, webserver, apollo-router, appproxy, swarm-network-daemon) 는 k8s 위에 그대로 돌리되, **agent 만 호스트의 일반 process 로** 띄움.

차이 — `dood2` 와 비교:

| 항목 | dood2 | k8s-control-plane-and-native-agent |
|---|---|---|
| agent | k8s DaemonSet pod | host systemd/process |
| `/var/run/docker.sock` | pod hostPath mount | agent 가 직접 사용 |
| etcd / redis 접근 | cluster DNS | **NodePort** |
| manager API 접근 | cluster DNS | NodePort |
| agent 노드 추가 | k8s 노드 추가 + agent label | 그냥 도커 깔린 호스트 + agent process |

## 사전 준비 (각 호스트)

| # | 항목 | 명령 |
|---|---|---|
| 1 | docker daemon | `sudo apt install docker-ce && sudo systemctl enable --now docker` |
| 2 | docker insecure-registries | `/etc/docker/daemon.json` 에 사설 registry 추가 + `systemctl restart docker` |
| 3 | NFS mount | `sudo mount -t nfs4 192.168.0.156:/ /vfroot` (or `/etc/fstab`) |
| 4 | host firewall | agent RPC 6001, service 6003, container port-range 30000-31000 open |
| 5 | python 3.13 + venv | backend.ai-agent wheel 설치용 |

## etcd / redis NodePort 활성화

manager helm chart 의 values 에 (이미 `k8s-control-plane-and-native-agent` 의 values-local.yaml 에 적용됨):
```yaml
manager:
  service:
    type: NodePort
    port: 8081
    nodePort: 32081
  exposeDepsAsNodePort: true
  etcdNodePort: 32379
  redisNodePort: 32679
```

추가로 **etcd 안의 redis URL** 도 NodePort 로 갱신해야 (default 는 `bai-redis:6379` 라 호스트에서 resolve 불가):
```bash
kubectl exec -n backend-ai bai-etcd-0 -- etcdctl \
  put /sorna/local/config/redis/addr "192.168.0.156:32679"
```

## agent 설치 (호스트)

### 1. backend.ai-agent wheel 빌드 / 설치

소스 트리에서:
```bash
pants package src/ai/backend/agent:dist
# 결과: dist/backend_ai_agent-*.whl
```

호스트의 venv 에:
```bash
python3.13 -m venv /opt/backend.ai/venv
/opt/backend.ai/venv/bin/pip install dist/backend_ai_agent-*.whl \
    dist/backend_ai_cli-*.whl dist/backend_ai_common-*.whl \
    dist/backend_ai_logging-*.whl dist/backend_ai_plugin-*.whl
```

또는 pre-built `backend.ai-agent:dev` docker image 의 `/opt/backend.ai/venv` 를 꺼내서 사용.

### 2. agent.toml

template: `configs/agent/k8s-control-plane-and-native-agent.toml`. 핵심:
- `[etcd] addr = { host = "192.168.0.156", port = 32379 }`
- `[agent] rpc-listen-addr = { host = "0.0.0.0", port = 6001 }`
- `[agent] public-host = "<this-host-ip>"`
- `[container] advertised-host = "<this-host-ip>"`, `scratch-root = "/var/lib/backend.ai/scratches"`
- `[agent] scaling-group = "default"` (matches the manager-side scaling group)

호스트 별로 `public-host`, `advertised-host` 갈아끼움.

### 3. systemd unit

`/etc/systemd/system/backend-ai-agent.service`:
```ini
[Unit]
Description=Backend.AI Agent
After=docker.service network.target
Requires=docker.service

[Service]
Type=simple
User=root
Environment=BACKEND_CONFIG_PATH=/etc/backend.ai/agent.toml
ExecStart=/opt/backend.ai/venv/bin/backend.ai ag start-server --config /etc/backend.ai/agent.toml
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now backend-ai-agent
sudo journalctl -fu backend-ai-agent
```

### 4. 검증

호스트의 agent process 가 etcd 에 등록되고 manager 가 발견하는지:
```bash
# host 에서
sudo journalctl -u backend-ai-agent -n 30 --no-pager | grep -E "rpc|service-discovery|registered"

# k8s 쪽에서
./bai admin agent search --limit 5
# i-<hostname>  tcp://<host-ip>:6001  default
```

kernel 부팅 검증:
```bash
./bai session enqueue @<payload>.json  # cluster_size = 1
# 호스트의 docker 에 kernel.python.* container 떠야 함
docker ps | grep kernel
```

multi-node session (cluster_size > 1) 도 가능 — agent 가 호스트 process 라도 swarm-network-daemon 통해 overlay attach 됨.

## 노드 추가 시

1–5 의 사전 준비 + agent install + systemd 만 반복. helm uninstall / install 같은 k8s 작업 0.

## 한계

- agent 의 OS-level lifecycle 관리가 k8s 가 아닌 운영자 몫 (rolling restart, log aggregation, healthcheck alerting)
- 새 agent 노드 추가 시 manual 작업이 많음 — ansible / cloud-init 으로 자동화 권장
- NFS mount 가 노드별로 필요 — `/etc/fstab` 또는 autofs
- swarm join (multi-node session 사용 시) — agent 노드도 swarm worker 로 join 해야 overlay attach 가능
