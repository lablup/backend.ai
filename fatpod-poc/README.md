# fatPod PoC — Backend.AI 컨트롤 플레인 on k8s + fatPod 에이전트

Backend.AI를 k8s 위에서 돌리는 PoC. 컨트롤 플레인(manager/postgres/valkey/etcd)을 전부 k8s pod로
올리고, 에이전트를 **privileged fatPod**로 띄워 세션을 그 안에서 실행한다. 두 가지 컨테이너 토폴로지를
검증했다.

| 토폴로지 | 세션 컨테이너 위치 | 격리 | 매니페스트 |
|---|---|---|---|
| **CoC** (Container-outside-of-Container) | 호스트 containerd (형제) | 약함 (호스트 공유) | `k8s/coc-agent-*.yaml` |
| **CinC** (Container-in-Container) | fatPod 내부 nested containerd | 강함 (pod 경계 안) | `k8s/cinc-agent-*.yaml` |

두 경우 모두 에이전트는 **작업 트리 코드**를 `PYTHONPATH=<repo>/src`로 실행한다(레지스트리 이미지는
divergent 브랜치라 의존성 carrier로만 사용). BEP-1062 VXLAN 오버레이는 `hostNetwork`로 VTEP=노드 IP.

## 디렉토리

```
fatpod-poc/
├── k8s/
│   ├── infra.yaml            # postgres / valkey / etcd
│   ├── manager.yaml          # manager (작업트리 코드, docker.sock 마운트)
│   ├── coc-agent-104.yaml    # CoC: 호스트 containerd 소켓 마운트
│   ├── coc-agent-ser8.yaml
│   ├── cinc-agent-104.yaml   # CinC: entrypoint가 nested containerd 기동
│   ├── cinc-agent-156.yaml
│   └── appproxy-demo.yaml    # AppProxy 역할 프록시(hostNetwork) 데모
├── config/
│   ├── manager.k8s.toml      # db/etcd = ClusterIP (환경마다 수정 필요)
│   ├── agent.coc-*.toml      # CoC 에이전트 설정
│   ├── agent.cinc-*.toml     # CinC 에이전트 설정
│   └── cinc-entrypoint.sh    # runc 복사 → nested containerd → 이미지 import → agent
├── hostbin/                  # 이미지에 없는 도구를 호스트에서 빌려오는 nsenter 래퍼
│   ├── iptables ethtool conntrack
└── session-payloads/         # ./bai session enqueue 용 JSON (멀티노드/filler/gpu)
```

> 상위 `../fatpod-hostnetwork-poc.md`(체크리스트), `../fatpod-poc-results.md`(실험 결과)도 참조.

## 핵심 결정/이슈 (실측으로 확인)

- **에이전트 이미지엔 agent용 Dockerfile이 없다** → 작업트리 코드를 `PYTHONPATH`로 실행. manager도 동일.
- **로그-라이터 launcher 인터프리터는 호스트에서 유효해야** 함(`sys.executable`) → 호스트 공유 dev venv
  python(`dist/export/.../3.13.7`)으로 에이전트 실행 + `.pyenv` 마운트.
- **DNS 누출이 세션 RUNNING의 최대 블로커**였다: `ClusterFirstWithHostNet`이 컨테이너에 도달 불가한
  k8s CoreDNS를 전파 → 조회 타임아웃 → 커널-runner 이벤트 루프 블록 → jupyter 핸드셰이크 굶음.
  **`dnsPolicy: Default`**로 해결.
- **네트워크 도구**(`iptables/ethtool/conntrack`)가 이미지에 없어 `nsenter -t 1 -m`로 호스트 바이너리 사용
  (`hostbin/` 래퍼). 따라서 **hostPID 필요**. `network-privnet-socket` 미설정 → 특권 에이전트가
  in-process 네트워킹.
- **GPU**: privileged면 `/dev/nvidia*`는 이미 pod에 있음. 에이전트가 NVML/cudart를 ctypes로 로드하므로
  드라이버 lib 마운트 + `LD_LIBRARY_PATH`, 그리고 cuda_open이 docker 게이트를 봐서 `docker.sock` 마운트.
- **CinC의 runc**: bind-mount된 runc는 overlayfs 자기-봉인(CVE-2019-5736)이 빈 placeholder inode를
  봉인해 깨진다 → **runc를 일반 파일로 복사**해서 쓰면 최신 runc 그대로 동작(entrypoint가 처리).
- **멀티노드 분산**: 스케줄러(dispersed)가 이용률 기준이라 비대칭 노드에서 한 쪽에 몰림 →
  **filler 세션**으로 강제 분산(`session-payloads/cinc-filler*.json`).
- **세션 격리**: 각 클러스터 세션이 고유 VXLAN VNI + 서브넷(10.128.N.x). 다른 세션은 같은 노드여도 차단.
- **AppProxy**: 세션은 `advertised-host:host-port`로 iptables DNAT 퍼블리시. pod-native AppProxy는
  에이전트가 `cni0 → 세션브릿지` FORWARD를 열어주면 그 DNAT 포트로 바로 연결 가능(별도 proxy listener 불필요).

## 배포 개요

1. `k8s/infra.yaml` → DB/etcd/valkey. 호스트 DB/etcd를 dump해서 복원(users/images/config).
2. `config/*.toml`의 ClusterIP를 실제 값으로 치환 → ConfigMap.
3. RPC 키페어(`fixtures/{manager,agent}/*.key*`)를 Secret으로.
4. `k8s/manager.yaml` → 8091. `k8s/{coc,cinc}-agent-*.yaml` → 에이전트 등록.
5. `session-payloads/*.json`로 세션 enqueue.

> ⚠️ config의 db 비밀번호는 dev 기본값(`develove`)이고 ClusterIP는 placeholder다 — 환경마다 수정할 것.
