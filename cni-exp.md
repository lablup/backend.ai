# containerd 워크로드 ↔ Cilium CNI 통신 실험 기록

## 1. 목적

Backend.AI containerd 백엔드 — 네이티브 containerd API로 생성하고 전용
containerd namespace(`backendai`)에 두어 kubelet에 보이지 않는 워크로드 —
가 **cluster Cilium CNI 패브릭에 편입되어 실제 k8s pod와 통신**할 수 있는지
검증한다.

## 2. 환경

- k8s 3노드 클러스터:
  | 노드 | IP | CiliumNode pod CIDR |
  |---|---|---|
  | charsyam-gen1 (control-plane) | 192.168.0.11 | `10.0.2.0/24` |
  | charsyam-nvidia | 192.168.0.104 | `10.0.0.0/24` |
  | ser8 (실험 호스트) | 192.168.0.156 | `10.0.1.0/24` |
- cluster Cilium: DaemonSet, CRD 모드(`identity-allocation-mode=crd`,
  kvstore 없음), `ipam=cluster-pool`, `routing-mode=tunnel`(vxlan),
  `enable-policy=default`
- containerd v2.2.0 (kubelet·docker와 공유)
- ser8 초기 상태: cluster Cilium DS pod가 사망한 상태였고, 그 자리를
  **standalone cilium-agent**(Docker 컨테이너 `cilium-agent`, cilium
  v1.14.13, `--enable-k8s=false --routing-mode=native --enable-policy=never
  --kvstore=etcd@192.168.0.156:2379`)가 대신 동작 → pod에 `10.156.x` 할당

## 3. 실험 경과

### 실험 0 (배경) — CRI sandbox가 kubelet에 회수됨
- cri-poc로 공유 containerd에 CRI sandbox 생성 → `--keep`인데도 ~2초 만에 사라짐.
- 원인: kubelet의 `HandlePodCleanups()`가 CRI `ListPodSandbox()`로 풀 안의
  모든 sandbox를 열거 → backing Pod 없는 것을 orphan으로 `RemovePodSandbox`.
- 대조 실험(kubelet 중지 → sandbox 생존)으로 확정.
- → 결정: CRI 대신 **네이티브 containerd API + 전용 namespace**.
  kubelet의 CRI 플러그인은 `k8s.io` namespace만 열거하므로 `backendai`
  namespace의 워크로드는 보이지 않는다.

### 실험 1 — 네트워크 레이어 (netns + CNI + cilium attach)
- `containerd-poc net`: per-workload netns 생성 → `CniInvoker`가 cilium
  conflist를 실행 → cilium-cni가 IP 할당.
- 결과: ✅ attach 성공, netns에 cilium IP 부여.

### 실험 2 — same-node 통신 (standalone cilium 시점)
- containerd 워크로드(ser8) ↔ k8s pod(ser8), ICMP·TCP 양방향.
- 결과: ✅ 전부 통과.
- 단, 이때 standalone agent는 `enable-policy=never` (정책 OFF) 였다.

### 실험 3 — cross-node #1: 실패
- containerd 워크로드(ser8, `10.156.x`) ↔ k8s pod(charsyam-nvidia, `10.0.0.x`).
- 결과: ❌ 100% 손실. plain k8s pod끼리(ser8↔nvidia)도 동일하게 실패.
- → 우리 containerd/CNI 코드와 무관, cilium 토폴로지 문제로 좁혀짐.

### 실험 4 — cilium 토폴로지 진단
- 물리 노드 간(192.168.0.x) ping은 정상 → 순수 cilium pod 라우팅 문제.
- `CiliumNode`: 클러스터는 ser8 pod CIDR을 `10.0.1.0/24`로 알지만, 실제
  ser8 pod은 `10.156.x` (standalone agent가 독자 할당) → **CIDR 불일치**.
  클러스터 cilium에는 `10.156.x`로 가는 경로가 없다.
- 근본 원인: ser8의 cluster Cilium DS pod가 2026-04-27부터 사망(exit 255).
  `/run/xtables.lock`이 **파일이 아니라 빈 디렉토리**여서 cilium·kube-proxy의
  hostPath(`type: File`) 마운트가 실패. standalone agent는 그 우회책이었다.

### 실험 5 — cilium 복구
1. `/run/xtables.lock` 디렉토리 → 파일로 교정 (`rmdir` 후 `touch`).
2. standalone cilium-agent 컨테이너 중지 (`docker stop cilium-agent`).
3. `cilium-cdj9n`·`kube-proxy-vgdsq` pod 삭제 → DaemonSet이 재생성 →
   마운트 성공 → 정상 기동.
- 결과: ✅ ser8이 cluster Cilium 정상 노드로 복귀 (`ds cilium READY 3/3`).

### 실험 6 — cross-node #2: plain k8s pod (복구 후)
- ser8 pod(`10.0.1.88`) ↔ nvidia pod(`10.0.0.172`), 양방향.
- 결과: ✅ 통과. ser8 pod이 정상 CIDR `10.0.1.x`를 받음.

### 실험 7 — containerd 워크로드 on cluster Cilium
- `containerd-poc run`: attach가 이번엔 `10.0.1.189` (cluster CIDR ✅).
- 연결성: ❌ same-node·cross-node **둘 다** 실패.
- cilium endpoint 조회: 우리 endpoint는 identity `reserved:init`,
  **policy Enabled**. (정상 k8s pod endpoint는 실제 identity, policy Disabled.)
- 진단: cluster Cilium은 `enable-k8s=true`라 endpoint identity를 backing
  k8s Pod의 라벨에서 끌어낸다. 우리 워크로드는 Pod가 없으므로 `reserved:init`
  에 영구히 정체. `enable-policy=default`에서 init 상태 endpoint는 정책
  제약을 받아 트래픽이 차단된다.
- cilium 정책은 endpoint의 veth에서 적용되므로 노드 위치와 무관 →
  실험 2의 same-node 성공은 노드 위치 덕이 아니라 당시 `enable-policy=never`
  때문이었음이 확인됨.

### 실험 8 — identity 매뉴얼 부여: 성공
- cilium agent API로 endpoint에서 `reserved:init` 라벨을 제거하고 실제 라벨을
  set (`cilium endpoint labels <id> --delete reserved:init`).
- 결과: endpoint가 실제 identity를 획득(예: `22727`), policy가 Disabled로 해소.
  same-node ping ✅, cross-node ping ✅, 15초 후에도 identity 안정(되돌아오지 않음).
- **k8s 객체를 전혀 건드리지 않음** — 노드 로컬 cilium agent API
  (`/var/run/cilium/cilium.sock`)만 사용.

### 실험 9 — 코드 자동화: 완전 통과 (2026-05-20)
- `CiliumNetworkProvider`가 CNI ADD 직후 `_assign_endpoint_identity`로
  `PATCH /v1/endpoint/{id}/labels`를 자동 호출. `containerd-poc run`을
  매뉴얼 명령 한 줄도 없이 19/19 단계 모두 통과 (cross-node ping 포함:
  ser8 컨테이너 `10.0.1.152` ↔ nvidia pod `10.0.0.210`, 0% packet loss).
- 자동화 과정에서 발견된 4가지 비자명한 디테일은 §4의 "추가 발견"에 정리.

## 4. 핵심 발견

1. **containerd 네이티브 백엔드 + CNI 통합 코드는 정상.** 워크로드를 cilium에
   attach하고 유효한 IP를 받는다. 실패는 모두 환경(cilium 토폴로지) 또는
   cilium의 identity 모델 때문이지 우리 코드의 버그가 아니다.
2. **변수는 same-node vs cross-node가 아니라 "정책 적용 여부 + endpoint
   identity"** 다. 정책 적용 cilium에서 `reserved:init` endpoint는 same-node
   도 막힌다.
3. **비-k8s 워크로드의 cilium identity가 핵심 관문.** k8s 모드 cilium은
   identity를 k8s 객체(Pod)에서 끌어내므로, 비-k8s 워크로드는 `reserved:init`
   에 갇힌다.
4. **해결책 (검증됨, 코드화됨):** CNI attach 후 cilium agent endpoint API로
   `reserved:init`을 제거하고 실제 identity 라벨을 set하면 → 안정적 실제
   identity → 정책 해소 → cross-node 양방향 통신. k8s 객체 0개.
5. cilium identity는 라벨셋 단위 공유 자원이며 reference-count로 GC된다.
   teardown은 endpoint를 CNI DEL로 지우기만 하면 cilium이 identity 참조를
   해제하고 미참조 시 회수한다. 별도의 identity 삭제는 불필요하다.

### 추가 발견 (실험 9 자동화 과정에서)

6. **K8S_POD_NAMESPACE / K8S_POD_NAME 을 CNI_ARGS로 전달하면 오히려 해롭다**
   (Backing Pod이 실제로 없는 경우). cilium-cni는 그 값을 endpoint의
   `external-identifiers`에 기록하고 cilium-daemon이 k8s API에서 그 Pod을
   주기적으로 reconcile한다. Pod이 없음 → reconciler가 user 라벨을
   `security-relevant`에서 strip하고 `reserved:init`을 강제 재투입한다.
   `realized.user`에는 우리 라벨이 그대로 있지만 `security-relevant`에는
   `reserved:init`만 남는 정합 불일치가 관찰된다. 따라서 우리는 이 인자를
   **default OFF (`cilium_pod_namespace=""`)** 로 두고, ClusterMesh
   External Workloads 또는 placeholder Pod 같은 사전 셋업이 있는
   운영자만 opt-in 한다.

7. **cilium의 default `valid-label-prefixes` 필터는 키 prefix를 본다.**
   `^id\..*`, `^io\.kubernetes\.pod\.namespace`, `^app\.kubernetes\.io`,
   `^io\.cilium\.k8s\.policy` 만 security-relevant로 인정한다. Backend.AI의
   도메인 키(`backendai/kernel-id` 등)는 어느 prefix와도 안 맞아 user에
   PATCH해도 `security-relevant`에 진입하지 못한다 → cilium 입장에서
   "security-relevant 비었음 → reserved:init 부여" 결론. 우리는 도메인 키
   앞에 `id.`를 붙여 (`container:id.backendai/kernel-id=...`) `^id\..*` 룰에
   매치시키도록 코드에 박았다.

8. **`prepare_snapshot` 직후 `create_container`까지 가는 시간이 길면
   containerd metadata GC가 active snapshot을 청소한다** (1초 안팎의 짧은
   주기). `create_task`가 overlay 마운트를 시도할 때 upperdir 디렉토리가
   사라져 `no such file or directory`로 실패한다. 디스크에서 직접 확인하면
   parent (image layer) snapshot은 멀쩡한데 active snapshot의 디렉토리만
   증발해 있다. 운영 경로의 정답은 `attach → prepare_snapshot →
   create_container` 순서로 묶어 GC 윈도우를 닫는 것 (또는 containerd
   lease를 명시적으로 잡는 것).

9. **PATCH 후 identity 안착에는 endpoint state 천이 대기가 필요.**
   라벨 PATCH가 받아들여지면 endpoint state는 `ready → regenerating →
   waiting-for-identity → ready`로 한 사이클 돌고, 이 사이 `identity`
   필드는 기존(stale) identity를 가리킨다. PATCH 후 즉시 `identity.labels`를
   읽으면 `reserved:init`이 아직 보여 "실패"로 잘못 판정한다.
   `state == ready`로 다시 안착할 때까지 폴링한 다음 검증해야 새 identity가
   확정된다. 그래도 안 풀리면 PATCH를 재시도(최대 5회) — 우리 코드는 이
   3-step (wait-ready → PATCH → wait-ready → verify identity) 댄스로
   수렴한다.

## 5. 결론 및 남은 과제

**결론:** 비-k8s containerd 워크로드가 cluster Cilium 패브릭의 1급 시민이
되어 실제 k8s pod와 cross-node 양방향 통신을 한다. 컨테이너 부팅 → CNI
attach → identity 자동 부여 → cross-node ping 까지 코드로 자동화되어
있으며, 매뉴얼 cilium CLI 명령 없이 `containerd-poc run` 한 번으로 19개
단계 모두 통과를 확인했다 (실험 9).

**남은 과제 / 옵션:**
- 세션그룹 격리(R3): 부여한 라벨을 selector로 한
  `CiliumNetworkPolicy`를 걸어 구현 (`container:id.backendai/session-id=...`
  를 인-/아웃-바운드 셀렉터로 사용).
- ClusterMesh External Workloads 경로: 진짜 Pod 없이도 cilium의 정식
  외부 워크로드로 등록하는 sanctioned 메커니즘. `cilium_pod_namespace`
  opt-in과 함께 운영자에게 제공.
- 전제: cross-node는 BAI 호스트가 cluster Cilium의 정상 노드여야 한다
  (CNI 전략 문서 섹션 4.1의 요건).
