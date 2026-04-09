# Backend.AI K8s 컨트롤 플레인 + DooD 에이전트 아키텍처 제안서

| 항목 | 값 |
|---|---|
| **문서 ID** | TR-2026-002 |
| **작성일** | 2026-04-08 |
| **작성자** | Backend.AI Architecture Team |
| **상태** | 초안 |
| **분류** | 내부 기술 참조 문서 |
| **범위** | K8s 네이티브 컨트롤 플레인 배포, DooD 기반 에이전트 아키텍처, 컨테이너 런타임 선택 (Docker vs containerd) |

---

## 목차

1. [요약](#1-요약)
2. [서론 및 동기](#2-서론-및-동기)
   - 2.1 [배경](#21-배경)
   - 2.2 [목표](#22-목표)
   - 2.3 [범위](#23-범위)
   - 2.4 [전제 조건 및 가정](#24-전제-조건-및-가정)
3. [현재 아키텍처 개요](#3-현재-아키텍처-개요)
   - 3.1 [컴포넌트 토폴로지](#31-컴포넌트-토폴로지)
   - 3.2 [에이전트-커널 관계](#32-에이전트-커널-관계)
   - 3.3 [인프라 의존성](#33-인프라-의존성)
4. [제안 아키텍처: K8s 컨트롤 플레인 + DooD 에이전트](#4-제안-아키텍처-k8s-컨트롤-플레인--dood-에이전트)
   - 4.1 [아키텍처 개요](#41-아키텍처-개요)
   - 4.2 [컨트롤 플레인 컴포넌트](#42-컨트롤-플레인-컴포넌트)
   - 4.3 [DooD 에이전트 Pod](#43-dood-에이전트-pod)
   - 4.4 [커널 컨테이너 라이프사이클](#44-커널-컨테이너-라이프사이클)
   - 4.5 [네트워킹 아키텍처](#45-네트워킹-아키텍처)
   - 4.6 [스토리지 아키텍처](#46-스토리지-아키텍처)
   - 4.7 [GPU 및 가속기 패스스루](#47-gpu-및-가속기-패스스루)
     - 4.7.1 [이중 레이어 GPU 관리](#471-이중-레이어-gpu-관리)
     - 4.7.2 [NVIDIA 드라이버 및 Container Toolkit (호스트 레벨 전제)](#472-nvidia-드라이버-및-container-toolkit-호스트-레벨-전제)
     - 4.7.3 [Agent Pod의 GPU 접근](#473-agent-pod의-gpu-접근)
     - 4.7.4 [커널 컨테이너 GPU 할당](#474-커널-컨테이너-gpu-할당)
     - 4.7.5 [분할 GPU Hook Library 배포](#475-분할-gpu-hook-library-배포)
     - 4.7.6 [MIG 파티셔닝](#476-mig-파티셔닝)
     - 4.7.7 [GPU 헬스 모니터링 및 장애 처리](#477-gpu-헬스-모니터링-및-장애-처리)
     - 4.7.8 [컴퓨트 플러그인 이미지 전략](#478-컴퓨트-플러그인-이미지-전략)
     - 4.7.9 [VM 기반 격리 대안 (외부 문서)](#479-vm-기반-격리-대안-외부-문서)
5. [컨테이너 런타임 분석: Docker vs containerd](#5-컨테이너-런타임-분석-docker-vs-containerd)
   - 5.1 [Docker를 이용한 DooD (docker.sock)](#51-docker를-이용한-dood-dockersock)
   - 5.2 [containerd를 이용한 DooD (containerd.sock)](#52-containerd를-이용한-dood-containerdsock)
   - 5.3 [기능 동등성 매트릭스](#53-기능-동등성-매트릭스)
   - 5.4 [성능 비교](#54-성능-비교)
   - 5.5 [보안 비교](#55-보안-비교)
   - 5.6 [운영 복잡도](#56-운영-복잡도)
   - 5.7 [런타임 선택 권고](#57-런타임-선택-권고)
6. [컨트롤 플레인 설치 (Helm)](#6-컨트롤-플레인-설치-helm)
   - 6.1 [의존성 체인 및 부트스트랩 순서](#61-의존성-체인-및-부트스트랩-순서)
   - 6.2 [서비스 디스커버리 아키텍처](#62-서비스-디스커버리-아키텍처)
   - 6.3 [Helm 차트 구조](#63-helm-차트-구조)
   - 6.4 [글로벌 Values 설정](#64-글로벌-values-설정)
   - 6.5 [컴포넌트 환경 변수 주입](#65-컴포넌트-환경-변수-주입)
   - 6.6 [부팅 순서 및 Init 컨테이너](#66-부팅-순서-및-init-컨테이너)
   - 6.7 [설치 명령](#67-설치-명령)
   - 6.8 [컨테이너 이미지 관리](#68-컨테이너-이미지-관리)
   - 6.9 [데이터베이스 마이그레이션 전략 (Alembic)](#69-데이터베이스-마이그레이션-전략-alembic)
   - 6.10 [Redis 고가용성](#610-redis-고가용성)
7. [상세 컴포넌트 설계](#7-상세-컴포넌트-설계)
   - 7.1 [컨트롤 플레인 Pod 사양](#71-컨트롤-플레인-pod-사양)
   - 7.2 [에이전트 DaemonSet 설계](#72-에이전트-daemonset-설계)
   - 7.3 [커널 컨테이너 관리](#73-커널-컨테이너-관리)
   - 7.4 [서비스 디스커버리 및 통신](#74-서비스-디스커버리-및-통신)
8. [현재 아키텍처로부터의 마이그레이션 경로](#8-현재-아키텍처로부터의-마이그레이션-경로)
   - 8.1 [에이전트 코드 변경 사항](#81-에이전트-코드-변경-사항)
   - 8.2 [매니저 코드 변경 사항](#82-매니저-코드-변경-사항)
   - 8.3 [설정 변경 사항](#83-설정-변경-사항)
9. [리스크 분석](#9-리스크-분석)
   - 9.1 [기술적 리스크](#91-기술적-리스크)
   - 9.2 [운영 리스크](#92-운영-리스크)
   - 9.3 [완화 전략](#93-완화-전략)
10. [대안적 접근 방식](#10-대안적-접근-방식)
    - 10.1 [순수 K8s 네이티브 (커널을 Pod으로)](#101-순수-k8s-네이티브-커널을-pod으로)
    - 10.2 [하이브리드: 호스트 에이전트 + K8s 컨트롤 플레인](#102-하이브리드-호스트-에이전트--k8s-컨트롤-플레인)
    - 10.3 [K8s Operator 패턴](#103-k8s-operator-패턴)
11. [필요 실험](#11-필요-실험)
    - 11.1 [EXP-1: DooD 컨테이너에 대한 CNI 직접 호출](#111-exp-1-dood-컨테이너에-대한-cni-직접-호출)
    - 11.2 [EXP-2: CNI IPAM과 K8s Pod의 공존](#112-exp-2-cni-ipam과-k8s-pod의-공존)
    - 11.3 [EXP-3: 호스트 CNI를 통한 크로스 노드 연결](#113-exp-3-호스트-cni를-통한-크로스-노드-연결)
    - 11.4 [EXP-4: DooD 커널 컨테이너에서 GPU 디바이스 접근](#114-exp-4-dood-커널-컨테이너에서-gpu-디바이스-접근)
    - 11.5 [EXP-5: 에이전트 Pod 재시작 및 커널 복구](#115-exp-5-에이전트-pod-재시작-및-커널-복구)
    - 11.6 [EXP-6: containerd DooD 기본 라이프사이클](#116-exp-6-containerd-dood-기본-라이프사이클)
    - 11.7 [EXP-7: vfolder 바인드 마운트 경로 일관성](#117-exp-7-vfolder-바인드-마운트-경로-일관성)
    - 11.8 [EXP-8: Docker Swarm Overlay와 K8s CNI의 공존](#118-exp-8-docker-swarm-overlay와-k8s-cni의-공존)
    - 11.9 [실험 실행 우선순위](#119-실험-실행-우선순위)
12. [결론 및 권고사항](#12-결론-및-권고사항)
13. [참고 문헌](#13-참고-문헌)

---

## 1. 요약

이 문서는 Backend.AI의 컨트롤 플레인(Manager, etcd, PostgreSQL, Redis)을 Kubernetes Pod으로 운영하고, 에이전트는 DaemonSet Pod으로 배포하여 Docker-out-of-Docker(DooD) 방식으로 호스트의 컨테이너 런타임에서 커널(컴퓨트 세션) 컨테이너를 직접 실행하는 아키텍처를 제안한다.

**핵심 발견 사항:**

- DooD 아키텍처는 Backend.AI의 기존 Docker 기반 커널 라이프사이클 관리를 그대로 유지하면서, 컨트롤 플레인에 K8s 운영 이점(롤링 업데이트, 자가 복구, 선언적 설정)을 확보한다.
- **신규 배포 환경에서는 Docker보다 containerd를 DooD 런타임 대상으로 권고한다.** containerd는 표준 K8s CRI 런타임이며, Docker 데몬 의존성을 제거하고, Backend.AI 사용 사례에 동등한 기능을 제공한다. Docker는 이미 배포된 환경이나 Docker Compose 기반 도구가 필요한 환경에서 여전히 유효한 선택지이다.
- 에이전트 DaemonSet Pod은 호스트 컨테이너 런타임 소켓, GPU 디바이스, 호스트 네트워크/스토리지 경로에 접근하기 위해 `privileged` 또는 특정 capability 권한이 필요하다.
- 제안된 아키텍처는 VM 기반 격리(예: Kata Containers)에서 관찰되는 제한 없이, 완전한 GPU 패스스루(멀티 GPU, 분할 GPU), vfolder 바인드 마운트, 오버레이 네트워킹을 지원한다.
- 현재 베어메탈/VM 에이전트 배포에서의 마이그레이션은 점진적이다: DooD 컨테이너가 동일한 Docker/containerd API 인터페이스를 공유하므로 기존 `DockerAgent` 코드베이스는 최소한의 변경만 필요하다.

---

## 2. 서론 및 동기

### 2.1 배경

Backend.AI는 현재 두 가지 에이전트 백엔드를 지원한다: `docker`(프로덕션)과 `kubernetes`(실험적). `docker` 백엔드가 프로덕션 배포에 사용되는 성숙하고 기능이 완전한 구현체이다. 에이전트는 일반적으로 베어메탈 또는 VM 호스트에 직접 배포되며, 인프라 서비스(etcd, Redis, PostgreSQL)와 함께 같은 호스트 또는 별도 호스트에 위치한다.

이 배포 모델에는 운영상의 어려움이 있다:
- **인프라 프로비저닝**: 각 에이전트 노드에 Docker 데몬, 에이전트 프로세스, 컴퓨트 플러그인, 네트워크 설정을 수동 또는 Ansible로 구성해야 한다.
- **컨트롤 플레인 관리**: Manager, etcd, PostgreSQL, Redis가 Kubernetes 외부에서 별도의 배포, 모니터링, 라이프사이클 관리를 필요로 한다.
- **확장**: 에이전트 노드 추가 시 매니저 클러스터에 수동 등록이 필요하다.
- **업데이트**: 에이전트 롤링 업데이트에 별도의 오케스트레이션이 필요하다.

### 2.2 목표

1. **K8s 네이티브 컨트롤 플레인**: Manager, etcd, PostgreSQL, Redis를 StatefulSet, Service, ConfigMap, Helm 차트를 활용한 표준 K8s 워크로드로 운영한다.
2. **K8s 관리 에이전트 라이프사이클**: 에이전트를 DaemonSet으로 배포하여 GPU 노드 자동 스케줄링, 롤링 업데이트, 헬스 기반 재시작을 확보한다.
3. **커널 관리 모델 유지**: Docker/containerd API를 직접 사용하여 커널 컨테이너 라이프사이클을 관리하며, 멀티 GPU, 분할 GPU, 오버레이 네트워크, 바인드 마운트 등 전체 기능 세트를 보존한다.
4. **최소한의 코드 변경**: 새로운 K8s 네이티브 커널 관리 레이어 대신 기존 `DockerAgent` 구현체를 DooD로 활용한다.

### 2.3 범위

이 문서가 다루는 내용:
- K8s 기반 컨트롤 플레인 배포의 아키텍처 설계
- DooD 에이전트 Pod 설계 및 호스트 리소스 접근 패턴
- 커널 관리를 위한 컨테이너 런타임 선택 (Docker 데몬 vs containerd)
- 마이그레이션 경로 및 필요한 코드 변경
- 리스크 분석 및 대안적 접근 방식

### 2.4 전제 조건 및 가정

이 아키텍처는 다음 명시적 가정을 기반으로 한다. 이 설계가 설명된 대로 동작하려면 이 가정들이 참이어야 하며, 이는 Kubernetes 관리 도메인과 Backend.AI 관리 도메인 간의 경계를 정의한다.

#### 2.4.1 GPU 리소스는 Kubernetes가 관리하지 않는다

Kubernetes는 Backend.AI 에이전트 노드에서 GPU 리소스를 스케줄링, 할당, 추적하지 **않는다**. 구체적으로:

- NVIDIA device plugin(`nvidia-device-plugin-daemonset`)은 에이전트 노드에 **배포되지 않는다**.
- K8s Pod 스펙의 `nvidia.com/gpu` 리소스 요청은 이 노드에서 의미가 없다.
- GPU 할당은 Backend.AI 자체 스케줄러(Sokovan)가 etcd를 통해 전적으로 처리한다.
- Kubernetes는 어떤 GPU가 어떤 커널 컨테이너에 사용되는지 알지 못한다.

K8s device plugin과 Backend.AI Agent 간에 GPU 관리를 공유하려고 하면 이중 할당 충돌(동일 GPU가 K8s Pod과 Backend.AI 커널에 동시에 할당됨)이 발생하며, Backend.AI의 가속기 플러그인 시스템을 K8s device plugin API에 통합하기 위해 재작성해야 한다. 이 통합은 명시적으로 **범위 외**이다.

#### 2.4.2 GPU 노드는 Taint로 격리된다

모든 Backend.AI 에이전트 노드는 전용 taint로 표시된다:

```bash
kubectl taint nodes <gpu-node> backendai.io/dedicated=agent:NoSchedule
```

이는 다음 효과를 가진다:

- 일반 K8s 워크로드는 이 노드에 스케줄될 수 없다 (taint에 대한 toleration 없음).
- Backend.AI의 DaemonSet(Agent, NFS Mounter)만 이 taint를 tolerate하여 이 노드에서 실행 가능하다.
- 커널 컨테이너(DooD)는 K8s 리소스가 아니므로 taint의 영향을 받지 않는다 — K8s 스케줄러를 완전히 우회한다.

이 격리는 노드 리소스(CPU, 메모리, GPU)가 Backend.AI 워크로드 전용으로 예약됨을 보장하며, 관련 없는 K8s Pod과의 노이지 네이버(noisy neighbor) 시나리오를 방지한다.

#### 2.4.3 커널 컨테이너는 Kubernetes 제어 밖에서 동작한다

커널 컨테이너는 K8s Pod이 아닌 Docker/containerd API(DooD)를 통해 생성된다. 따라서:

- K8s는 커널 컨테이너의 라이프사이클, 리소스 사용량, 라벨, 네트워킹에 대해 알지 못한다.
- `kubectl get pods`는 커널 컨테이너를 표시하지 않는다.
- K8s NetworkPolicy, PodSecurityPolicy, LimitRange, ResourceQuota는 커널 컨테이너에 적용되지 않는다.
- 커널 컨테이너 메트릭은 Backend.AI 자체 모니터링이 수집한다 (기본적으로 K8s Prometheus 스택이 아님).

모든 커널 레벨 작업 — 생성, 바인드 마운트, GPU 할당, 헬스 모니터링, 정리 — 은 Backend.AI Agent의 책임이다.

#### 2.4.4 전용 노드 풀

노드 풀 간의 명확한 분리가 필요하다:

| 노드 풀 | Taint | 목적 | 워크로드 |
|---|---|---|---|
| **컨트롤 플레인 풀** | 없음 | K8s 관리 Backend.AI 서비스 실행 | Manager, PostgreSQL, Redis, etcd, AppProxy, WebServer |
| **에이전트 풀** | `backendai.io/dedicated=agent:NoSchedule` | Backend.AI Agent와 커널 컨테이너 실행 | Agent DaemonSet, NFS Mounter DaemonSet, 커널 컨테이너 (DooD 경유) |

동일 노드에 컨트롤 플레인 워크로드와 에이전트 워크로드를 혼합하는 것은 **지원되지 않으며** 리소스 경합을 초래한다.

#### 2.4.5 NVIDIA 드라이버와 Container Toolkit은 호스트 레벨 전제이다

NVIDIA GPU 드라이버와 NVIDIA Container Toolkit은 Docker, containerd, kubelet과 동일한 범주의 **호스트 레벨 전제 조건**으로 취급된다. Backend.AI 배포 전에 각 에이전트 노드에 설치되어야 하며, Kubernetes/Helm이 이들의 설치를 관리하지 않는다.

**근거:**

- NVIDIA 드라이버는 커널 모듈이므로 호스트 커널 버전과 긴밀히 결합됨
- 드라이버는 DaemonSet이 reconcile한 후가 아닌 노드 부팅 직후에 즉시 사용 가능해야 함
- 컨테이너 런타임(Docker/containerd)은 데몬 레벨에서 `nvidia-container-runtime`을 구성해야 하며, 이는 호스트 레벨 설정임
- GPU 문제 디버깅은 컨테이너화된 드라이버 설치기보다 호스트 레벨 드라이버로 훨씬 쉬움

**설치 방법** (하나 선택):

| 환경 | 권장 방법 |
|---|---|
| 베어메탈 / 온프레미스 | 드라이버가 사전 설치된 노드 OS 이미지 (Packer, Ansible) |
| 클라우드 (AWS/GCP/Azure) | GPU 지원 베이스 이미지 (Deep Learning AMI 등) 또는 cloud-init |
| Kubernetes 배포판 | K3s/RKE2 GPU 설정, 또는 RHEL/OpenShift GPU 노드 프로비저닝 |

**Backend.AI 배포 전 필요 상태:**

1. 호스트에서 `nvidia-smi`가 정상 동작
2. NVIDIA Container Toolkit이 Docker/containerd에 설치 및 구성됨
3. 호스트에서 `docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi`가 동작

이 중 하나라도 누락되면 Backend.AI Agent가 GPU 열거에 실패한다.

**NVIDIA GPU Operator에 관한 참고**: Operator의 드라이버 설치 기능(컨테이너화된 드라이버 DaemonSet)은 주 설치 방법으로 **권장하지 않는다**. GPU Feature Discovery와 DCGM 메트릭에 제한된 선택적 Operator 사용에 대해서는 섹션 4.7.2를 참조.

#### 2.4.6 관리 도메인 경계

위 가정들은 Kubernetes가 관리하는 것과 Backend.AI가 관리하는 것 사이의 명확한 경계를 확립한다:

| 도메인 | 관리 주체 | 범위 |
|---|---|---|
| 컨트롤 플레인 라이프사이클 | Kubernetes | Manager/DB/Redis/etcd/AppProxy Pod 스케줄링, 헬스, 롤링 업데이트 |
| Agent DaemonSet 라이프사이클 | Kubernetes | Agent Pod 스케줄링, 헬스, 롤링 업데이트 |
| GPU 디바이스 할당 | **Backend.AI** | 물리 GPU의 커널 컨테이너 할당, 분할 공유, MIG 파티셔닝 |
| 커널 컨테이너 라이프사이클 | **Backend.AI** | 컨테이너 생성, 바인드 마운트, REPL 통신, 서비스 포트 매핑 |
| 커널 네트워킹 | **Backend.AI + Docker/containerd** | 브릿지/오버레이 네트워크, 커널 간 통신 |
| 스토리지 마운트 오케스트레이션 | **Backend.AI + 호스트/CSI** | vfolder 경로, 스크래치 공간 |

이 분리는 의도된 것이며, Backend.AI의 기존 가속기 플러그인 시스템의 전체 기능 세트(CUDA 훅 라이브러리를 통한 분할 GPU, 멀티 GPU 할당, MIG 지원 등)를 재구조화 없이 보존한다. 섹션 4.7 (GPU 및 가속기 패스스루) 이후 섹션들은 이 전제 조건이 충족되었다고 가정한다.

---

## 3. 현재 아키텍처 개요

### 3.1 컴포넌트 토폴로지

```
┌─────────────────────── 배포 토폴로지 ─────────────────────────┐
│                                                                │
│  ┌─── 매니저 노드 ───────────────────────────────────────┐    │
│  │  ┌──────────┐  ┌──────────┐  ┌───────┐  ┌──────────┐  │    │
│  │  │ Manager  │  │PostgreSQL│  │ Redis │  │   etcd   │  │    │
│  │  │ (Python) │  │          │  │       │  │          │  │    │
│  │  └────┬─────┘  └──────────┘  └───────┘  └──────────┘  │    │
│  │       │ ZeroMQ/Callosum RPC                            │    │
│  └───────┼────────────────────────────────────────────────┘    │
│          │                                                     │
│  ┌───────▼─── 에이전트 노드 (GPU 호스트별) ──────────────┐    │
│  │  ┌──────────┐     ┌──────────────┐                    │    │
│  │  │  Agent   │────▶│ Docker Daemon│                    │    │
│  │  │ (Python) │     │              │                    │    │
│  │  └──────────┘     └──────┬───────┘                    │    │
│  │                          │                             │    │
│  │          ┌───────────────┼───────────────┐             │    │
│  │          │               │               │             │    │
│  │   ┌──────▼───┐   ┌──────▼───┐   ┌──────▼───┐         │    │
│  │   │ Kernel 1 │   │ Kernel 2 │   │ Kernel 3 │         │    │
│  │   │(세션)    │   │(세션)    │   │(세션)    │         │    │
│  │   └──────────┘   └──────────┘   └──────────┘         │    │
│  └────────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────┘
```

### 3.2 에이전트-커널 관계

Backend.AI 에이전트(`src/ai/backend/agent/docker/agent.py`의 `DockerAgent`)는 Docker API(`aiodocker` 라이브러리)를 통해 커널 컨테이너를 관리한다:

- **컨테이너 생성**: 에이전트가 특정 리소스 제한, GPU 디바이스 매핑, 네트워크 설정, 볼륨 마운트를 가진 Docker 컨테이너를 생성한다.
- **라이프사이클 관리**: 시작, 중지, 재시작, 삭제 작업은 에이전트의 상태 머신(`agent/stage/`)을 통해 이루어진다.
- **리소스 할당**: GPU 할당(전체, CUDA 훅 라이브러리를 통한 분할), CPU 피닝, 메모리 제한이 Docker 컨테이너 생성 파라미터로 설정된다.
- **스토리지**: vfolder가 호스트 경로에서 커널 컨테이너로 바인드 마운트된다.
- **네트워킹**: Docker 오버레이 네트워크(Swarm 모드)가 멀티 노드 세션 연결을 제공한다.

### 3.3 인프라 의존성

| 컴포넌트 | 역할 | 연결 방식 |
|---|---|---|
| PostgreSQL | 영구 상태 (세션, 사용자, 리소스 정책) | TCP (asyncpg) |
| Redis/Valkey | Pub/sub, 캐싱, 실시간 세션 상태 | TCP (redis-py async) |
| etcd | 설정 저장소, 서비스 디스커버리, 분산 락 | gRPC (etcetra) |
| Docker Daemon | 커널 컨테이너 라이프사이클 | Unix 소켓 (`/var/run/docker.sock`) |
| Manager | 오케스트레이션, 스케줄링, API 게이트웨이 | ZeroMQ/Callosum RPC |

---

## 4. 제안 아키텍처: K8s 컨트롤 플레인 + DooD 에이전트

### 4.1 아키텍처 개요

```
┌───────────────────── Kubernetes 클러스터 ─────────────────────────┐
│                                                                    │
│  ┌─── 컨트롤 플레인 네임스페이스 (backendai-system) ──────────┐   │
│  │                                                             │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────┐  ┌──────────┐  │   │
│  │  │  Manager   │  │ PostgreSQL │  │ Redis  │  │   etcd   │  │   │
│  │  │ Deployment │  │ StatefulSet│  │ Deploy/│  │ Stateful │  │   │
│  │  │ (복제본:  │  │ (복제본:  │  │ Stateful│  │ Set      │  │   │
│  │  │  2-3, HA) │  │  1-3, HA) │  │ Set    │  │ (3 노드) │  │   │
│  │  └─────┬──────┘  └────────────┘  └────────┘  └──────────┘  │   │
│  │        │ K8s Service (ClusterIP)                             │   │
│  └────────┼─────────────────────────────────────────────────────┘   │
│           │ ZeroMQ RPC (K8s Service 엔드포인트)                     │
│           │                                                         │
│  ┌────────▼─── 에이전트 DaemonSet (GPU 노드 풀) ────────────────┐  │
│  │                                                               │  │
│  │  ┌─────────────────────────────────────────────────────────┐  │  │
│  │  │  에이전트 Pod (노드당 1개)                               │  │  │
│  │  │  ┌────────────┐     ┌─────────────────────────────┐     │  │  │
│  │  │  │  Agent     │────▶│ 호스트 컨테이너 런타임      │     │  │  │
│  │  │  │  Container │     │ (Docker/containerd,         │     │  │  │
│  │  │  │            │     │  마운트된 소켓 - DooD)      │     │  │  │
│  │  │  └────────────┘     └──────────────┬──────────────┘     │  │  │
│  │  └────────────────────────────────────┼────────────────────┘  │  │
│  │                                       │                       │  │
│  │     ┌─────────────────────────────────┼─────────────────┐     │  │
│  │     │              호스트             │                 │     │  │
│  │     │  ┌───────────┐  ┌───────────┐  ┌───────────┐     │     │  │
│  │     │  │ Kernel 1  │  │ Kernel 2  │  │ Kernel 3  │     │     │  │
│  │     │  │ Container │  │ Container │  │ Container │     │     │  │
│  │     │  │ [GPU 0,1] │  │ [GPU 2]   │  │ [CPU only]│     │     │  │
│  │     │  └───────────┘  └───────────┘  └───────────┘     │     │  │
│  │     └───────────────────────────────────────────────────┘     │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### 4.2 컨트롤 플레인 컴포넌트

각 컨트롤 플레인 컴포넌트는 표준 K8s 워크로드로 운영된다:

| 컴포넌트 | K8s 워크로드 타입 | 복제본 | 영속성 | 비고 |
|---|---|---|---|---|
| Manager | Deployment | 2-3 (HA) | 없음 (무상태) | K8s Service로 노출 (내부: ClusterIP, API: LoadBalancer/Ingress) |
| PostgreSQL | StatefulSet | 1 (단일) 또는 3 (HA, Patroni/CloudNativePG) | PVC (PersistentVolumeClaim) | CloudNativePG 오퍼레이터 또는 외부 관리형 DB 사용 |
| Redis/Valkey | Deployment 또는 StatefulSet | 1 (단일) 또는 3 (Sentinel/Cluster) | PVC (선택적, AOF) | 프로덕션에서는 관리형 Redis(ElastiCache, Memorystore) 고려 |
| etcd | StatefulSet | 3 (쿼럼) | 멤버별 PVC | etcd 오퍼레이터 또는 Bitnami Helm 차트 사용 |
| Storage Proxy | Deployment | 1-2 | 없음 | 스토리지 백엔드 접근 필요 |
| Web Server | Deployment | 2-3 | 없음 | 외부 접근용 Ingress |
| AppProxy Coordinator | Deployment | 1-2 | 없음 | DB + etcd + Redis 필요 |
| AppProxy Worker | Deployment | 2-3 | 없음 | Redis + etcd 필요 |

**핵심 설계 결정:**

- **네임스페이스 격리**: 컨트롤 플레인은 `backendai-system` 네임스페이스에 위치. 커널은 호스트에서 직접 실행(K8s 외부) 또는 선택적으로 별도 네임스페이스.
- **서비스 메시 선택적**: 내부 컨트롤 플레인 통신은 K8s Service를 직접 사용 가능. mTLS와 관측성을 위해 Istio/Linkerd 선택적.
- **ConfigMap과 Secret**: 매니저 설정, 데이터베이스 인증 정보, etcd TLS 인증서는 K8s 네이티브 프리미티브로 관리.

### 4.3 DooD 에이전트 Pod

에이전트는 GPU 노드 풀의 모든 노드에 스케줄되는 **DaemonSet** Pod으로 실행된다. 마운트된 소켓을 통해 호스트의 컨테이너 런타임에 접근한다:

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: backendai-agent
  namespace: backendai-system
spec:
  selector:
    matchLabels:
      app: backendai-agent
  template:
    metadata:
      labels:
        app: backendai-agent
    spec:
      hostNetwork: true          # 커널 통신을 위해 호스트 네트워킹 필요
      hostPID: false
      nodeSelector:
        backendai.io/role: agent  # 에이전트 지정 노드에만 스케줄
      tolerations:
        - key: nvidia.com/gpu
          operator: Exists
          effect: NoSchedule
      serviceAccountName: backendai-agent
      containers:
        - name: agent
          image: lablup/backend.ai-agent:latest
          securityContext:
            privileged: true       # GPU 접근 및 컨테이너 런타임 소켓에 필요
            readOnlyRootFilesystem: true
            seccompProfile:
              type: RuntimeDefault
          volumeMounts:
            # DooD: 호스트 컨테이너 런타임 소켓 마운트
            - name: container-runtime-socket
              mountPath: /var/run/docker.sock   # 또는 /run/containerd/containerd.sock
            # 커널 데이터용 호스트 경로
            - name: scratch-space
              mountPath: /var/cache/scratches
            - name: vfolder-storage
              mountPath: /vfolder
            # 호스트 메트릭 가시성
            - name: host-proc
              mountPath: /host/proc
              readOnly: true
            - name: host-sys
              mountPath: /host/sys
              readOnly: true
            # NVIDIA 디바이스 파일
            - name: nvidia-devices
              mountPath: /dev/nvidia0
              # ... (노드 GPU 수에 따라 동적 매핑)
          env:
            - name: BACKEND_AGENT_BACKEND
              value: "docker"       # 기존 DockerAgent를 DooD로 사용
            - name: NODE_NAME
              valueFrom:
                fieldRef:
                  fieldPath: spec.nodeName
      volumes:
        - name: container-runtime-socket
          hostPath:
            path: /var/run/docker.sock  # 또는 /run/containerd/containerd.sock
            type: Socket
        - name: scratch-space
          hostPath:
            path: /var/cache/backendai/scratches
            type: DirectoryOrCreate
        - name: vfolder-storage
          hostPath:
            path: /mnt/vfolder
            type: Directory
        - name: host-proc
          hostPath:
            path: /proc
            type: Directory
        - name: host-sys
          hostPath:
            path: /sys
            type: Directory
```

> **참고**: Pod 내부의 `/proc`과 `/sys`는 Pod의 cgroup을 반영하며 호스트 것이 아니다. 정확한 리소스 감지와 메트릭 수집을 위해 호스트의 `/proc`과 `/sys`를 읽기 전용으로 마운트해야 한다.

**DooD 에이전트에 필요한 호스트 마운트:**

| 호스트 경로 | 용도 | 마운트 타입 |
|---|---|---|
| `/var/run/docker.sock` 또는 `/run/containerd/containerd.sock` | 컨테이너 런타임 API 접근 | Socket |
| `/var/cache/backendai/scratches` | 커널 스크래치 공간 (작업 디렉터리) | DirectoryOrCreate |
| `/mnt/vfolder` (또는 설정된 스토리지 경로) | vfolder 스토리지 백엔드 마운트 포인트 | Directory |
| `/proc` → `/host/proc` | 호스트 리소스 감지 및 메트릭 수집 | Directory (읽기 전용) |
| `/sys` → `/host/sys` | 호스트 디바이스/토폴로지 정보 | Directory (읽기 전용) |
| `/dev/nvidia*` | GPU 디바이스 파일 | Device (NVIDIA 디바이스 플러그인 경유) |
| `/usr/local/nvidia` 또는 `/usr/lib/x86_64-linux-gnu` | NVIDIA 드라이버 라이브러리 | Directory (읽기 전용) |

### 4.4 커널 컨테이너 라이프사이클

DooD 모델에서 커널 컨테이너는 마운트된 런타임 소켓을 통해 **호스트에서** 생성된다. 에이전트 Pod의 자식이 아니라 형제(sibling)이다:

```
┌──────────────── K8s 노드 ────────────────────────────────────┐
│                                                               │
│  ┌── kubelet 관리 ─────────────────────────────────────────┐  │
│  │  에이전트 Pod (DaemonSet)                               │  │
│  │  - 마운트된 소켓으로 호스트 컨테이너 런타임과 통신      │  │
│  └──────────────────────────┬──────────────────────────────┘  │
│                             │                                  │
│                    소켓을 통한 API 호출                         │
│                             │                                  │
│  ┌── 호스트 컨테이너 런타임 ▼──────────────────────────────┐  │
│  │  docker daemon / containerd                              │  │
│  │                                                          │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐         │  │
│  │  │  Kernel A  │  │  Kernel B  │  │  Kernel C  │         │  │
│  │  │  (K8s에서  │  │  (K8s에서  │  │  (K8s에서  │         │  │
│  │  │  관리되지  │  │  관리되지  │  │  관리되지  │         │  │
│  │  │  않음)     │  │  않음)     │  │  않음)     │         │  │
│  │  └────────────┘  └────────────┘  └────────────┘         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

**중요 특성:**

- 커널 컨테이너는 **Kubernetes에서 보이지 않는다**. Docker/containerd API를 통해 Backend.AI 에이전트가 전적으로 관리한다.
- 따라서 K8s 리소스 회계에 커널 컨테이너가 포함되지 않는다. 노드 리소스 할당은 Backend.AI 자체 리소스 관리(etcd 기반 슬롯 할당)를 통해 조율되어야 한다.
- 커널 컨테이너는 호스트 GPU, 호스트 네트워크 인터페이스, 호스트 스토리지에 직접 접근한다 — 가상화 레이어 오버헤드가 없다.

### 4.5 네트워킹 아키텍처

#### 4.5.1 에이전트-매니저 통신

| 경로 | 프로토콜 | K8s 메커니즘 |
|---|---|---|
| Agent → Manager RPC | ZeroMQ/Callosum | K8s Service (ClusterIP) + 에이전트 hostNetwork |
| Agent → etcd | gRPC | K8s Service (ClusterIP) |
| Agent → Redis | TCP | K8s Service (ClusterIP) |
| Manager → Agent 이벤트 | ZeroMQ pub/sub | 에이전트 hostNetwork IP |

**RPC 보안**: 에이전트가 `hostNetwork: true`를 사용하므로 사이드카 기반 서비스 메시(Istio/Linkerd)가 에이전트 트래픽을 가로채서 mTLS를 적용할 수 없다. 대신 Backend.AI의 내장 ZeroMQ CURVE 암호화를 Manager↔Agent RPC에 활성화해야 한다. 에이전트 설정에서 `manager-public-key`와 에이전트 키페어를 구성하여 서비스 메시에 의존하지 않고 모든 RPC 트래픽을 암호화한다.

에이전트 Pod이 `hostNetwork: true`를 사용하는 이유:
1. 매니저가 노드의 실제 IP 주소로 에이전트에 도달할 수 있어야 한다(기존 ZeroMQ 기반 RPC 모델에 필요).
2. 커널 컨테이너(호스트 네트워크 또는 Docker 오버레이에서 실행)가 `localhost` 또는 호스트 IP로 에이전트와 통신할 수 있다.

#### 4.5.2 커널 네트워킹

커널 컨테이너는 Docker/containerd 네트워킹을 직접 사용한다(K8s CNI가 아님):

- **단일 노드 세션**: Docker 브릿지 네트워크(`backendai_network`), 현재 배포와 동일.
- **멀티 노드 세션(클러스터 모드)**: 크로스 노드 커널 통신(SSH, MPI, NCCL)을 위한 Docker Swarm 오버레이 네트워크.
- **서비스 포트**: 호스트에서 Docker 포트 매핑을 통해 노출, K8s NodePort 또는 외부 로드 밸런서로 접근 가능.

**참고**: Docker Swarm 오버레이는 K8s CNI와 독립적이다. 두 네트워킹 스택이 동일 노드에 공존한다. 이는 일반적인 DooD 패턴이지만, Swarm 오버레이와 K8s CNI의 공존 동작은 CNI 구현(iptables 기반 vs eBPF 기반)에 따라 다르다. 환경별로 상호작용을 검증해야 한다 — 필요 실험 섹션의 EXP-8을 참조.

**네트워크 성능 참고**: Docker Swarm 오버레이는 Backend.AI의 현재 베어메탈 프로덕션 배포에서 멀티 노드 세션에 사용되는 것과 동일한 네트워킹 메커니즘이다. 에이전트를 K8s DaemonSet(DooD)으로 이전해도 커널 컨테이너 네트워킹 경로는 변경되지 않는다 — Swarm 오버레이가 동일하게 계속 동작한다. 따라서 현재 배포 모델 대비 **네트워크 성능 저하가 없다.**

#### 4.5.3 커널 통신 모델

커널 컨테이너는 **인프라에 대해 완전히 무지(agnostic)**하다 — etcd, Redis, PostgreSQL, Manager의 존재를 전혀 알지 못한다. 커널 코드베이스(`src/ai/backend/kernel/`, `src/ai/backend/runner/`)에는 어떤 인프라 서비스에 대한 참조도 없다. 모든 외부 통신은 Agent가 중개한다.

**통신 채널:**

```
┌─── Node A ──────────────────────────────┐    ┌─── Node B ──────────────────────────────┐
│                                          │    │                                          │
│  ┌── Agent A (hostNetwork) ───────────┐  │    │  ┌── Agent B (hostNetwork) ───────────┐  │
│  │  ZeroMQ      ZeroMQ                │  │    │  │  ZeroMQ      ZeroMQ                │  │
│  │  ▲              ▲                   │  │    │  │  ▲              ▲                   │  │
│  └──┼──────────────┼──────────────────┘  │    │  └──┼──────────────┼──────────────────┘  │
│     │              │                      │    │     │              │                      │
│     ▼              ▼                      │    │     ▼              ▼                      │
│  ┌────────┐  ┌────────┐                  │    │  ┌────────┐  ┌────────┐                  │
│  │Kernel 1│  │Kernel 2│                  │    │  │Kernel 3│  │Kernel 4│                  │
│  └───┬────┘  └───┬────┘                  │    │  └───┬────┘  └───┬────┘                  │
│      └─────┬─────┘                        │    │      └─────┬─────┘                        │
│            │ Docker Swarm Overlay          │    │            │ Docker Swarm Overlay          │
└────────────┼──────────────────────────────┘    └────────────┼──────────────────────────────┘
             └──────────── Swarm Overlay ─────────────────────┘
                  (커널 간: SSH, MPI, NCCL)
```

각 커널 컨테이너는 정확히 두 가지 통신 경로만 가진다:

| 경로 | 프로토콜 | 네트워크 | 용도 |
|---|---|---|---|
| 커널 → **로컬 Agent** | ZeroMQ TCP (`127.0.0.1:{mapped_port}`) | Docker 포트 매핑을 통한 호스트 loopback | 코드 실행 (포트 2000/2001의 REPL in/out), 자동완성, 인터럽트 |
| 커널 ↔ **다른 커널** (멀티 노드) | SSH, MPI, NCCL | Docker Swarm Overlay | 분산 학습, 클러스터 세션 프로세스 간 통신 |

**커널이 직접 통신하지 않는 컴포넌트:**

| 컴포넌트 | 직접 통신? | 처리 방식 |
|---|---|---|
| etcd | 아니오 | Agent가 커널을 대신하여 etcd를 읽기/쓰기 |
| Redis | 아니오 | Agent가 이벤트와 메트릭을 Redis에 발행 |
| PostgreSQL | 아니오 | Manager가 모든 DB 작업을 처리 |
| Manager | 아니오 | Agent가 세션 상태, 이벤트, 라이프사이클 작업을 중계 |

**DooD에서 이것이 중요한 이유**: 커널은 (1) Agent REPL 통신을 위한 호스트 loopback과 (2) 커널 간 통신을 위한 Docker Swarm 오버레이만 필요하므로, K8s Service DNS, K8s CNI, 또는 어떤 클러스터 내부 네트워킹에도 접근할 필요가 없다. 베어메탈에서 K8s DooD 배포로 마이그레이션할 때 커널 컨테이너 이미지는 **완전히 변경 없이** 사용할 수 있다.

**ZeroMQ REPL 상세**: Agent는 ZeroMQ TCP를 통해 커널에 연결하는 `DockerCodeRunner`를 생성한다:
- `repl_in` (컨테이너 포트 2000): Agent가 커널에 코드 전송
- `repl_out` (컨테이너 포트 2001): 커널이 Agent에 실행 결과 반환

이 포트들은 Docker에 의해 `127.0.0.1:{host_port}`로 매핑된다. Agent Pod이 `hostNetwork: true`를 사용하므로, 호스트의 loopback 인터페이스를 공유하여 이 매핑된 포트에 직접 접근할 수 있다 — 베어메탈 동작과 동일하다.

### 4.6 스토리지 아키텍처

#### 4.6.1 vfolder 마운트 경로

```
┌── K8s 노드 ──────────────────────────────────────────────────┐
│                                                               │
│  분산 스토리지 (CephFS/NFS/WekaFS)                           │
│  마운트 위치: /mnt/vfolder                                    │
│        │                                                      │
│        ├──────────────────────────────────┐                   │
│        │                                  │                   │
│  ┌─────▼──────┐                    ┌──────▼──────┐            │
│  │ Agent Pod  │                    │  커널       │            │
│  │ (vfolder   │                    │  컨테이너   │            │
│  │  메타데이터│                    │  (호스트에서 │            │
│  │  읽기)     │                    │   바인드 마운트)│         │
│  └────────────┘                    └─────────────┘            │
└───────────────────────────────────────────────────────────────┘
```

- 분산 스토리지 파일시스템은 **호스트** 노드에 마운트된다(fstab, systemd mount, 또는 CSI 드라이버를 통해).
- 에이전트 Pod은 `hostPath`를 통해 이 경로를 마운트하여 vfolder 메타데이터를 읽고 마운트 포인트를 결정한다.
- 커널 컨테이너는 Docker/containerd API를 통해 동일한 호스트 경로에서 직접 바인드 마운트를 받는다.
- **가상화 오버헤드 없음** — 바인드 마운트는 네이티브 Linux 파일시스템 작업이며, 현재 베어메탈 배포와 동일하다.

#### 4.6.2 스크래치 공간

커널 스크래치 디렉터리(커널 내부의 `/home/work`)는 호스트 로컬 스토리지(SSD/NVMe)가 지원한다. 에이전트 Pod과 커널 컨테이너 모두 호스트의 `/var/cache/backendai/scratches`에 접근한다.

#### 4.6.3 DooD 환경에서의 NFS 마운트 고려사항

현재 베어메탈 배포에서 NFS 스토리지는 호스트 OS 레벨(`fstab` 또는 `systemd`)에서 마운트된다. Agent 프로세스는 이미 마운트된 경로(`agent.toml`의 `mount-path`)를 읽고 Docker 바인드 마운트 파라미터로 커널 컨테이너에 전달할 뿐이다. Agent는 NFS를 마운트하거나 언마운트하지 **않는다** — 이미 마운트된 경로의 순수한 소비자일 뿐이다.

K8s DooD 배포에서 이는 제어 격차를 만든다: Helm 차트가 모든 Backend.AI 컴포넌트를 관리하지만, 호스트 레벨 NFS 마운트는 K8s 제어 밖에 있다. 인프라팀에게 각 노드에 NFS 마운트를 사전 구성하도록 요구하는 것은 자체 완결형 배포 목표에 어긋난다.

**옵션 A: 호스트 사전 마운트 (단순, 외부 의존성)**

NFS가 Backend.AI 배포 전에 각 노드에 마운트되며, 베어메탈과 동일하다:

| 항목 | 설명 |
|---|---|
| 마운트 방법 | `fstab`, `systemd`, `cloud-init`, 또는 노드 이미지 |
| 제어 주체 | 인프라팀 (Helm 외부) |
| Agent 재시작 영향 | 없음 — OS 레벨 마운트 |
| 노드 확장 | 새 노드에 수동 마운트 설정 필요 |
| `helm install`만으로 완료? | 아니오 |

**옵션 B: NFS Mounter DaemonSet (K8s 네이티브 배포 권장)**

전용 DaemonSet이 각 에이전트 노드에서 NFS 마운트를 처리하며, Helm 차트로 완전히 관리된다:

```
┌─── Helm 차트가 둘 다 배포 ────────────────────────────────────┐
│                                                                │
│  ┌── nfs-mounter DaemonSet ────────────────────────────────┐  │
│  │  - mountPropagation으로 각 노드에 NFS 마운트            │  │
│  │  - Agent와 독립적인 라이프사이클                        │  │
│  │  - 헬스 체크: 주기적 마운트 포인트 확인                 │  │
│  │  - 실패 시 자동 재마운트                                │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌── Agent DaemonSet ──────────────────────────────────────┐  │
│  │  - init container가 NFS 마운트 대기                     │  │
│  │  - hostPath로 /mnt/vfolder 접근 (이미 마운트됨)        │  │
│  │  - 재시작해도 NFS 마운트에 영향 없음                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌── 커널 컨테이너 (DooD) ─────────────────────────────────┐  │
│  │  - 호스트 /mnt/vfolder/...에서 Docker 바인드 마운트     │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

NFS Mounter DaemonSet:

```yaml
# templates/daemonset-nfs-mounter.yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: {{ .Release.Name }}-nfs-mounter
spec:
  selector:
    matchLabels:
      app: backendai-nfs-mounter
  template:
    spec:
      nodeSelector:
        backendai.io/role: agent
      tolerations:
        - key: nvidia.com/gpu
          operator: Exists
          effect: NoSchedule
      priorityClassName: backendai-nfs-mounter-critical
      containers:
        - name: nfs-mounter
          image: busybox:1.36
          securityContext:
            privileged: true
          command: ['sh', '-c', |
            if ! mountpoint -q /mnt/vfolder; then
              echo "Mounting NFS..."
              mount -t nfs -o {{ .Values.global.storage.nfs.mountOptions }} \
                {{ .Values.global.storage.nfs.server }}:{{ .Values.global.storage.nfs.export }} \
                /mnt/vfolder
            fi
            # 상주하면서 마운트 상태 주기적 확인
            while true; do
              if ! mountpoint -q /mnt/vfolder; then
                echo "NFS mount lost, remounting..."
                mount -t nfs -o {{ .Values.global.storage.nfs.mountOptions }} \
                  {{ .Values.global.storage.nfs.server }}:{{ .Values.global.storage.nfs.export }} \
                  /mnt/vfolder
              fi
              sleep 30
            done
          ]
          volumeMounts:
            - name: vfolder-mount
              mountPath: /mnt/vfolder
              mountPropagation: Bidirectional
          livenessProbe:
            exec:
              command: ['mountpoint', '-q', '/mnt/vfolder']
            periodSeconds: 30
            failureThreshold: 3
      volumes:
        - name: vfolder-mount
          hostPath:
            path: /mnt/vfolder
            type: DirectoryOrCreate
```

Agent DaemonSet에 NFS 마운트 대기 init container 추가:

```yaml
# Agent DaemonSet init containers에 추가
- name: wait-for-nfs
  image: busybox:1.36
  command: ['sh', '-c',
    'until mountpoint -q /mnt/vfolder; do echo "waiting for NFS mount..."; sleep 3; done']
  volumeMounts:
    - name: vfolder-storage
      mountPath: /mnt/vfolder
```

**`mountPropagation: Bidirectional` 동작 원리**: NFS Mounter Pod이 자신의 마운트 네임스페이스 안에서 `/mnt/vfolder`에 NFS를 마운트한다. `Bidirectional` 전파로 인해 이 마운트가 호스트의 마운트 네임스페이스로 전파된다. Agent Pod과 Docker 데몬은 호스트의 `/mnt/vfolder`에서 NFS 내용을 볼 수 있다. NFS Mounter Pod이 재시작되면 재마운트하고 다시 전파한다.

스토리지 설정을 위한 Helm values:

```yaml
global:
  storage:
    nfsMounter:
      enabled: true           # false = 호스트 사전 마운트 (옵션 A)
    nfs:
      server: "nfs-server.internal"
      export: "/export/vfolder"
      mountPath: "/mnt/vfolder"
      mountOptions: "vers=4.1,hard,timeo=600,retrans=2,noresvport"
```

**옵션 비교:**

| 항목 | 옵션 A (호스트 사전 마운트) | 옵션 B (NFS Mounter DaemonSet) |
|---|---|---|
| 제어 주체 | 인프라팀 | Helm 차트 |
| 노드 확장 | 새 노드에 수동 NFS 설정 | 자동 (DaemonSet이 새 노드에 배포) |
| 설정 변경 | 각 노드에 SSH | `helm upgrade` |
| 마운트 모니터링 | 별도 구성 필요 | 내장 livenessProbe + 자동 재마운트 |
| Agent 재시작 영향 | 없음 (OS 레벨 마운트) | 없음 (별도 DaemonSet) |
| `helm install`만으로 완료? | 아니오 | **예** |
| NFS Mounter Pod 재시작 | 해당 없음 | 재마운트 및 전파; `hard` 마운트 옵션 사용 시 커널 I/O가 잠시 블로킹됨 (자동 복구) |

### 4.7 GPU 및 가속기 패스스루

이 섹션은 K8s DooD 배포에서 GPU 및 가속기 패스스루가 어떻게 동작하는지 설명한다. 섹션 2.4에서 확립된 전제 — Kubernetes가 GPU 리소스를 관리하지 않으며 GPU 노드가 taint로 격리됨 — 을 기반으로 한다.

#### 4.7.1 이중 레이어 GPU 관리

GPU 관리는 명확히 정의된 책임을 가진 두 레이어로 나뉜다:

```
┌─── K8s 레이어 (GPU 미인식) ──────────────────────────────────┐
│                                                                │
│  ❌ NVIDIA device plugin         — 미배포                      │
│  ❌ nvidia.com/gpu 리소스         — 에이전트 노드에서 무의미   │
│  ✅ GPU Feature Discovery (GFD)  — 노드 라벨링만 사용          │
│  ✅ NVIDIA 드라이버 설치          — Operator로 자동화 (선택)   │
│  ✅ DCGM Exporter                — Prometheus 메트릭           │
│                                                                │
└────────────────────────────────────────────────────────────────┘
         │
         │ nodeSelector: backendai.io/role=agent
         │ toleration: backendai.io/dedicated=agent:NoSchedule
         ▼
┌─── Backend.AI 레이어 (완전한 GPU 제어) ───────────────────────┐
│                                                                │
│  Agent DaemonSet                                               │
│    ├── GPU 디바이스 발견 (/dev/nvidia* 직접 읽기)              │
│    ├── 드라이버 라이브러리 마운트 (/usr/lib/.../nvidia/*)      │
│    ├── GPU 슬롯 계산 → etcd 등록                               │
│    ├── GPU 할당과 함께 커널 컨테이너 생성                      │
│    ├── CUDA 훅 라이브러리 주입 (분할 GPU)                      │
│    └── GPU 헬스 모니터링 (nvidia-smi, XID 에러)                │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

K8s는 인프라 전제 조건(드라이버 설치, 노드 라벨링, 메트릭 수집)을 담당하지만 **GPU 할당 로직에는 절대 관여하지 않는다**. 모든 GPU 관련 결정은 Backend.AI Agent가 수행한다.

#### 4.7.2 NVIDIA 드라이버 및 Container Toolkit (호스트 레벨 전제)

섹션 2.4.5에서 확립된 바와 같이, NVIDIA 드라이버와 NVIDIA Container Toolkit은 호스트 레벨 전제 조건이며 K8s나 Helm이 관리하지 않는다. 이 섹션은 설치 접근법을 명확히 하고 NVIDIA GPU Operator의 제한된 역할을 설명한다.

##### 4.7.2.1 호스트 레벨 설치 (주 접근법)

Backend.AI를 배포하기 전에 각 에이전트 노드에 NVIDIA 드라이버와 Container Toolkit을 직접 설치한다:

```bash
# Ubuntu 예시
apt install nvidia-driver-535
apt install nvidia-container-toolkit
systemctl restart docker    # 또는 containerd

# 검증
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

이 접근법은 GPU Operator의 컨테이너화된 드라이버 설치기 대비 다음과 같은 장점을 가진다:

| 항목 | 호스트 설치 | GPU Operator 드라이버 DaemonSet |
|---|---|---|
| 설치 위치 | `/usr/lib/x86_64-linux-gnu/` (영구 디스크) | `/run/nvidia/driver/` (tmpfs, 메모리) |
| 재부팅 후 | 즉시 사용 가능 | DaemonSet이 재설치 (5-10분 지연) |
| 메모리 오버헤드 | 없음 | 노드당 500MB-1GB tmpfs |
| 디버깅 | 표준 Linux 도구 | DaemonSet Pod 로그 조사 필요 |
| Linux 배포판 지원 | 모든 배포판 | 공식 지원 배포판만 |
| Secure Boot | 표준 MOK enrollment | 추가 operator 구성 필요 |
| 드라이버 버전 제어 | 인프라팀 소유 | Helm values + Operator reconciliation |
| K8s와의 결합 | 없음 | K8s Pod 라이프사이클이 드라이버 상태에 영향 |

**권장 배포 워크플로:**

| 환경 | 방법 | 아티팩트 |
|---|---|---|
| 베어메탈 / 온프레미스 | Packer + Ansible로 드라이버가 사전 설치된 노드 이미지 빌드 | 커스텀 OS 이미지 |
| AWS | AWS Deep Learning AMI (드라이버 + 툴킷 사전 설치) | Amazon Linux 2 또는 Ubuntu DLAMI |
| GCP | GCP Deep Learning VM 이미지 또는 NVIDIA GPU 최적화 COS | 드라이버 사전 설치된 COS |
| Azure | NVIDIA 드라이버가 포함된 Azure N-series | N-series Ubuntu 이미지 |
| K3s/RKE2 | 배포판의 GPU 지원 설치기 사용 | 네이티브 통합 |

##### 4.7.2.2 NVIDIA GPU Operator (선택적 보조 도구)

NVIDIA GPU Operator는 Backend.AI K8s 배포에서 여전히 유용할 수 있지만, **드라이버나 툴킷 설치가 아닌 보조 컴포넌트에만** 사용한다. 대부분의 컴포넌트를 비활성화한 상태로 Operator를 사용한다:

```yaml
# values.yaml (NVIDIA GPU Operator)
gpu-operator:
  driver:
    enabled: false          # ❌ 호스트 레벨 설치 사용
  toolkit:
    enabled: false          # ❌ 호스트 레벨 설치 사용
  devicePlugin:
    enabled: false          # ❌ 섹션 2.4.1과 충돌 (Backend.AI가 GPU 관리)
  migManager:
    enabled: false          # ❌ 필요 시 Backend.AI가 MIG 처리
  gfd:
    enabled: true           # ✅ GPU Feature Discovery — GPU 정보로 노드 자동 라벨링
  dcgmExporter:
    enabled: true           # ✅ 관측성을 위한 Prometheus 메트릭
  nodeStatusExporter:
    enabled: true           # ✅ 노드 헬스 리포팅
```

이 구성에서 Operator가 제공하는 것:

| 컴포넌트 | 목적 | 이점 |
|---|---|---|
| GPU Feature Discovery (GFD) | `nvidia.com/gpu.product`, `nvidia.com/gpu.count`, `nvidia.com/gpu.memory`로 노드 라벨링 | Agent DaemonSet이 GPU 모델 기반 nodeSelector 사용 가능 |
| DCGM Exporter | GPU 메트릭(활용률, 온도, 메모리, ECC 에러)을 Prometheus에 노출 | 클러스터 전체 관측성 대시보드 |
| Node Status Exporter | GPU 관련 노드 조건 보고 | K8s 모니터링 스택과 통합 |

Operator는 **필수가 아니다**. GFD와 DCGM 메트릭이 필요하지 않으면 Operator를 완전히 건너뛸 수 있다 — Backend.AI는 호스트 레벨 드라이버와 툴킷만으로 정상 동작한다.

##### 4.7.2.3 왜 GPU Operator로 드라이버를 설치하지 않는가?

GPU Operator의 드라이버 설치는 교묘하지만 복잡한 접근이다: privileged DaemonSet이 컨테이너 내부에서 커널 모듈을 컴파일하고 호스트 tmpfs 경로에 설치한다. 이 방식은 동작하지만, 프로덕션 Backend.AI 배포에 대해 상당한 운영상 단점이 있다:

1. **재부팅 복구가 느림**: 노드 재부팅 후 드라이버 DaemonSet이 재스케줄되고, 드라이버 이미지를 pull하고, 모듈을 컴파일하고, 설치해야 한다. 5-10분이 소요되며, 이 동안 노드는 GPU 접근이 불가능하다.
2. **메모리 오버헤드**: `/run/nvidia/driver`(tmpfs)에 저장된 드라이버 파일이 노드당 500MB-1GB RAM을 영구적으로 소비한다.
3. **커널에 대한 취약한 의존성**: 커널 업그레이드 시 드라이버 컨테이너가 재컴파일해야 한다. 컨테이너의 커널 소스 패키지가 사용 불가하거나 호환되지 않으면 드라이버 설치 실패.
4. **비정상적인 디버깅 경로**: GPU 이슈를 표준 호스트 도구 대신 드라이버 Pod의 `kubectl logs`로 진단해야 한다.
5. **제한된 배포판 지원**: 특정 Ubuntu, RHEL, SLES 버전만 공식 지원. 다른 배포판(Arch, Debian minor 버전, 커스텀 커널)은 미지원.
6. **Secure Boot 복잡성**: 컨테이너화된 환경에서 서명된 모듈을 위한 추가 MOK(Machine Owner Key) 관리 필요.
7. **Operator 라이프사이클 결합**: GPU Operator 배포가 삭제되거나 업그레이드되면 드라이버 상태가 불일치해질 수 있음.

이러한 이유로, Backend.AI 배포는 NVIDIA 드라이버를 다른 호스트 레벨 시스템 소프트웨어(커널, Docker daemon, kubelet)와 동일하게 취급해야 한다 — K8s가 아닌 노드 프로비저닝 레이어에서 설치 및 관리.

#### 4.7.3 Agent Pod의 GPU 접근

Backend.AI Agent Pod은 다음 용도로 GPU 디바이스와 드라이버 라이브러리에 접근해야 한다:

1. **시작 시 GPU 발견** — GPU 열거, 모델/메모리 조회
2. **헬스 모니터링** — 주기적 `nvidia-smi` 쿼리
3. **리소스 슬롯 계산** — etcd에 GPU 슬롯 보고
4. **할당 결정** — 각 커널 컨테이너에 할당할 GPU 결정

GPU 접근이 가능한 Agent DaemonSet 구성:

```yaml
spec:
  template:
    spec:
      nodeSelector:
        backendai.io/role: agent
        nvidia.com/gpu.present: "true"      # GFD가 제공하는 라벨
      tolerations:
        - key: backendai.io/dedicated
          operator: Equal
          value: agent
          effect: NoSchedule
      containers:
        - name: agent
          securityContext:
            privileged: true
          env:
            - name: LD_LIBRARY_PATH
              value: "/usr/local/nvidia/lib64:/usr/local/nvidia/lib"
            - name: PATH
              value: "/usr/local/nvidia/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
          volumeMounts:
            # GPU 디바이스 파일 (privileged로 모든 /dev/nvidia* 접근 가능)
            - name: dev
              mountPath: /dev
            # 호스트에서 NVIDIA 드라이버 라이브러리
            - name: nvidia-driver
              mountPath: /usr/local/nvidia
              readOnly: true
      volumes:
        - name: dev
          hostPath:
            path: /dev
        - name: nvidia-driver
          hostPath:
            path: /run/nvidia/driver        # GPU Operator 마운트 포인트
            type: Directory
```

**대안: Agent 이미지를 NVIDIA CUDA 베이스로 빌드**. Agent 이미지를 `nvidia/cuda:12.x-base`에서 빌드하고 NVIDIA Container Runtime을 사용한다. Agent Pod이 생성될 때 NVIDIA 런타임이 드라이버 라이브러리와 디바이스를 자동으로 컨테이너에 마운트한다. Pod 스펙이 단순해지지만 Agent 이미지의 CUDA 버전이 호스트 드라이버 버전과 일치해야 한다.

#### 4.7.4 커널 컨테이너 GPU 할당

Agent가 GPU 접근으로 실행되면, 커널 컨테이너 GPU 할당은 현재 베어메탈 모델과 동일하게 동작한다. Agent는 Docker/containerd API를 직접 사용하여 각 커널 컨테이너에 GPU 디바이스, 라이브러리, 환경변수를 연결한다.

| 기능 | 메커니즘 | 호환성 |
|---|---|---|
| 단일 GPU 할당 | Docker API의 `--device /dev/nvidia0` | 베어메탈과 동일 |
| 멀티 GPU 할당 | 다중 `--device` 플래그 또는 `--gpus '"device=0,1"'` | 베어메탈과 동일 |
| 분할 GPU (cuda.shares) | `generate_hooks()` + `LD_PRELOAD`로 CUDA 훅 라이브러리 주입 | 호스트에 훅 라이브러리 필요 (4.7.5 참조) |
| NVIDIA Container Toolkit | `--gpus all` 플래그 또는 CDI 디바이스 스펙 | 호스트에 툴킷 설치 필요 |
| MIG (Multi-Instance GPU) | MIG UUID를 디바이스로 주입 | 호스트 레벨 MIG 파티셔닝 필요 (4.7.6 참조) |
| NUMA 인식 배치 | CPU 피닝 + GPU 어피니티 힌트 | 호스트 `/sys`의 NUMA 토폴로지 사용 |
| ROCm (AMD) | `/dev/kfd`, `/dev/dri/*` 디바이스 파일 | 컴퓨트 플러그인이 디바이스 결정 |
| Habana, IPU, Rebellions, XPU | 플러그인별 디바이스 경로 | 각 컴퓨트 플러그인이 처리 |

Agent가 베어메탈과 동일한 Docker/containerd API 코드 경로를 사용하므로, **가속기 플러그인 시스템에 변경이 필요 없다**. DooD 아키텍처는 Backend.AI의 GPU 관리 전체 기능 세트를 보존한다.

#### 4.7.5 분할 GPU Hook Library 배포

Backend.AI의 분할 GPU 공유는 `LD_PRELOAD`로 주입되는 CUDA 훅 라이브러리(`libbaicuda.so`)에 의존한다. Agent의 `generate_hooks()` 메서드가 이 라이브러리의 호스트 경로를 반환하며, 커널 컨테이너에 바인드 마운트된다.

K8s DooD 배포에서는 훅 라이브러리가 **호스트** 파일시스템의 알려진 경로에 있어야 한다. 세 가지 배포 옵션:

| 옵션 | 설명 | 복잡도 | 버전 관리 |
|---|---|---|---|
| **A. Agent 이미지 번들** | Agent 이미지에 `.so` 파일 포함; init container가 hostPath에 복사 | 낮음 | Agent 업그레이드 시 자동 |
| **B. 전용 installer DaemonSet** | 별도 DaemonSet이 호스트에 라이브러리 배포 | 중간 | Agent 버전과 독립 |
| **C. 노드 이미지 사전 설치** | 노드 OS 이미지에 라이브러리 포함 | 중간 | 노드 재프로비저닝 필요 |

**권고: 옵션 A (Agent 이미지 번들)**. 라이브러리 버전이 Agent 버전과 자동으로 동기화되며, Helm 업그레이드가 배포를 처리한다:

```yaml
# Agent DaemonSet init container
initContainers:
  - name: install-cuda-hook
    image: "{{ .Values.agent.image.repository }}:{{ .Values.agent.image.tag }}"
    command:
      - sh
      - -c
      - |
        mkdir -p /host/opt/backendai/hooks
        cp /opt/backendai/hooks/libbaicuda.so /host/opt/backendai/hooks/
        chmod 755 /host/opt/backendai/hooks/libbaicuda.so
    volumeMounts:
      - name: host-backendai-hooks
        mountPath: /host/opt/backendai/hooks
volumes:
  - name: host-backendai-hooks
    hostPath:
      path: /opt/backendai/hooks
      type: DirectoryOrCreate
```

Agent의 `generate_hooks()`가 `/opt/backendai/hooks/libbaicuda.so`를 반환하며, Docker가 이를 각 커널 컨테이너에 바인드 마운트한다. 커널의 `LD_PRELOAD` 환경변수가 시작 시 이 라이브러리를 로드하도록 설정된다.

#### 4.7.6 MIG 파티셔닝

NVIDIA H100/A100의 Multi-Instance GPU (MIG) 파티셔닝은 Agent가 GPU를 열거하기 **전에** 호스트 레벨 구성이 완료되어야 한다. MIG 파티션 관리 옵션:

| 옵션 | 설명 | 트레이드오프 |
|---|---|---|
| **노드 프로비저닝 시** | cloud-init 또는 Ansible로 노드 부트스트랩 중 MIG 파티션 설정 | 정적 — 파티션 레이아웃 변경 시 재프로비저닝 필요 |
| **NVIDIA GPU Operator MIG Manager** | Operator의 MIG Manager 컴포넌트 | 섹션 4.7.2에 따라 **비활성화** — device plugin과 결합됨 |
| **수동 nvidia-smi** | 클러스터 관리자가 노드별로 `nvidia-smi mig -cgi ...` 실행 | 운영 부담 |
| **향후: Backend.AI Agent 동적 MIG** | Agent가 할당 요청에 따라 MIG 파티셔닝 | 현재 미구현 |

**현재 권고**: 노드 프로비저닝 시 정적으로 MIG 파티션을 설정한다. Agent가 `nvidia-smi -L`로 MIG 인스턴스를 감지하고 각 MIG UUID를 별도 GPU 슬롯으로 etcd에 등록한다. 커널 컨테이너는 `NVIDIA_VISIBLE_DEVICES` 환경변수를 통해 특정 MIG UUID를 받는다.

#### 4.7.7 GPU 헬스 모니터링 및 장애 처리

K8s 관리 Pod과 달리, 커널 컨테이너 GPU 장애는 K8s 스케줄러에 보이지 않는다 (설계 의도 — 섹션 2.4.1). Backend.AI Agent가 GPU 헬스 모니터링과 복구를 단독으로 책임진다.

**Agent의 GPU 헬스 루프:**

```
N초마다 (설정 가능):
  1. 모든 GPU에 대해 `nvidia-smi -q` 실행
  2. XID 에러 카운트, ECC 에러, 온도, 파워 상태 파싱
  3. 각 GPU에 대해:
     - XID 치명적 에러 → 슬롯을 etcd에서 unavailable로 마킹
     - ECC 복구 불가 에러 카운트 증가 → 슬롯을 degraded로 마킹
     - 온도 > 임계값 → 경고 로그, 실패 처리하지 않음
  4. 노드의 모든 GPU가 unavailable이면:
     - Manager에 GPU 슬롯 0 보고
     - 선택적으로 K8s API를 호출하여 노드 cordon (RBAC 필요)
     - Manager가 이 노드에 새 세션 스케줄링 중단
  5. Manager 알림을 위해 Redis에 헬스 이벤트 발행
```

**K8s와의 상호작용:**

- **DCGM Exporter** (GPU Operator 제공)는 Agent 자체 모니터링과 독립적으로 GPU 메트릭을 Prometheus에 발행한다. 클러스터 운영자는 이 메트릭으로 대시보드를 구성할 수 있지만 Agent는 이를 소비하지 않는다.
- **Node Problem Detector** (선택)는 NVIDIA 드라이버 크래시를 감지하여 K8s 노드를 NotReady로 마킹하도록 구성할 수 있다. 이는 Agent Pod을 축출하지만 커널 컨테이너에는 영향 없음 (DooD로 실행되므로).
- **K8s API를 통한 Cordon**은 선택 사항. Agent에 RBAC 권한이 있으면 `kubectl cordon`과 동등한 호출로 새 Pod(다른 Backend.AI DaemonSet이 있다면) 스케줄링을 방지할 수 있다. 기존 커널 컨테이너에는 영향 없음.

**복구**: 수동 드라이버 리셋(`nvidia-smi --gpu-reset`) 또는 노드 재부팅. Agent가 재시작 시 GPU를 재열거하고 정상 GPU 풀에 다시 참여한다. 실패한 GPU를 사용 중인 커널 컨테이너는 종료되고 Manager가 재스케줄해야 한다.

#### 4.7.8 컴퓨트 플러그인 이미지 전략

Backend.AI의 가속기 플러그인(`backendai_accelerator_cuda`, `backendai_accelerator_rocm`, `backendai_accelerator_xpu`, `backendai_accelerator_habana` 등)은 Agent 프로세스 시작 시 로드된다. K8s 배포에서 이 플러그인을 Agent 이미지로 배포하는 두 가지 전략이 있다:

| 전략 | 설명 | 장점 | 단점 |
|---|---|---|---|
| **단일 통합 이미지** | 하나의 Agent 이미지에 모든 플러그인 포함; 런타임에 하드웨어 감지 후 적절한 플러그인 활성화 | 단일 이미지 관리; 단순한 Helm values | 이미지 크기 증가; 미사용 플러그인 로드 |
| **벤더별 이미지** | 별도 이미지: `backendai-agent-cuda`, `backendai-agent-rocm`, `backendai-agent-xpu` | 작은 이미지; 명확한 의존성 | 이미지 매트릭스 관리 부담; 노드 타입별 DaemonSet 선택 필요 |

**권고: 단일 통합 이미지**. 크기 오버헤드는 미미하며(플러그인 코드는 CUDA/ROCm 라이브러리에 비해 작음), 더 단순한 배포 모델이 운영 복잡도를 줄인다. Agent는 시작 시 다음을 통해 사용 가능한 하드웨어를 감지한다:

1. 노드 라벨 (`nvidia.com/gpu.product`, `amd.com/gpu.family`) — GFD 또는 유사한 것이 배포된 경우
2. 직접 하드웨어 프로빙 (`lspci`, `/dev/nvidia*`, `/dev/kfd`)
3. `agent.toml` 또는 환경변수 설정

이종 클러스터(예: NVIDIA H100 노드 + AMD MI300 노드)의 경우, 엄격한 이미지 분리가 필요하면 nodeSelector를 가진 벤더별 DaemonSet을 사용할 수 있다:

```yaml
# values.yaml
agent:
  daemonsets:
    - name: agent-nvidia
      nodeSelector:
        nvidia.com/gpu.present: "true"
      image:
        tag: "25.12.0-cuda"
    - name: agent-amd
      nodeSelector:
        amd.com/gpu.present: "true"
      image:
        tag: "25.12.0-rocm"
```

이 방식은 단일 values 구성에서 여러 DaemonSet을 생성하기 위해 Helm 템플릿이 필요하다.

#### 4.7.9 VM 기반 격리 대안 (외부 문서)

DooD 컨테이너가 제공하는 격리보다 더 강한 격리가 필요한 환경 — 신뢰할 수 없는 코드의 멀티테넌시, 규제 준수, 기밀 컴퓨팅 — 에서는 기본 DooD 아키텍처와 함께 VM 기반 격리 런타임(Kata Containers, KubeVirt)이 지원되어야 한다.

VM 런타임 지원은 상당한 아키텍처 고려사항, GPU 제약, 운영 전략, 12개 레이어에 걸친 시스템 전반 변경 사항을 포함하므로, **별도의 동반 문서**로 분리되어 있다:

**📄 [Backend.AI VM 런타임 지원: Kata Containers와 KubeVirt](./support_vm_kata.ko.md)**

해당 문서가 다루는 내용:

- **배경**: DooD와 함께 VM 격리가 지원되어야 하는 이유 (보안, 규제 준수, 기밀 컴퓨팅)
- **런타임 옵션**: Kata Containers vs KubeVirt vs DooD 비교
- **GPU + VM 제약**: Firecracker를 사용할 수 없는 이유, VM 풀링이 GPU에서 실패하는 이유, GPU cold start 현실 (30초~수 분)
- **운영 전략**: 세션별 runtime class 선택, 전용 GPU 풀, NVIDIA vGPU/MIG 통합, 하이브리드 노드를 위한 GPU별 드라이버 바인딩
- **하이브리드 런타임 아키텍처**: taint 기반 풀 분리를 가진 멀티 런타임 클러스터 설계
- **시스템 전반 변경 사항**: 12개 아키텍처 레이어에 걸친 55개 필요 변경 (Agent 코어, 커널 통신, GPU 할당, 스토리지, 네트워킹, 이미지 관리, 스케줄러, 노드 인프라, 모니터링, Helm, API/CLI/UI, 테스트 인프라)
- **점진적 구현 로드맵**: 12-18개월에 걸친 4단계 접근
- **결정 게이트**: VM 런타임 지원에 착수하기 전 평가 기준

**이 문서 맥락에서의 핵심 시사점:**

| 측면 | 상태 |
|---|---|
| VM 런타임 지원 필요성 | 예 (보안/규제 시나리오) |
| 기본 런타임 | DooD (일반 워크로드용으로 유지) |
| 구현 영향 | 12-18개월, 2-3명 엔지니어, 12 레이어 변경 |
| 현재 4.7.1-4.7.8 설계와의 호환성 | 예 (DooD 주력, VM 런타임은 옵트인) |

---

## 5. 컨테이너 런타임 분석: Docker vs containerd

### 5.1 Docker를 이용한 DooD (docker.sock)

이 모델에서 호스트는 Docker 데몬(`dockerd`)을 실행하고, 에이전트 Pod이 `/var/run/docker.sock`을 마운트한다:

```
Agent Pod ──(docker.sock)──▶ dockerd ──▶ containerd ──▶ runc ──▶ 커널 컨테이너
```

Backend.AI 에이전트는 Docker Engine API(Unix 소켓을 통한 REST)와 통신하는 `aiodocker` 라이브러리를 사용한다. 이것이 현재 프로덕션 모델이다.

**장점:**
- **에이전트 코드 변경 불필요**: 기존 `DockerAgent` 구현체가 그대로 동작한다.
- **Docker Compose 호환성**: Docker Compose를 사용하는 개발 및 테스트 워크플로우가 유지된다.
- **Docker Swarm 오버레이**: Docker Swarm 오버레이 네트워크를 통한 멀티 노드 세션 네트워킹이 프로덕션에서 검증되어 있다.
- **성숙한 도구**: 디버깅 및 운영을 위한 `docker exec`, `docker logs`, `docker stats`.
- **이미지 관리**: 잘 이해된 라이프사이클의 `docker pull`, `docker build`, `docker tag`.
- **NVIDIA Container Toolkit**: `nvidia-docker2` 또는 `nvidia-container-toolkit` 패키지를 통한 완전한 통합.

**단점:**
- **추가 데몬**: Docker 데몬(`dockerd`)이 노드의 추가 프로세스로, 메모리 오버헤드(50-100MB)와 잠재적 단일 장애점을 추가한다.
- **계층화된 아키텍처**: Docker → containerd → runc는 컨테이너 작업에 레이턴시를 추가한다.
- **K8s CRI 충돌**: 최신 K8s(1.24+)는 containerd를 CRI로 직접 사용한다. Docker를 함께 실행하면 동일 노드에 두 개의 컨테이너 런타임이 존재하여, 어떤 런타임이 어떤 컨테이너를 관리하는지 혼란이 발생할 수 있다.
- **Dockershim 제거**: Kubernetes는 1.24에서 dockershim을 제거했다. Docker는 더 이상 일급 K8s 런타임이 아니지만, DooD 목적의 독립 데몬으로는 여전히 실행 가능하다.
- **공격 표면**: Docker 데몬이 root 권한으로 실행되며 넓은 capability를 가짐. 소켓 탈취 시 전체 호스트 접근 권한이 부여된다.

### 5.2 containerd를 이용한 DooD (containerd.sock)

이 모델에서 에이전트는 containerd(K8s가 이미 CRI 런타임으로 사용)와 직접 통신한다:

```
Agent Pod ──(containerd.sock)──▶ containerd ──▶ runc ──▶ 커널 컨테이너
```

에이전트는 containerd 클라이언트 라이브러리(예: gRPC를 통한 `containerd` Python 바인딩, 또는 Docker 호환 인터페이스인 `nerdctl` CLI)를 사용한다.

**장점:**
- **단일 런타임**: containerd가 이미 모든 K8s 노드에서 실행 중이다. 추가 데몬이 필요 없다.
- **낮은 오버헤드**: 데몬 프로세스 하나 적음(no `dockerd`), 노드당 50-100MB 메모리 절감.
- **네이티브 K8s 정합**: containerd로 생성된 컨테이너를 별도 네임스페이스(예: `backendai.io`)에 배치하여 K8s 관리 컨테이너와의 간섭을 방지할 수 있다.
- **단순한 아키텍처**: Agent → containerd → runc (한 레이어 적음).
- **보안**: containerd 소켓은 Docker 소켓보다 작은 공격 표면을 가진다. 세밀한 네임스페이스 격리가 가능하다.
- **CDI (Container Device Interface)**: containerd가 표준화된 디바이스(GPU) 관리를 위한 CDI를 네이티브로 지원하며, 이는 NVIDIA 컨테이너 통합의 미래 방향이다.

**단점:**
- **에이전트 코드 변경 필요**: `DockerAgent`가 `aiodocker`(Docker Engine API)를 사용한다. containerd로 전환하려면:
  - containerd의 gRPC API를 사용하도록 컨테이너 관리 재작성 (상당한 노력).
  - containerd의 Docker 호환 CLI 래퍼인 `nerdctl` 사용 (중간 노력, 다만 CLI 의존성 추가). `nerdctl`은 개발 및 디버그 용도로만 적합하다. 프로덕션에서는 containerd의 비동기 gRPC API 또는 CRI gRPC API를 직접 사용해야 한다.
  - CRI(Container Runtime Interface) gRPC API 직접 사용 (중간 노력).
- **Swarm 오버레이 없음**: containerd에는 Docker Swarm의 내장 오버레이 네트워크가 없다. 멀티 노드 세션 네트워킹에 대안(예: CNI 플러그인 직접 호출, WireGuard, 커스텀 오버레이 솔루션)이 필요하다.
- **이미지 관리 차이**: containerd는 네임스페이스 기반 이미지 저장소를 사용한다. 이미지 pull/tag 작업이 Docker CLI 관례와 다르다.
- **NVIDIA Container Toolkit**: CDI 또는 `nvidia-ctk` 런타임 설정을 통해 지원되지만, 통합 경로가 Docker 기반 모델과 다르다.
- **디버깅 UX**: `ctr`과 `nerdctl`은 `docker` CLI보다 인체공학적이지 않다.

### 5.3 기능 동등성 매트릭스

| 기능 | Docker (docker.sock) | containerd (containerd.sock) | 격차 평가 |
|---|---|---|---|
| 컨테이너 생성/시작/중지/삭제 | 완전 (Docker Engine API) | 완전 (containerd gRPC / CRI) | 동등 |
| 컨테이너 exec | 완전 (`docker exec`) | 완전 (`ctr tasks exec` / CRI ExecSync) | 동등 |
| 컨테이너 로그 (stdout/stderr) | 완전 (Docker API 스트림) | 완전 (containerd 로그 API) | 동등 |
| 컨테이너 통계 (CPU, 메모리, I/O) | 완전 (Docker API 스트림) | 완전 (containerd 메트릭 API) | 동등 |
| 이미지 pull/push/tag | 완전 (Docker API) | 완전 (containerd API, 다른 시맨틱) | 경미한 차이 (네임스페이스) |
| 이미지 빌드 | 완전 (`docker build`) | BuildKit(독립) 또는 `nerdctl build` | 동등 (BuildKit) |
| 바인드 마운트 | 완전 | 완전 | 동등 |
| GPU 디바이스 매핑 | 완전 (`--gpus`, `--device`) | 완전 (CDI, `--device`) | 동등 (CDI 선호) |
| CPU/메모리 제한 | 완전 (cgroup) | 완전 (cgroup) | 동등 |
| 네트워크: 브릿지 | 완전 (docker0 브릿지) | 완전 (CNI 브릿지 플러그인) | 동등 |
| 네트워크: 오버레이 (멀티 노드) | 완전 (Docker Swarm 오버레이) | **내장 없음** | **유의미한 격차** |
| 네트워크: 호스트 | 완전 (`--net=host`) | 완전 (호스트 네임스페이스) | 동등 |
| NVIDIA Container Toolkit | 완전 (nvidia-docker2) | 완전 (CDI / nvidia-ctk) | 동등 |
| CUDA 훅 라이브러리 주입 | 완전 (Docker를 통한 OCI 훅) | 완전 (containerd를 통한 OCI 훅) | 동등 |
| 컨테이너 라벨/어노테이션 | 완전 | 완전 (containerd 컨테이너의 라벨) | 동등 |
| 헬스 체크 | 완전 (Docker HEALTHCHECK) | 내장 없음 (애플리케이션 레벨) | 경미한 격차 |
| Docker Compose | 완전 | `nerdctl compose` | 동등 (nerdctl 사용 시) |
| 컨테이너 재시작 정책 | 완전 | 제한적 (애플리케이션 레벨) | 경미한 격차 |
| Python 클라이언트 라이브러리 | aiodocker (성숙, async) | 성숙한 async Python 라이브러리 없음 | **유의미한 격차** |

### 5.4 성능 비교

| 지표 | Docker | containerd | 차이 |
|---|---|---|---|
| 컨테이너 생성 레이턴시 | ~200-300ms | ~150-250ms | containerd ~20% 빠름 (dockerd 경유 없음) |
| 컨테이너 시작 레이턴시 | ~100-200ms | ~80-150ms | containerd ~20% 빠름 |
| 메모리 오버헤드 (데몬) | ~50-100MB (dockerd) + containerd | containerd만 (~30-50MB) | containerd가 노드당 ~50-100MB 절감 |
| 이미지 pull 처리량 | 동등 | 동등 | 동등 (Docker도 내부적으로 containerd 사용) |
| 컨테이너 exec 레이턴시 | ~50ms | ~30ms | containerd ~40% 빠름 |
| I/O 성능 (바인드 마운트) | 네이티브 | 네이티브 | 동등 (둘 다 runc 사용) |
| GPU 컴퓨트 성능 | 네이티브 | 네이티브 | 동등 (VFIO/CDI 패스스루) |

성능 차이는 미미하다. Backend.AI의 사용 사례(장시간 AI/ML 세션)에서 컨테이너 생성 레이턴시 차이(50-100ms)는 세션 설정 시간(이미지 pull, 스토리지 마운트, GPU 초기화)에 비해 무시할 수 있다.

### 5.5 보안 비교

| 측면 | Docker | containerd | 평가 |
|---|---|---|---|
| 소켓 접근 = root | 예 (docker.sock = 전체 root) | 예 (containerd.sock = 전체 root) | 동등한 리스크 |
| 네임스페이스 격리 | 단일 네임스페이스 | 멀티 네임스페이스 (K8s, backendai) | containerd 우위 |
| 공격 표면 | 큼 (Docker API + containerd) | 작음 (containerd만) | containerd 우위 |
| 루트리스 모드 | 지원 (rootless Docker) | 지원 (rootless containerd) | 동등 |
| Seccomp 프로파일 | 완전 | 완전 | 동등 |
| AppArmor/SELinux | 완전 | 완전 | 동등 |
| 이미지 서명 검증 | Docker Content Trust | containerd + cosign/notation | 동등 |

**핵심 보안 고려사항**: 두 모델 모두 에이전트 Pod이 컨테이너 런타임 소켓에 접근해야 하며, 이는 사실상 노드에 대한 root 동등 접근 권한을 부여한다. 이는 DooD 모델의 본질적인 트레이드오프이다. 완화 방법:
- 에이전트 DaemonSet이 실행되는 노드 제한 (nodeSelector, taints/tolerations)
- K8s RBAC를 사용하여 DaemonSet 생성 가능한 ServiceAccount 제한
- 에이전트 Pod 통신 제한을 위한 네트워크 정책
- 비에이전트 워크로드에 대한 PodSecurityAdmission 정책
- GPU 노드를 전용 노드 풀로 분리하고, taint를 적용하여 Backend.AI 에이전트 워크로드만 스케줄되도록 제한. 이를 통해 런타임 소켓 접근 권한이 GPU가 없는 범용 노드로 확산되는 것을 방지한다.

### 5.6 운영 복잡도

| 측면 | Docker | containerd | 평가 |
|---|---|---|---|
| 노드 설정 | Docker 설치 + 설정 | 이미 존재 (K8s CRI) | containerd 단순 |
| 에이전트 배포 | docker.sock 마운트 | containerd.sock 마운트 | 동등 |
| 디버깅 | `docker ps`, `docker logs`, `docker exec` | `nerdctl`/`ctr` (덜 익숙) | Docker 용이 |
| 모니터링 | Docker stats API, cAdvisor | containerd 메트릭, cAdvisor | 동등 |
| 멀티 노드 네트워킹 | Docker Swarm (내장) | 별도 솔루션 필요 | Docker 용이 |
| 이미지 레지스트리 인증 | `~/.docker/config.json` | containerd config.toml | Docker 용이 |
| 업그레이드 경로 | Docker 독립 릴리스 | K8s와 함께 containerd 업그레이드 | containerd 단순 |
| K8s와의 공존 | 노드에 두 개 런타임 | 단일 런타임 | containerd 단순 |

### 5.7 런타임 선택 권고

#### 권고: **초기 배포에는 Docker; 장기적으로는 containerd를 목표**

**Phase 1 (즉시): Docker 기반 DooD**

- **근거**: 에이전트 코드 변경 불필요. 기존 `DockerAgent` + `aiodocker` 스택이 즉시 동작한다. 멀티 노드 세션을 위한 Docker Swarm 오버레이 네트워킹이 프로덕션에서 검증되어 있다. GPU 통합 경로(`nvidia-docker2`, `generate_docker_args()`, `generate_hooks()`)가 변경 없이 유지된다.
- **배포**: K8s 워커 노드에 containerd와 함께 Docker 데몬을 설치(K8s는 Pod에 containerd를 사용; Backend.AI는 커널 컨테이너에 Docker를 사용).
- **트레이드오프**: 동일 노드에 두 개의 컨테이너 런타임. 운영 단순성과 전달 속도가 우선인 초기 배포에서는 허용 가능.
- **네트워크 성능**: Docker Swarm 오버레이는 현재 베어메탈 프로덕션 배포에서 멀티 노드 세션에 이미 사용되고 있다. K8s + Docker DooD로 이동해도 네트워킹 경로는 변경되지 않는다 — 커널 컨테이너는 이전과 동일한 Swarm 오버레이를 사용한다. 현재 프로덕션 배포 대비 **네트워크 성능 저하가 없다.**

**Phase 2 (중기): containerd 런타임 + 분리 CNI 네트워킹**

- **근거**: containerd로 컨테이너 관리를 전환하여 이중 런타임 복잡성을 제거하되, K8s CNI를 비-Pod 컨테이너와 공유하는 리스크를 회피한다. K8s Pod 네트워크와 완전히 독립적인 자체 IP 주소 대역을 가진 별도 CNI 설정을 사용한다.
- **필요 작업**:
  1. containerd의 async gRPC API를 사용하는 `ContainerdAgent` 구현체 개발(nerdctl CLI가 아닌).
  2. Backend.AI 커널 컨테이너를 위한 별도 CNI 네트워크 구성(`--cni-netconfpath`로 자체 IPAM/CIDR을 가진 전용 설정 디렉터리 지정).
  3. 크로스 노드 커널 통신을 위해 전용 VXLAN 오버레이(예: 독립 Flannel 인스턴스) 사용 또는 AppProxy를 통해 트래픽 라우팅.
  4. GPU 디바이스 매핑을 CDI(Container Device Interface)로 마이그레이션.
  5. containerd의 OCI 훅 지원을 통한 CUDA 훅 라이브러리 주입 검증.
- **핵심 이점**: K8s IPAM 충돌, NetworkPolicy 간섭, kubelet GC가 알려지지 않은 엔드포인트를 정리하는 리스크가 제로. Backend.AI 네트워크가 K8s 네트워킹과 완전히 격리된다.
- **예상 노력**: 3-4개월의 엔지니어링 작업.

**Phase 3 (장기): CNI 네이티브 통합**

- **근거**: DooD 커널 컨테이너에 대한 K8s CNI(Calico/Cilium) 완전 통합으로, K8s Pod과 Backend.AI 커널 간 통합 라우팅, 정책 적용, 관측성을 제공한다.
- **세 가지 가능한 접근법** (조직 표준에 맞춰 선택):

  | 접근법 | 메커니즘 | 장점 | 단점 |
  |---|---|---|---|
  | **CNI 직접 호출** | 소형 Go 헬퍼 데몬이 커널 컨테이너 netns에 대해 CNI ADD/DEL 호출. K8s Pod과의 IPAM 충돌 방지를 위해 전용 IP 풀/블록 사용. | 가장 단순한 통합; 기존 CNI 인프라 재사용 | 비-Pod 엔드포인트에 NetworkPolicy 미적용; 고아 엔드포인트 정리를 위한 GC 데몬 필요 |
  | **Calico/Cilium 네이티브** | Calico WorkloadEndpoint CRD 또는 Cilium 엔드포인트 API를 통해 비-Pod 엔드포인트 등록. | K8s Pod과 완전한 정책/관측성 동등성 | 제품/버전 의존성; CRD/오퍼레이터 통합 필요 |
  | **CRI 기반 PodSandbox** | 에이전트가 CRI API를 통해 PodSandbox 유사체를 생성, containerd가 CNI를 자연스럽게 호출하도록 유도. | 가장 "K8s 네이티브"; kubelet 호환 라이프사이클 | 구현 복잡도 최고; kubelet 상태 충돌 리스크 |

- **모든 접근법의 운영 요구사항**:
  - **IPAM 격리**: Backend.AI 커널 컨테이너를 위한 전용 CIDR/IP 블록. K8s Pod과 동일한 IP 풀을 절대 공유하지 않음.
  - **엔드포인트 GC**: 에이전트 재시작/크래시 복구 시 네트워크 상태 정합 — 고아 veth 쌍 정리, CNI DEL을 통한 누수 IP 반환.
  - **관측성**: 서비스 노출은 직접 NodePort 매핑이 아닌 AppProxy를 통해 일관된 라우팅과 가시성 유지.
- **예상 노력**: 선택한 접근법에 따라 6-12개월.

**배포 시나리오별 결정 매트릭스:**

| 시나리오 | 권고 런타임 | 근거 |
|---|---|---|
| 기존 Docker 기반 배포의 K8s 마이그레이션 | Docker | 마이그레이션 리스크 제로; 검증된 스택 |
| 신규 K8s 배포 (단일 노드 세션만) | containerd | 단순함; Swarm 의존성 없음 |
| 멀티 노드 세션이 필요한 신규 배포 | Docker | Swarm 오버레이가 가장 단순한 멀티 노드 솔루션 |
| 최소 리소스의 엣지 배포 | containerd | 낮은 메모리 오버헤드 |
| 에어갭 / 고보안 환경 | containerd | 작은 공격 표면, 단일 런타임 |

### 5.8 containerd DooD를 위한 CNI 통합 전략

Docker에서 containerd로 전환할 때 가장 중요한 과제는 컨테이너 런타임 자체가 아니라 **네트워킹**이다. Docker Swarm은 멀티 노드 세션에 "그냥 동작하는" 내장 오버레이 네트워크를 제공한다. containerd에는 동등한 것이 없으므로, 네트워킹을 명시적으로 설계해야 한다.

#### 5.8.1 K8s CNI 공유가 위험한 이유

비-Pod 컨테이너에 대해 K8s CNI(Calico/Cilium)를 직접 호출하면 즉시 드러나지 않는 여러 리스크가 존재한다:

| 리스크 | 설명 | 심각도 |
|---|---|---|
| kubelet GC 간섭 | kubelet이 자신이 모르는 컨테이너의 네트워크 리소스를 주기적으로 가비지 컬렉션함. 비-Pod 엔드포인트가 예기치 않게 정리될 수 있음. | 높음 |
| NetworkPolicy 공백 | K8s NetworkPolicy는 Pod 라벨/셀렉터 기반으로 적용됨. 비-Pod 엔드포인트에는 K8s 메타데이터가 없어 정책이 적용되지 않거나 잘못 적용됨(예: Cilium이 "world" identity로 분류). | 중간 |
| 크래시 시 IPAM 누수 | 에이전트가 CNI DEL을 호출하지 않고 크래시하면 할당된 IP가 수동 정리 전까지 누수됨. kubelet은 자체 Pod에 대해 이를 자동 처리함. | 높음 |
| 상태 불일치 | CNI 플러그인의 내부 상태(Calico의 WorkloadEndpoint, Cilium의 eBPF 맵)가 에이전트 재시작 후 실제 컨테이너 상태와 불일치할 수 있음. | 중간 |

#### 5.8.2 권장 단계적 접근

```
Phase 2: containerd + 분리 CNI
    ┌──────────────────────────────────────────────────────────┐
    │  K8s CNI (Calico/Cilium)     Backend.AI CNI (별도)      │
    │  ┌──────────────┐            ┌────────────────────┐     │
    │  │ Pod CIDR:    │            │ BAI CIDR:          │     │
    │  │ 10.244.0.0/16│            │ 172.30.0.0/16      │     │
    │  │              │            │                    │     │
    │  │ K8s pods     │            │ 커널 컨테이너      │     │
    │  │ (kubelet     │            │ (Agent가           │     │
    │  │  관리)       │            │  containerd로 관리)│     │
    │  └──────────────┘            └────────────────────┘     │
    │         ▲                            ▲                   │
    │         │                            │                   │
    │    K8s CNI 설정                 별도 CNI 설정            │
    │    /etc/cni/net.d/             /etc/cni/backendai.d/     │
    └──────────────────────────────────────────────────────────┘

Phase 3: 통합 CNI (Calico/Cilium 네이티브 연계)
    ┌──────────────────────────────────────────────────────────┐
    │  통합 CNI (Calico/Cilium)                                │
    │  ┌────────────────────────────────────────────────┐      │
    │  │ K8s Pod 풀:   10.244.0.0/16                    │      │
    │  │ BAI 풀:       10.244.128.0/17 (전용)           │      │
    │  │                                                │      │
    │  │ K8s pods + 커널 컨테이너                       │      │
    │  │ (통합 라우팅, 정책, 관측성)                    │      │
    │  └────────────────────────────────────────────────┘      │
    │                      ▲                                    │
    │                      │                                    │
    │              전용 IP 풀을 가진                             │
    │              단일 CNI                                      │
    └──────────────────────────────────────────────────────────┘
```

#### 5.8.3 구현 스케치: CNI 직접 호출 헬퍼

Phase 3 CNI 통합을 위해 전용 Go 헬퍼 데몬이 커널 컨테이너의 네트워크 라이프사이클을 관리한다:

```
Agent ──(gRPC)──▶ CNI 헬퍼 데몬 ──(CNI API)──▶ Calico/Cilium
                        │
                        ├── 엔드포인트 레지스트리 유지
                        ├── CNI ADD/DEL 처리
                        ├── 주기적 GC (실행 중인 컨테이너와 정합)
                        └── IP/라우트 정보를 Agent에 반환
```

헬퍼 데몬의 책임:
- 컨테이너 생성 후 Agent로부터 컨테이너 PID 수신
- veth 쌍 생성 및 컨테이너 netns에 부착
- 전용 IP 풀 설정으로 CNI ADD 호출
- 모든 관리 엔드포인트를 로컬 상태 파일에 추적
- 시작 시: 실행 중인 컨테이너와 상태 정합 및 고아 정리
- Agent 재시작 신호 시: 종료된 컨테이너에 대해 CNI DEL 실행

---

## 6. 컨트롤 플레인 설치 (Helm)

이 섹션에서는 Kubernetes 위에 Backend.AI 컨트롤 플레인을 설치하기 위한 Helm 기반 설치 전략을 설명한다. 핵심 과제는 **서비스 디스커버리 부트스트랩**이다: 각 컴포넌트는 시작 시 의존하는 서비스의 주소를 알아야 하며, 이 주소들은 Pod 재시작에도 안정적으로 유지되어야 한다.

### 6.1 의존성 체인 및 부트스트랩 순서

각 Backend.AI 컴포넌트는 서로 다른 의존성 요구사항을 갖는다:

```
┌─── 인프라 (Backend.AI 의존성 없음) ────────────────────────────┐
│                                                                │
│  etcd          PostgreSQL          Redis                       │
│  (가장 먼저   (가장 먼저          (가장 먼저                   │
│   시작 필요)   시작 필요)          시작 필요)                   │
│                                                                │
└──────────┬───────────┬───────────────┬─────────────────────────┘
           │           │               │
           ▼           ▼               ▼
┌─── Manager (세 가지 모두 필요) ───────────────────────────────┐
│                                                                │
│  읽는 곳:                                                      │
│    - etcd:       BACKEND_ETCD_ADDR  (환경 변수)                │
│    - PostgreSQL: BACKEND_DB_ADDR    (환경 변수)                │
│    - Redis:      [redis] addr       (toml / 환경 변수)         │
│                                                                │
│  etcd에 기록:                                                   │
│    - announce-addr (K8s Service DNS)                           │
│    - announce-internal-addr (K8s Service DNS)                  │
│    - cluster configuration                                     │
│                                                                │
└──────────┬─────────────────────────────────────────────────────┘
           │
           ▼
┌─── Agent (etcd만 필요) ──────────────────────────────────────┐
│                                                                │
│  읽는 곳:                                                      │
│    - etcd:       BACKEND_ETCD_ADDR  (환경 변수)                │
│                                                                │
│  etcd를 통해 디스커버리:                                        │
│    - Manager announce-addr                                     │
│    - Redis addr                                                │
│    - Cluster configuration                                     │
│                                                                │
│  etcd에 기록:                                                   │
│    - advertised-rpc-addr (호스트 노드 IP)                      │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

**핵심 인사이트**: Manager는 시작 시 etcd + DB + Redis 주소가 필요하다. Agent는 etcd 주소만 필요하며, 나머지는 모두 런타임에 etcd에서 디스커버리한다.

### 6.2 서비스 디스커버리 아키텍처

모든 컴포넌트 간 디스커버리는 안정적인 엔드포인트로서 **K8s Service DNS 이름**에 의존한다. 이 DNS 이름은 Helm 릴리스를 기반으로 결정론적이며, Pod 재시작에도 변경되지 않는다.

```
┌─── K8s Service DNS (안정적, 결정론적) ─────────────────────────────────┐
│                                                                         │
│  backendai-etcd.backendai-system.svc.cluster.local:2379                │
│  backendai-pg-rw.backendai-system.svc.cluster.local:5432               │
│  backendai-redis.backendai-system.svc.cluster.local:6379               │
│  backendai-manager.backendai-system.svc.cluster.local:8080             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─ etcd ─────────┐  ┌─ Manager ──────────┐  ┌─ Agent ───────────────────┐
│                 │  │                     │  │                           │
│ 환경 변수:      │  │ 환경 변수:          │  │ 환경 변수:                │
│  etcd addr      │  │  etcd addr          │  │  BACKEND_ETCD_ADDR       │
│  (Helm values   │  │  DB addr            │  │  (Helm values에서)       │
│   에서)         │  │  Redis addr         │  │                           │
│                 │  │  (Helm values에서)   │  │ etcd에 등록:             │
│ 등록:           │  │                     │  │  advertised-rpc-addr     │
│  (self, quorum) │  │ etcd에 등록:        │  │  = NODE_IP:6001          │
│                 │  │  announce-addr      │  │  (K8s Downward API 경유) │
│                 │  │  = K8s Service DNS  │  │                           │
└─────────────────┘  └─────────────────────┘  └───────────────────────────┘
```

**주소 등록 요약:**

| 컴포넌트 | etcd에 등록되는 이름 | K8s에서의 값 | 해석하는 주체 |
|---|---|---|---|
| Manager `announce-addr` | K8s Service DNS | `backendai-manager.backendai-system.svc:8080` | Agent |
| Manager `announce-internal-addr` | K8s Service DNS | `backendai-manager.backendai-system.svc:18080` | Agent, Storage Proxy |
| Agent `advertised-rpc-addr` | 호스트 노드 IP | `192.168.1.100:6001` (Downward API 경유) | Manager |
| Agent `advertised-host` (커널용) | 호스트 노드 IP | `192.168.1.100` (Downward API 경유) | 커널 컨테이너 |

### 6.3 Helm 차트 구조

```
backendai/                              # 우산(Umbrella) 차트
├── Chart.yaml
├── values.yaml                         # 글로벌 설정
├── charts/
│   ├── etcd/                           # 서브차트 (또는 의존성: bitnami/etcd)
│   ├── postgresql/                     # 서브차트 (또는 의존성: cnpg-cluster)
│   ├── redis/                          # 서브차트 (또는 의존성: bitnami/redis)
│   ├── manager/                        # Backend.AI Manager
│   │   ├── Chart.yaml
│   │   └── templates/
│   │       ├── deployment.yaml
│   │       ├── service.yaml
│   │       ├── configmap.yaml
│   │       └── _helpers.tpl
│   ├── agent/                          # Backend.AI Agent
│   │   ├── Chart.yaml
│   │   └── templates/
│   │       ├── daemonset.yaml
│   │       └── _helpers.tpl
│   ├── storage-proxy/                  # Backend.AI Storage Proxy
│   │   └── templates/
│   │       └── deployment.yaml
│   ├── app-proxy/                      # Backend.AI AppProxy
│   │   └── templates/
│   │       └── deployment.yaml
│   └── webserver/                      # Backend.AI Web Server
│       └── templates/
│           ├── deployment.yaml
│           └── ingress.yaml
└── templates/
    ├── namespace.yaml
    ├── secrets.yaml                    # 공유 시크릿 (DB, etcd, Redis 인증정보)
    └── _helpers.tpl                    # 공통 DNS 이름 생성 헬퍼
```

**외부 차트 의존성** (`Chart.yaml` 내):

```yaml
# Chart.yaml
apiVersion: v2
name: backendai
version: 1.0.0
dependencies:
  - name: etcd
    version: "10.x.x"
    repository: "https://charts.bitnami.com/bitnami"
    condition: etcd.enabled
  - name: postgresql
    version: "1.x.x"
    repository: "https://cloudnative-pg.github.io/charts"
    condition: postgresql.enabled
    alias: postgresql
  - name: redis
    version: "19.x.x"
    repository: "https://charts.bitnami.com/bitnami"
    condition: redis.enabled
```

`etcd.enabled=false`, `postgresql.enabled=false`, 또는 `redis.enabled=false`로 설정하면 외부에서 관리되는 인스턴스(예: AWS RDS, ElastiCache, 관리형 etcd)를 사용할 수 있다.

### 6.4 글로벌 Values 설정

`values.yaml`은 모든 서비스 주소에 대한 단일 진실 공급원(single source of truth)이다:

```yaml
# values.yaml
global:
  namespace: backendai-system

  # ── etcd ──────────────────────────────────────────────────
  # 이것이 부트스트랩 진입점이다. Manager와 Agent 모두
  # 이 주소가 필요하다. 나머지는 모두 etcd를 통해
  # (Agent의 경우) 또는 추가 환경 변수를 통해 (Manager의 경우) 디스커버리된다.
  etcd:
    host: "backendai-etcd.backendai-system.svc"
    port: 2379
    namespace: "backend"        # Backend.AI용 etcd 키 접두사
    auth:
      user: "root"
      existingSecret: "backendai-etcd-credentials"
      secretKey: "password"

  # ── PostgreSQL ────────────────────────────────────────────
  # Manager만 이것을 직접 필요로 한다.
  db:
    host: "backendai-pg-rw.backendai-system.svc"   # CloudNativePG 읽기-쓰기 서비스
    port: 5432
    name: "backend"
    auth:
      user: "backend"
      existingSecret: "backendai-db-credentials"
      secretKey: "password"

  # ── Redis ─────────────────────────────────────────────────
  # Manager는 설정에서 읽고, Agent는 etcd에서 디스커버리한다.
  redis:
    host: "backendai-redis-master.backendai-system.svc"
    port: 6379
    auth:
      existingSecret: "backendai-redis-credentials"
      secretKey: "password"

  # ── Manager announce 주소 ─────────────────────────────────
  # 이 주소들은 에이전트가 매니저를 디스커버리할 수 있도록 etcd에 기록된다.
  # Pod 재시작에도 안정적인 K8s Service DNS 이름이어야 한다.
  manager:
    announceAddr:
      host: "backendai-manager.backendai-system.svc"
      port: 8080
    announceInternalAddr:
      host: "backendai-manager.backendai-system.svc"
      port: 18080

# ── AppProxy ────────────────────────────────────────────────
appProxy:
  coordinator:
    replicas: 1
    image:
      repository: lablup/backend.ai-app-proxy
      tag: "25.12.0"
  worker:
    replicas: 2
    image:
      repository: lablup/backend.ai-app-proxy
      tag: "25.12.0"

# ── Manager 서브차트 ──────────────────────────────────────────
manager:
  replicas: 2
  image:
    repository: lablup/backend.ai-manager
    tag: "25.12.0"

# ── Agent 서브차트 ────────────────────────────────────────────
agent:
  image:
    repository: lablup/backend.ai-agent
    tag: "25.12.0"
  nodeSelector:
    backendai.io/role: agent
  containerRuntime: docker          # "docker" 또는 "containerd"
  rpcPort: 6001

# ── 외부 차트 오버라이드 ──────────────────────────────────────
etcd:
  enabled: true
  replicaCount: 3
  persistence:
    size: 10Gi
    storageClass: fast-ssd

postgresql:
  enabled: true
  # CloudNativePG Cluster 사양
  instances: 3
  storage:
    size: 50Gi
    storageClass: fast-ssd

redis:
  enabled: true
  architecture: standalone          # 또는 HA를 위한 "replication"
  master:
    persistence:
      size: 8Gi
```

### 6.5 컴포넌트 환경 변수 주입

#### 6.5.1 Manager Deployment 템플릿

Manager는 세 가지 인프라 주소가 모두 필요하다:

```yaml
# charts/manager/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backendai-manager
spec:
  replicas: {{ .Values.replicas }}
  template:
    spec:
      initContainers:
        - name: wait-for-etcd
          image: bitnami/etcd:3.5
          command: ['sh', '-c',
            'until etcdctl --endpoints={{ .Values.global.etcd.host }}:{{ .Values.global.etcd.port }} endpoint health 2>/dev/null; do echo "etcd not healthy yet..."; sleep 3; done']
        - name: wait-for-db
          image: postgres:16-alpine
          command: ['sh', '-c',
            'until pg_isready -h {{ .Values.global.db.host }} -p {{ .Values.global.db.port }} -U {{ .Values.global.db.auth.user }}; do echo "db not ready yet..."; sleep 3; done']
        - name: wait-for-redis
          image: redis:7-alpine
          command: ['sh', '-c',
            'until redis-cli -h {{ .Values.global.redis.host }} -p {{ .Values.global.redis.port }} ping 2>/dev/null | grep -q PONG; do echo "redis not ready yet..."; sleep 3; done']
      containers:
        - name: manager
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          env:
            # ── etcd ──
            - name: BACKEND_ETCD_ADDR
              value: "{{ .Values.global.etcd.host }}:{{ .Values.global.etcd.port }}"
            - name: BACKEND_NAMESPACE
              value: "{{ .Values.global.etcd.namespace }}"
            - name: BACKEND_ETCD_USER
              value: "{{ .Values.global.etcd.auth.user }}"
            - name: BACKEND_ETCD_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: "{{ .Values.global.etcd.auth.existingSecret }}"
                  key: "{{ .Values.global.etcd.auth.secretKey }}"
            # ── PostgreSQL ──
            - name: BACKEND_DB_ADDR
              value: "{{ .Values.global.db.host }}:{{ .Values.global.db.port }}"
            - name: BACKEND_DB_NAME
              value: "{{ .Values.global.db.name }}"
            - name: BACKEND_DB_USER
              value: "{{ .Values.global.db.auth.user }}"
            - name: BACKEND_DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: "{{ .Values.global.db.auth.existingSecret }}"
                  key: "{{ .Values.global.db.auth.secretKey }}"
            # ── Manager announce 주소 (etcd에 기록) ──
            - name: BACKEND_MANAGER_ANNOUNCE_ADDR
              value: "{{ .Values.global.manager.announceAddr.host }}:{{ .Values.global.manager.announceAddr.port }}"
            - name: BACKEND_MANAGER_ANNOUNCE_INTERNAL_ADDR
              value: "{{ .Values.global.manager.announceInternalAddr.host }}:{{ .Values.global.manager.announceInternalAddr.port }}"
          volumeMounts:
            - name: manager-config
              mountPath: /etc/backend.ai/manager.toml
              subPath: manager.toml
      volumes:
        - name: manager-config
          configMap:
            name: backendai-manager-config
```

#### 6.5.2 Agent DaemonSet 템플릿

Agent는 etcd 주소만 필요하다 -- Manager와 Redis 주소는 런타임에 etcd에서 디스커버리한다.

> **참고**: `system-node-critical`은 kubelet, kube-proxy 등 핵심 K8s 시스템 컴포넌트 전용으로 예약된 PriorityClass이다. Backend.AI 에이전트에는 전용 PriorityClass를 생성하여 사용한다.

```yaml
# charts/agent/templates/priorityclass.yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: backendai-agent-critical
value: 1000000
globalDefault: false
description: "Backend.AI 에이전트 DaemonSet Pod 전용 PriorityClass. 에이전트 Pod이 GPU 노드에서 축출되지 않도록 높은 우선순위를 설정한다."
```

```yaml
# charts/agent/templates/daemonset.yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: backendai-agent
spec:
  template:
    spec:
      hostNetwork: true
      nodeSelector:
        {{- toYaml .Values.nodeSelector | nindent 8 }}
      tolerations:
        - key: nvidia.com/gpu
          operator: Exists
          effect: NoSchedule
      priorityClassName: backendai-agent-critical
      initContainers:
        - name: wait-for-etcd
          image: bitnami/etcd:3.5
          command: ['sh', '-c',
            'until etcdctl --endpoints={{ .Values.global.etcd.host }}:{{ .Values.global.etcd.port }} endpoint health 2>/dev/null; do echo "etcd not healthy yet..."; sleep 3; done']
      containers:
        - name: agent
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          securityContext:
            privileged: true
            readOnlyRootFilesystem: true
            seccompProfile:
              type: RuntimeDefault
          env:
            # ── etcd (유일한 부트스트랩 의존성) ──
            - name: BACKEND_ETCD_ADDR
              value: "{{ .Values.global.etcd.host }}:{{ .Values.global.etcd.port }}"
            - name: BACKEND_NAMESPACE
              value: "{{ .Values.global.etcd.namespace }}"
            - name: BACKEND_ETCD_USER
              value: "{{ .Values.global.etcd.auth.user }}"
            - name: BACKEND_ETCD_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: "{{ .Values.global.etcd.auth.existingSecret }}"
                  key: "{{ .Values.global.etcd.auth.secretKey }}"
            # ── Agent advertised 주소 (Downward API를 통한 노드 IP) ──
            - name: BACKEND_AGENT_HOST_OVERRIDE
              valueFrom:
                fieldRef:
                  fieldPath: status.hostIP
            - name: BACKEND_BIND_HOST_OVERRIDE
              valueFrom:
                fieldRef:
                  fieldPath: status.hostIP
            # ── 컨테이너 런타임 백엔드 ──
            - name: BACKEND_AGENT_BACKEND
              value: "docker"
          volumeMounts:
            {{- if eq .Values.containerRuntime "docker" }}
            - name: container-runtime-socket
              mountPath: /var/run/docker.sock
            {{- else }}
            - name: container-runtime-socket
              mountPath: /run/containerd/containerd.sock
            {{- end }}
            - name: scratch-space
              mountPath: /var/cache/scratches
            - name: vfolder-storage
              mountPath: /vfolder
            - name: host-proc
              mountPath: /host/proc
              readOnly: true
            - name: host-sys
              mountPath: /host/sys
              readOnly: true
      volumes:
        - name: container-runtime-socket
          hostPath:
            {{- if eq .Values.containerRuntime "docker" }}
            path: /var/run/docker.sock
            {{- else }}
            path: /run/containerd/containerd.sock
            {{- end }}
            type: Socket
        - name: scratch-space
          hostPath:
            path: /var/cache/backendai/scratches
            type: DirectoryOrCreate
        - name: vfolder-storage
          hostPath:
            path: /mnt/vfolder
            type: Directory
        - name: host-proc
          hostPath:
            path: /proc
            type: Directory
        - name: host-sys
          hostPath:
            path: /sys
            type: Directory
```

> **참고**: `hostNetwork: true`를 사용하면 에이전트가 기본 바인드 주소 `0.0.0.0`을 etcd에 등록하게 되어, 매니저가 에이전트에 도달할 수 없다. Kubernetes Downward API를 통해 실제 노드 IP를 `BACKEND_AGENT_HOST_OVERRIDE`와 `BACKEND_BIND_HOST_OVERRIDE`로 주입하여, 에이전트가 올바른 호스트 IP를 advertise하고 바인딩하도록 해야 한다.

### 6.6 부팅 순서 및 Init 컨테이너

Helm은 단일 릴리스 내에서 배포 순서를 보장하지 않는다. 모든 리소스가 동시에 적용된다. 부팅 순서는 **init 컨테이너**를 통해 Pod 수준에서 강제된다:

```
┌─ Helm install (모든 리소스가 한 번에 적용) ────────────────────────┐
│                                                                     │
│  etcd StatefulSet    ──▶ Pod 시작, 쿼럼 구성                       │
│  PostgreSQL          ──▶ Pod 시작, ready 상태 도달                 │
│  Redis               ──▶ Pod 시작, ready 상태 도달                 │
│                                                                     │
│  Manager Deployment  ──▶ init 컨테이너가 etcd/DB/Redis 대기        │
│                          ──▶ 모두 준비된 후 메인 컨테이너 시작      │
│                                                                     │
│  Agent DaemonSet     ──▶ init 컨테이너가 etcd 대기                 │
│                          ──▶ 메인 컨테이너 시작                     │
│                          ──▶ etcd에서 manager 주소 읽기             │
│                              (manager 등록까지 재시도)              │
└─────────────────────────────────────────────────────────────────────┘
```

**init 컨테이너로 충분한 이유:**

1. **etcd, PostgreSQL, Redis**: Backend.AI 의존성이 없는 인프라 서비스이다. 즉시 시작되며 수 초 내에 ready 상태가 된다.
2. **Manager**: init 컨테이너가 세 가지 인프라 서비스 모두 도달 가능할 때까지 블로킹한다. 그 후 Manager가 시작되어 etcd에 `announce-addr`을 등록한다.
3. **Agent**: init 컨테이너가 etcd 도달 가능할 때까지 블로킹한다. Agent가 시작되어 etcd에서 Manager 주소를 읽는다. Manager가 아직 등록하지 않았다면, Agent의 기존 재시도 로직이 이를 처리한다(주기적으로 etcd에서 Manager 엔드포인트를 재확인).

**단순 포트 체크(`nc -z`) 대신 네이티브 클라이언트 헬스 체크를 사용하는 이유:**

단순 TCP 포트 체크(`nc -z`)는 서비스가 실제로 준비되지 않았는데도 통과할 수 있다. 각 init 컨테이너는 실제 서비스 준비 상태를 검증하는 네이티브 클라이언트를 사용한다:

| 서비스 | 체크 도구 | 검증 내용 | `nc -z`가 불충분한 이유 |
|---|---|---|---|
| etcd | `etcdctl endpoint health` | 쿼럼 형성 완료, 읽기/쓰기 가능 | etcd는 쿼럼 형성 전에도 포트를 리스닝함 — 쿼럼이 형성될 때까지 쓰기 실패 |
| PostgreSQL | `pg_isready` | 연결 수락 상태, 리커버리 완료 | PostgreSQL은 시작 시 리커버리 중에 TCP 포트를 열음 — 리커버리 완료까지 쿼리 실패 |
| Redis | `redis-cli ping` → `PONG` | 명령 처리 가능, 메모리 로드 완료 | Redis는 AOF/RDB 로딩 전에 포트를 바인딩함 — 데이터 로드까지 명령 타임아웃 |

**대안적 접근 — 프로브와 애플리케이션 수준 재시도**: 무한 대기 루프의 init 컨테이너 대신, Kubernetes `startupProbe`와 `readinessProbe`를 애플리케이션 수준 재시도 로직과 결합하는 대안이 있다. Manager와 Agent는 이미 etcd 및 Redis에 대한 연결 재시도를 구현하고 있다. init 컨테이너 방식은 추론하기 더 단순하고 깨끗한 시작 순서를 보장하지만, init 컨테이너 이미지 pull이 레이턴시를 추가하는 프로덕션 환경에서는 프로브 기반 접근이 선호될 수 있다. 두 접근 모두 유효하며, 운영 선호에 따라 선택한다.

### 6.7 설치 명령

#### 6.7.1 사전 요구사항

```bash
# 네임스페이스 생성
kubectl create namespace backendai-system

# 시크릿 생성 (Helm install 전)
kubectl create secret generic backendai-etcd-credentials \
  --from-literal=password='<ETCD_PASSWORD>' \
  -n backendai-system

kubectl create secret generic backendai-db-credentials \
  --from-literal=password='<DB_PASSWORD>' \
  -n backendai-system

kubectl create secret generic backendai-redis-credentials \
  --from-literal=password='<REDIS_PASSWORD>' \
  -n backendai-system
```

#### 6.7.2 etcd 볼륨 경로 초기화

Backend.AI는 vfolder 스토리지 경로와 관련 설정을 etcd에 저장한다. Helm 설치 후 에이전트가 시작되기 전에, etcd에 볼륨 관련 키를 초기화해야 한다. 이 단계가 없으면 에이전트가 vfolder 마운트 경로를 알 수 없어 커널 컨테이너에 올바른 바인드 마운트를 설정할 수 없다.

```bash
# etcd Pod에 접속하여 볼륨 경로 초기화
kubectl exec -n backendai-system backendai-etcd-0 -- \
  etcdctl put /backend/volumes '{"default_host":"local:volume1","proxies":{}}'

kubectl exec -n backendai-system backendai-etcd-0 -- \
  etcdctl put /backend/volumes/local:volume1 \
  '{"path":"/mnt/vfolder","fsprefix":"","backend":"vfs"}'
```

#### 6.7.3 설치

```bash
# 단일 Helm 명령으로 모든 것을 설치
helm install backendai ./backendai \
  -n backendai-system \
  --create-namespace \
  -f values.yaml

# 또는 외부 인프라 사용 시 (예: 관리형 DB)
helm install backendai ./backendai \
  -n backendai-system \
  --set postgresql.enabled=false \
  --set global.db.host=my-rds-instance.region.rds.amazonaws.com \
  --set global.db.port=5432
```

#### 6.7.4 검증

```bash
# 모든 Pod이 실행 중인지 확인
kubectl get pods -n backendai-system

# 예상 출력:
# NAME                                  READY   STATUS    RESTARTS
# backendai-etcd-0                      1/1     Running   0
# backendai-etcd-1                      1/1     Running   0
# backendai-etcd-2                      1/1     Running   0
# backendai-pg-1                        1/1     Running   0
# backendai-pg-2                        1/1     Running   0
# backendai-pg-3                        1/1     Running   0
# backendai-redis-master-0              1/1     Running   0
# backendai-manager-xxxx-yyy            1/1     Running   0
# backendai-manager-xxxx-zzz            1/1     Running   0
# backendai-agent-node1                 1/1     Running   0
# backendai-agent-node2                 1/1     Running   0

# Manager가 etcd에 등록되었는지 확인
kubectl exec -n backendai-system backendai-etcd-0 -- \
  etcdctl get /backend/manager --prefix

# Agent가 etcd에 등록되었는지 확인
kubectl exec -n backendai-system backendai-etcd-0 -- \
  etcdctl get /backend/agents --prefix
```

#### 6.7.5 업그레이드

```bash
# 롤링 업그레이드 (예: 새 Manager 이미지)
helm upgrade backendai ./backendai \
  -n backendai-system \
  --set manager.image.tag="25.13.0"

# Agent 롤링 업데이트는 DaemonSet 업데이트 전략으로 처리됨
# 커널 컨테이너는 영향받지 않음 (DooD — 호스트에서 실행)
```

### 6.8 컨테이너 이미지 관리

DooD 아키텍처에서는 **두 개의 독립적인 이미지 pull 경로**가 있으며, 각각 별도로 설정해야 한다:

```
┌─── 이미지 레지스트리 (예: Harbor) ────────────────────────────┐
│                                                               │
│  backendai/manager:25.12.0        ← kubelet이 pull           │
│  backendai/agent:25.12.0          ← kubelet이 pull           │
│  backendai/webserver:25.12.0      ← kubelet이 pull           │
│  backendai/kernel-python:3.11     ← Agent가 pull (Docker API)│
│  backendai/kernel-pytorch:2.1     ← Agent가 pull (Docker API)│
│                                                               │
└───────────────────────────────────────────────────────────────┘
         ▲                                    ▲
         │                                    │
   K8s imagePullSecrets              etcd registry 설정
   (Helm values)                    (Manager API / etcd)
```

#### 6.8.1 이중 이미지 Pull 아키텍처

| 구분 | 컨트롤 플레인 이미지 | 커널 이미지 |
|---|---|---|
| **예시** | `manager`, `agent`, `webserver`, `app-proxy` | `kernel-python:3.11`, `kernel-pytorch:2.1` |
| **pull 주체** | kubelet | Backend.AI Agent (Docker/containerd API 경유) |
| **인증** | K8s `imagePullSecrets` | etcd `registry_conf` (username/password) |
| **설정 위치** | Helm `values.yaml` | Backend.AI Manager API 또는 etcd |
| **라이프사이클** | `helm upgrade`로 업데이트 | Backend.AI 이미지 관리 기능으로 업데이트 |

Agent의 pull 구현(`src/ai/backend/agent/docker/agent.py`)은 etcd에서 레지스트리 인증 정보를 읽어 Docker API에 직접 전달한다:

```python
reg_user = registry_conf.get("username")
reg_passwd = registry_conf.get("password")
auth_config = {"auth": base64.b64encode(f"{reg_user}:{reg_passwd}".encode()).decode("ascii")}
await docker.images.pull(image_ref.canonical, auth=auth_config)
```

이는 K8s `imagePullSecrets`가 커널 이미지 pull에 **전혀 영향을 미치지 않음**을 의미한다 — Agent는 kubelet을 완전히 우회한다.

#### 6.8.2 레지스트리 인증 정보 동기화

프라이빗 레지스트리(예: Harbor)를 컨트롤 플레인과 커널 이미지 모두에 사용하는 경우, 인증 정보를 **두 곳에** 설정해야 한다:

1. **K8s Secret** (kubelet용): Helm values의 `imagePullSecrets`
2. **etcd** (Agent용): Manager API를 통한 레지스트리 username/password

인증 정보를 두 곳에서 관리하는 것을 방지하기 위해, **Helm post-install/post-upgrade hook**을 사용하여 K8s Secret 인증 정보를 etcd에 자동 동기화한다:

```yaml
# templates/jobs/sync-registry-creds.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: {{ .Release.Name }}-sync-registry-creds
  annotations:
    helm.sh/hook: post-install,post-upgrade
    helm.sh/hook-weight: "-5"
    helm.sh/hook-delete-policy: hook-succeeded
spec:
  template:
    spec:
      restartPolicy: OnFailure
      containers:
        - name: sync
          image: bitnami/etcd:3.5
          command: ['sh', '-c', |
            etcdctl --endpoints={{ .Values.global.etcd.host }}:{{ .Values.global.etcd.port }} \
              put /{{ .Values.global.etcd.namespace }}/config/docker/registry/{{ .Values.global.imageRegistry.host }}/username "$REG_USER"
            etcdctl --endpoints={{ .Values.global.etcd.host }}:{{ .Values.global.etcd.port }} \
              put /{{ .Values.global.etcd.namespace }}/config/docker/registry/{{ .Values.global.imageRegistry.host }}/password "$REG_PASS"
          ]
          env:
            - name: REG_USER
              valueFrom:
                secretKeyRef:
                  name: {{ .Values.global.imageRegistry.existingSecret }}
                  key: username
            - name: REG_PASS
              valueFrom:
                secretKeyRef:
                  name: {{ .Values.global.imageRegistry.existingSecret }}
                  key: password
```

`values.yaml`에 대응하는 값을 추가한다:

```yaml
global:
  imageRegistry:
    host: "harbor.internal"
    existingSecret: "harbor-credentials"   # username/password 키를 가진 K8s Secret
  imagePullSecrets:
    - harbor-credentials                   # kubelet용 (컨트롤 플레인 이미지)
```

이렇게 하면 레지스트리 인증 정보를 **단일 K8s Secret에서만** 관리하고, Helm hook이 매 설치/업그레이드 시 Agent를 위해 etcd에 동기화한다.

#### 6.8.3 에어갭 배포

외부 레지스트리 접근이 없는 에어갭 환경에서:

| 이미지 유형 | 사전 로딩 전략 |
|---|---|
| 컨트롤 플레인 | 각 노드에서 `docker load` 또는 `ctr image import`, `imagePullPolicy: IfNotPresent` 설정 |
| 커널 | 각 에이전트 노드에서 `docker load` (DooD 접근을 위해 호스트 Docker 데몬에 로딩) |

에어갭 모드의 커널 이미지의 경우, Backend.AI 설정에서 `auto_pull`을 `NONE`으로 설정하여 Agent가 도달 불가능한 레지스트리에서 이미지를 pull하려는 시도를 방지한다. 모든 커널 이미지는 각 에이전트 노드의 Docker 데몬에 사전 로딩되어야 한다.

#### 6.8.4 인증 정보 로테이션 절차

레지스트리 인증 정보가 변경될 때:

1. K8s Secret 업데이트:
   ```bash
   kubectl create secret docker-registry harbor-credentials \
     --docker-server=harbor.internal \
     --docker-username=NEW_USER \
     --docker-password=NEW_PASS \
     -n backendai-system --dry-run=client -o yaml | kubectl apply -f -
   ```
2. Helm upgrade를 실행하여 동기화 hook 트리거:
   ```bash
   helm upgrade backendai ./backendai -n backendai-system
   ```
3. etcd에 인증 정보가 업데이트되었는지 확인:
   ```bash
   kubectl exec -n backendai-system backendai-etcd-0 -- \
     etcdctl get /backend/config/docker/registry/harbor.internal/username
   ```

### 6.9 데이터베이스 마이그레이션 전략 (Alembic)

Backend.AI는 데이터베이스 스키마 마이그레이션에 Alembic을 사용한다. 이미지 업데이트가 Pod 재생성을 트리거하는 K8s 배포에서, 마이그레이션은 새 Manager Pod이 시작되기 **전에** 실행되어야 한다. 그렇지 않으면 새 코드가 아직 존재하지 않는 컬럼이나 테이블을 참조하여 즉시 시작 실패가 발생한다.

#### 6.9.1 문제

```
helm upgrade (manager 이미지 25.12.0 → 25.13.0)
    │
    ├── 새 Manager Pod 생성 (25.13.0 코드)
    │     → DB 스키마는 아직 25.12.0 상태
    │     → 새 코드가 없는 컬럼/테이블을 참조
    │     → 크래시
    │
    └── 새 Pod 시작 전에 마이그레이션이 실행되어야 함
```

#### 6.9.2 해결: Helm Pre-Upgrade Hook

Kubernetes Job이 Manager Deployment 업데이트 전에 **새** Manager 이미지를 사용하여 Alembic 마이그레이션을 실행한다:

```yaml
# templates/jobs/db-migrate.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: {{ .Release.Name }}-db-migrate
  annotations:
    helm.sh/hook: pre-install,pre-upgrade
    helm.sh/hook-weight: "0"
    helm.sh/hook-delete-policy: before-hook-creation
spec:
  backoffLimit: 3
  template:
    spec:
      restartPolicy: OnFailure
      initContainers:
        - name: wait-for-db
          image: postgres:16-alpine
          command: ['sh', '-c',
            'until pg_isready -h {{ .Values.global.db.host }} -p {{ .Values.global.db.port }} -U {{ .Values.global.db.auth.user }}; do echo "db not ready..."; sleep 3; done']
      containers:
        - name: migrate
          image: "{{ .Values.manager.image.repository }}:{{ .Values.manager.image.tag }}"
          command: ["python", "-m", "ai.backend.manager.cli", "schema", "oneshot"]
          env:
            - name: BACKEND_DB_ADDR
              value: "{{ .Values.global.db.host }}:{{ .Values.global.db.port }}"
            - name: BACKEND_DB_NAME
              value: "{{ .Values.global.db.name }}"
            - name: BACKEND_DB_USER
              value: "{{ .Values.global.db.auth.user }}"
            - name: BACKEND_DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: "{{ .Values.global.db.auth.existingSecret }}"
                  key: "{{ .Values.global.db.auth.secretKey }}"
            - name: BACKEND_ETCD_ADDR
              value: "{{ .Values.global.etcd.host }}:{{ .Values.global.etcd.port }}"
```

AppProxy Coordinator도 자체 데이터베이스와 Alembic 마이그레이션이 있다:

```yaml
# templates/jobs/db-migrate-appproxy.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: {{ .Release.Name }}-db-migrate-appproxy
  annotations:
    helm.sh/hook: pre-install,pre-upgrade
    helm.sh/hook-weight: "1"
    helm.sh/hook-delete-policy: before-hook-creation
spec:
  backoffLimit: 3
  template:
    spec:
      restartPolicy: OnFailure
      initContainers:
        - name: wait-for-db
          image: postgres:16-alpine
          command: ['sh', '-c',
            'until pg_isready -h {{ .Values.global.db.host }} -p {{ .Values.global.db.port }} -U {{ .Values.global.db.auth.user }}; do echo "db not ready..."; sleep 3; done']
      containers:
        - name: migrate
          image: "{{ .Values.appProxy.coordinator.image.repository }}:{{ .Values.appProxy.coordinator.image.tag }}"
          command: ["python", "-m", "ai.backend.app_proxy.coordinator.cli", "schema", "oneshot"]
          env:
            - name: BACKEND_DB_ADDR
              value: "{{ .Values.global.db.host }}:{{ .Values.global.db.port }}"
            - name: BACKEND_DB_NAME
              value: "appproxy"
            - name: BACKEND_DB_USER
              value: "{{ .Values.global.db.auth.user }}"
            - name: BACKEND_DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: "{{ .Values.global.db.auth.existingSecret }}"
                  key: "{{ .Values.global.db.auth.secretKey }}"
```

#### 6.9.3 Helm Hook 실행 순서

모든 Helm hook은 메인 리소스가 업데이트되기 전에 `hook-weight` 순서로 실행된다:

```
helm install/upgrade
    │
    │  hook-weight: -5
    ├── sync-registry-creds Job       (K8s Secret → etcd 동기화)
    │
    │  hook-weight: 0
    ├── db-migrate Job                (Manager DB: alembic upgrade head)
    │
    │  hook-weight: 1
    ├── db-migrate-appproxy Job       (AppProxy DB: alembic upgrade head)
    │
    │  hook-weight: 5
    ├── init-etcd-volumes Job         (etcd vfolder 설정 초기화)
    │
    │  (모든 hook 성공적으로 완료)
    ├── Manager Deployment 업데이트    (새 이미지, 스키마 이미 최신)
    ├── AppProxy Deployment 업데이트
    ├── Agent DaemonSet 업데이트
    └── 기타 컴포넌트 업데이트
```

어떤 hook Job이라도 실패하면(예: 마이그레이션 오류), Helm이 업그레이드를 중단하고 Deployment가 업데이트되지 않는다. 이로써 호환되지 않는 스키마에 새 코드를 배포하는 것을 방지한다.

#### 6.9.4 롤백 시 고려사항

```
helm rollback backendai 1
    │
    ├── Manager 이미지 롤백: 25.13.0 → 25.12.0
    │
    └── DB 스키마는 25.13.0 상태 유지 (Helm 롤백은 마이그레이션을 실행하지 않음)
```

Backend.AI의 Alembic 마이그레이션은 기본적으로 **순방향 전용(forward-only)**이다. 롤백 동작은 마이그레이션 유형에 따라 다르다:

| 마이그레이션 유형 | 롤백 안전성 | 필요 조치 |
|---|---|---|
| 컬럼 추가 | **안전** — 이전 코드가 알려지지 않은 컬럼을 무시 | 조치 불필요 |
| 새 테이블 | **안전** — 이전 코드가 참조하지 않음 | 조치 불필요 |
| 컬럼 이름 변경 | **안전하지 않음** — 이전 코드가 이전 컬럼명을 참조 | 수동 `alembic downgrade` 필요 |
| 컬럼 삭제 | **안전하지 않음** — 이전 코드가 삭제된 컬럼을 참조 | 수동 `alembic downgrade` 필요 |
| 데이터 변환 | **안전하지 않음** — 데이터 형식이 호환되지 않을 수 있음 | 수동 평가 + downgrade 필요 |

**안전하지 않은 마이그레이션의 롤백 절차:**

```bash
# 1. 이전 버전의 대상 Alembic 리비전 확인
kubectl exec -n backendai-system deploy/backendai-manager -- \
  python -m ai.backend.manager.cli schema show-revision

# 2. 수동 downgrade 실행 (이전 이미지 사용)
kubectl run db-downgrade --rm -it \
  --image=backendai/manager:25.12.0 \
  -n backendai-system -- \
  python -m ai.backend.manager.cli schema downgrade <target-revision>

# 3. Helm 롤백 수행
helm rollback backendai 1 -n backendai-system
```

> **모범 사례**: 모든 업그레이드 전에 현재 Alembic 리비전을 기록한다. 이를 통해 롤백이 필요한 경우 대상 downgrade가 가능하다. 현재 리비전을 ConfigMap에 저장하는 pre-upgrade hook 추가를 고려한다.

### 6.10 Redis 고가용성

Backend.AI는 이미 고가용성을 위해 Redis Sentinel을 지원한다. K8s 배포는 기존 Sentinel 기반 클라이언트 코드와 호환되는 Redis HA 구성을 제공해야 한다.

#### 6.10.1 옵션 비교

| 옵션 | Pod 수 | Failover | Backend.AI 호환 | 운영 복잡도 | 적합한 환경 |
|---|---|---|---|---|---|
| **Bitnami Helm (Sentinel)** | **3** (각 Pod에 master+replica+sentinel) | Sentinel 자동 failover | 완전 (기존 Sentinel 지원) | 낮음 | 온프레미스, 단일 클러스터 |
| **Redis Operator (Spotahome)** | **7** (operator 1 + Redis 3 + Sentinel 3) | Operator + Sentinel | 완전 | 중간 | 멀티 클러스터, 플랫폼 팀 |
| **관리형 Redis** | 0 (클라우드 관리) | 클라우드 제공자 관리 | 완전 (단일 엔드포인트 또는 Sentinel) | 최저 | 클라우드 배포 (AWS, GCP, Azure) |
| **Redis Cluster** | 6+ (master 3 + replica 3) | 클러스터 내장 failover | **미지원** (클라이언트 변경 필요) | 높음 | 비권장 |

#### 6.10.2 권고: Bitnami Helm Chart (Sentinel 모드)

Backend.AI와 완전히 호환되는 가장 단순한 옵션. Sentinel이 각 Redis Pod에 사이드카로 실행되어 총 **3개 Pod**만 필요하다:

```
┌─── Redis StatefulSet (Bitnami Helm) ──────────────────────┐
│                                                            │
│  backendai-redis-node-0  (master + sentinel 사이드카)      │
│  backendai-redis-node-1  (replica + sentinel 사이드카)     │
│  backendai-redis-node-2  (replica + sentinel 사이드카)     │
│                                                            │
│  K8s Services:                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ backendai-redis.svc:6379       → master (read-write) │  │
│  │ backendai-redis-headless.svc   → 모든 노드           │  │
│  │ backendai-redis.svc:26379      → sentinel 포트       │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

Helm values:

```yaml
redis:
  enabled: true
  architecture: replication

  sentinel:
    enabled: true
    quorum: 2

  master:
    persistence:
      size: 8Gi
      storageClass: fast-ssd

  replica:
    replicaCount: 2

  auth:
    existingSecret: backendai-redis-credentials
    existingSecretPasswordKey: password
```

#### 6.10.3 대안: Redis Operator (Spotahome)

오퍼레이터 관리 인프라를 선호하는 조직을 위한 옵션. 오퍼레이터가 `RedisFailover` CRD를 감시하고 Redis 토폴로지, 롤링 업그레이드, 복구를 자동으로 관리한다:

```
┌─── Redis Operator Deployment ─────────────────────────────┐
│                                                            │
│  Operator Pod (1)          ← RedisFailover CRD 감시        │
│                                                            │
│  Redis Pods:                                               │
│    redis-0 (master)                                        │
│    redis-1 (replica)                                       │
│    redis-2 (replica)                                       │
│                                                            │
│  Sentinel Pods:                                            │
│    sentinel-0                                              │
│    sentinel-1                                              │
│    sentinel-2                                              │
│                                                            │
│  합계: 7 Pods                                              │
└────────────────────────────────────────────────────────────┘
```

```yaml
apiVersion: databases.spotahome.com/v1
kind: RedisFailover
metadata:
  name: backendai-redis
  namespace: backendai-system
spec:
  sentinel:
    replicas: 3
  redis:
    replicas: 3
    storage:
      persistentVolumeClaim:
        metadata:
          name: redis-data
        spec:
          accessModes: [ReadWriteOnce]
          resources:
            requests:
              storage: 8Gi
```

**Bitnami Helm 대비 Operator의 이점:**

| 시나리오 | Bitnami Helm | Redis Operator |
|---|---|---|
| K8s에 의한 Pod 삭제 | Sentinel이 failover 처리; 수동 토폴로지 확인 필요할 수 있음 | Operator가 자동으로 원하는 상태로 조정 |
| Redis 버전 업그레이드 | `helm upgrade`로 수동 검증 | Operator가 롤링 업데이트 관리 |
| 영속 스토리지 문제 | 수동 개입 | Operator가 감지하고 재생성 |
| 설정 드리프트 | 수동 변경 후 가능 | Operator가 지속적으로 조정 |

#### 6.10.4 대안: 관리형 Redis (클라우드)

클라우드 배포에서 관리형 Redis는 모든 운영 부담을 제거한다:

| 클라우드 제공자 | 서비스 | Sentinel 호환 | 설정 |
|---|---|---|---|
| AWS | ElastiCache for Redis | 예 (클러스터 모드 비활성화) | 단일 primary 엔드포인트 |
| GCP | Memorystore for Redis | 예 (Standard 티어) | 단일 엔드포인트 + 자동 failover |
| Azure | Azure Cache for Redis | 예 (Premium 티어) | 단일 엔드포인트 + 자동 failover |

관리형 Redis 사용 시, Helm values에서 `redis.enabled=false`로 설정하고 외부 엔드포인트를 구성한다:

```yaml
redis:
  enabled: false

global:
  redis:
    host: "my-redis.xxxx.cache.amazonaws.com"
    port: 6379
    # Sentinel 설정 불필요 — 관리형 Redis가 내부적으로 failover 처리
```

#### 6.10.5 Backend.AI Sentinel 설정

선택한 Redis HA 옵션(Bitnami 또는 Operator)과 관계없이, Backend.AI Manager와 Agent는 Sentinel 연결 정보가 필요하다. Sentinel은 여러 호스트 항목(`[[redis.sentinel]]` TOML 배열)이 필요하므로, 환경변수보다 ConfigMap을 통해 제공하는 것이 가장 적합하다:

```yaml
# Manager용 ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: backendai-manager-redis-config
data:
  redis.toml: |
    [redis]
    service-name = "mymaster"

    [[redis.sentinel]]
    host = "backendai-redis-node-0.backendai-redis-headless.backendai-system.svc"
    port = 26379

    [[redis.sentinel]]
    host = "backendai-redis-node-1.backendai-redis-headless.backendai-system.svc"
    port = 26379

    [[redis.sentinel]]
    host = "backendai-redis-node-2.backendai-redis-headless.backendai-system.svc"
    port = 26379
```

**Failover 동작:**

```
정상 상태:
  Client → Sentinel (master 주소 질의) → master에 연결

Master 장애:
  1. Sentinel이 master 다운 감지 (쿼럼: 2/3 동의)
  2. replica 중 하나를 새 master로 승격
  3. 다른 replica가 새 master를 따름
  4. Client가 Sentinel에 재질의 → 새 master에 연결

  → Backend.AI redis_helper가 이미 Sentinel 프로토콜을 지원
    — failover 시 자동 master 발견 및 재연결
```

---

## 7. 상세 컴포넌트 설계

### 7.1 컨트롤 플레인 Pod 사양

#### 7.1.1 Manager Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backendai-manager
  namespace: backendai-system
spec:
  replicas: 2
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  template:
    spec:
      containers:
        - name: manager
          image: lablup/backend.ai-manager:latest
          ports:
            - containerPort: 8080    # API
              name: api
            - containerPort: 8090    # RPC (에이전트 통신)
              name: rpc
          resources:
            requests:
              cpu: "1"
              memory: "2Gi"
            limits:
              cpu: "4"
              memory: "8Gi"
          envFrom:
            - configMapRef:
                name: backendai-manager-config
            - secretRef:
                name: backendai-manager-secrets
          livenessProbe:
            httpGet:
              path: /func/health
              port: api
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /func/health
              port: api
            initialDelaySeconds: 10
            periodSeconds: 5
```

#### 7.1.2 PostgreSQL StatefulSet

프로덕션급 PostgreSQL on K8s를 위해 **CloudNativePG 오퍼레이터** 사용을 권고한다.

```yaml
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: backendai-pg
  namespace: backendai-system
spec:
  instances: 3
  postgresql:
    parameters:
      max_connections: "200"
      shared_buffers: "512MB"
  storage:
    size: 50Gi
    storageClass: fast-ssd
  backup:
    barmanObjectStore:
      destinationPath: "s3://backendai-backup/pg"
```

#### 7.1.3 etcd StatefulSet

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: backendai-etcd
  namespace: backendai-system
spec:
  serviceName: backendai-etcd
  replicas: 3
  template:
    spec:
      containers:
        - name: etcd
          image: quay.io/coreos/etcd:v3.5
          ports:
            - containerPort: 2379
              name: client
            - containerPort: 2380
              name: peer
          volumeMounts:
            - name: data
              mountPath: /var/run/etcd
          resources:
            requests:
              cpu: "500m"
              memory: "1Gi"
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: fast-ssd
        resources:
          requests:
            storage: 10Gi
```

### 7.2 에이전트 DaemonSet 설계

#### 7.2.1 리소스 예약

에이전트 DaemonSet은 커널 워크로드가 과중한 상황에서도 에이전트 Pod이 항상 충분한 CPU와 메모리를 확보하도록 각 노드에서 리소스를 예약해야 한다:

```yaml
resources:
  requests:
    cpu: "500m"       # 에이전트 프로세스용 예약
    memory: "1Gi"     # 에이전트 프로세스용 예약
  limits:
    cpu: "2"          # 스케줄링 작업 중 에이전트 버스트 가능
    memory: "4Gi"     # 에이전트가 이미지 메타데이터, 커널 상태 캐시
```

K8s는 에이전트의 예약된 리소스에 다른 K8s Pod을 스케줄하지 않는다. 그러나 커널 컨테이너(K8s 외부에서 관리)는 노드의 나머지 리소스를 경쟁한다. Backend.AI 에이전트는 `available_slots` 계산 시 자체 예약 리소스를 고려해야 한다.

#### 7.2.2 헬스 체크

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 6009
  initialDelaySeconds: 60
  periodSeconds: 30
  failureThreshold: 3
readinessProbe:
  httpGet:
    path: /health
    port: 6009
  initialDelaySeconds: 15
  periodSeconds: 10
```

#### 7.2.3 에이전트 종료 및 커널 고아 관리

에이전트 Pod이 재시작되면(롤링 업데이트, 노드 드레인, OOM kill), 커널 컨테이너는 K8s에 의해 관리되지 않으므로 호스트에서 계속 실행된다:

- **정상 종료**: 에이전트가 SIGTERM을 받고, `pre_stop` 정리를 수행하며, 커널 레지스트리 상태를 etcd에 저장한다.
- **재시작 시 복구**: 새 에이전트 Pod이 etcd에서 커널 레지스트리를 읽고, 기존 커널 컨테이너에 재연결한다(`DockerKernelRegistryRecovery`).
- **고아 감지**: 시작 시 에이전트가 `ai.backend.` 라벨을 가진 실행 중인 컨테이너를 스캔하고 저장된 상태와 대조한다.

이는 현재 베어메탈 복구 동작과 동일하다 — DooD 모델은 커널 복구 시맨틱을 변경하지 않는다.

### 7.3 커널 컨테이너 관리

#### 7.3.1 컨테이너 라벨

모든 커널 컨테이너는 식별 및 관리를 위해 라벨이 부착되어야 한다:

```json
{
  "ai.backend.kernel-id": "<kernel-uuid>",
  "ai.backend.session-id": "<session-uuid>",
  "ai.backend.agent-id": "<agent-id>",
  "ai.backend.managed-by": "backendai-agent",
  "ai.backend.cluster": "<k8s-cluster-name>"
}
```

#### 7.3.2 리소스 격리

커널 컨테이너는 리소스 격리를 위해 Linux cgroup(Docker/containerd 경유)을 사용한다:

- **CPU**: 피닝을 위한 `--cpus`, `--cpuset-cpus`
- **메모리**: `--memory`, `--memory-swap`
- **GPU**: `--gpus`, `--device /dev/nvidia*`, 또는 CDI 디바이스 스펙
- **I/O**: cgroup blkio 컨트롤러를 통한 블록 I/O 제한

### 7.4 서비스 디스커버리 및 통신

| 통신 경로 | 메커니즘 |
|---|---|
| Manager → Agent | K8s Service(에이전트 `hostNetwork` IP)를 통한 ZeroMQ |
| Agent → Manager | 매니저용 K8s Service(ClusterIP)로의 ZeroMQ |
| Agent → etcd | etcd용 K8s Service(ClusterIP)로의 gRPC |
| Agent → Redis | Redis용 K8s Service(ClusterIP)로의 TCP |
| Agent → PostgreSQL | PostgreSQL용 K8s Service(ClusterIP)로의 TCP |
| Agent → Kernel | 소켓을 통한 Docker/containerd API + 커널 TCP 포트 |
| Kernel → Agent | 호스트 IP(에이전트 `hostNetwork`)로의 TCP |
| Kernel → Kernel (동일 노드) | Docker 브릿지 네트워크 |
| Kernel → Kernel (크로스 노드) | Docker Swarm 오버레이 / 대안 오버레이 |

---

## 8. 현재 아키텍처로부터의 마이그레이션 경로

### 8.1 에이전트 코드 변경 사항

| 변경 | 노력 | 설명 |
|---|---|---|
| 설정 소스 | 낮음 | toml 파일 대신 K8s ConfigMap/Secret(환경 변수)에서 설정 읽기. 에이전트가 이미 환경 변수 설정을 지원. |
| 매니저 주소 해석 | 낮음 | 정적 IP 대신 K8s Service DNS 이름 사용. |
| 노드 리소스 감지 | 낮음 | 에이전트가 호스트 리소스(Pod 리소스가 아닌)를 감지. 호스트의 `/proc`, `/sys`에 접근 가능하도록 보장하거나 리소스 감지를 위해 `hostPID` 사용. |
| 스크래치 공간 경로 | 낮음 | 에이전트 Pod 마운트와 커널 컨테이너 바인드 마운트 간 스크래치 경로 일관성 보장. |
| 네트워크 플러그인 | 중간 | Docker 오버레이 네트워크 설정이 K8s 관리 노드에서 적응이 필요할 수 있음. |
| 커널 복구 | 없음 | 기존 `DockerKernelRegistryRecovery`가 그대로 동작. |
| GPU 감지 | 낮음 | 노드 선택에 NVIDIA 디바이스 플러그인 라벨 사용 보장; 에이전트 자체 GPU 감지는 호스트 `/dev/nvidia*` 사용. |

**Docker 기반 DooD 총 예상 노력: 2-4주**

### 8.2 매니저 코드 변경 사항

| 변경 | 노력 | 설명 |
|---|---|---|
| 에이전트 디스커버리 | 중간 | 현재 에이전트가 etcd 하트비트를 통해 등록. K8s에서도 변경 없이 동작. 선택적으로 K8s 네이티브 서비스 디스커버리로 향상. |
| 헬스 모니터링 | 낮음 | 에이전트 헬스 체크가 ZeroMQ를 통해 변경 없이 동작. |
| 리소스 스케줄링 | 낮음 | 변경 없음 — Sokovan 스케줄러가 에이전트 보고 슬롯 사용. |
| API 서버 | 없음 | 매니저 API 변경 없음; K8s Ingress가 외부 라우팅 처리. |

**총 예상 노력: 1-2주**

### 8.3 설정 변경 사항

| 현재 설정 | K8s 대응 |
|---|---|
| `agent.toml` | ConfigMap + Secret |
| `manager.toml` | ConfigMap + Secret |
| etcd 연결 문자열 | K8s Service DNS |
| PostgreSQL 연결 문자열 | K8s Service DNS + Secret |
| Redis 연결 문자열 | K8s Service DNS |
| Docker 데몬 주소 | hostPath 소켓 마운트 |
| 스토리지 마운트 경로 | hostPath 볼륨 마운트 |

---

## 9. 리스크 분석

### 9.1 기술적 리스크

| 리스크 | 확률 | 영향 | 설명 |
|---|---|---|---|
| K8s 리소스 회계 불일치 | 높음 | 중간 | K8s가 커널 컨테이너를 알지 못함. K8s 관점에서 노드가 과다 할당될 수 있음. |
| Docker Swarm + K8s 공존 | 중간 | 중간 | Docker Swarm과 K8s CNI가 동일 노드에서 IP 범위 충돌 가능. |
| 에이전트 Pod 축출 | 중간 | 높음 | K8s가 에이전트 Pod을 축출하면(리소스 압력), 에이전트 재시작까지 커널 컨테이너가 고아 상태. |
| 호스트 경로 권한 | 중간 | 낮음 | 에이전트 Pod이 호스트 경로 접근을 위해 올바른 UID/GID 매핑 필요. |
| GPU 디바이스 플러그인 충돌 | 중간 | 중간 | K8s NVIDIA 디바이스 플러그인이 K8s Pod에 GPU 할당. 에이전트가 커널 컨테이너에 GPU 할당. 이중 할당 가능성. |
| 네트워크 포트 충돌 | 낮음 | 중간 | 커널 컨테이너 포트 매핑이 K8s NodePort 범위(30000-32767)와 충돌 가능. |

### 9.2 운영 리스크

| 리스크 | 확률 | 영향 | 설명 |
|---|---|---|---|
| 디버깅 복잡성 | 높음 | 낮음 | 두 계층의 컨테이너 관리(에이전트용 K8s, 커널용 Docker)가 디버깅 복잡성 증가. |
| 로그 집계 | 중간 | 낮음 | 커널 컨테이너 로그가 Docker/containerd에 있으며, K8s 로깅 파이프라인에 없음. 별도 로그 수집 필요. |
| 모니터링 격차 | 중간 | 중간 | K8s 모니터링(Prometheus, metrics-server)이 커널 컨테이너를 보지 못함. Backend.AI 자체 모니터링이 격차를 채움. |
| 노드 드레인 동작 | 중간 | 높음 | `kubectl drain`이 에이전트 Pod을 축출하지만 커널 컨테이너는 축출하지 않음. 커스텀 드레인 절차 필요. |

### 9.3 완화 전략

**K8s 리소스 회계 불일치:**
- K8s 시스템 Pod(kubelet, kube-proxy, 에이전트, 모니터링)을 위해 노드 리소스의 고정 비율을 예약.
- 에이전트가 `total_slots - k8s_reserved`를 가용 슬롯으로 보고하도록 설정.
- K8s `allocatable`에서 DaemonSet 요청을 뺀 값을 Backend.AI 슬롯 계산의 기준으로 사용.

**GPU 디바이스 플러그인 충돌:**
- **옵션 A**: 에이전트 노드에 NVIDIA K8s 디바이스 플러그인을 배포하지 않음. Backend.AI가 모든 GPU 할당을 관리.
- **옵션 B**: 디바이스 플러그인은 배포하되 에이전트 노드에 taint를 적용하여 K8s GPU 워크로드를 방지. Backend.AI 에이전트가 디바이스 플러그인을 무시하고 GPU를 직접 관리.
- **권고**: 옵션 A — Backend.AI 에이전트 노드에 NVIDIA 디바이스 플러그인을 배포하지 않음.

**에이전트 Pod 축출:**
- 에이전트 DaemonSet에 전용 `PriorityClass`(`backendai-agent-critical`)를 설정.
- 메모리 압력 하에서 축출을 방지하기 위해 적절한 리소스 요청 설정.

**노드 드레인 절차:**
- 커스텀 드레인 스크립트 생성:
  1. 노드를 cordon (새 세션 방지).
  2. 모든 Backend.AI 세션이 완료되거나 마이그레이션될 때까지 대기.
  3. `kubectl drain`으로 에이전트 및 시스템 Pod 축출.

---

## 10. 대안적 접근 방식

### 10.1 순수 K8s 네이티브 (커널을 Pod으로)

DooD 대신 각 커널 세션을 K8s Pod으로 실행:

| 측면 | 평가 |
|---|---|
| GPU 할당 | K8s 디바이스 플러그인 모델로 제한 (전체 GPU만, CUDA 훅을 통한 분할 불가) |
| 멀티 GPU | K8s 리소스 요청으로 지원 |
| 분할 GPU | 네이티브로는 **지원 안 됨**; K8s 레벨에서 NVIDIA MPS/MIG 필요 |
| 네트워킹 | K8s CNI; 멀티 노드 세션을 위한 Docker Swarm 오버레이 없음 |
| 스토리지 | K8s PV/PVC; 직접 바인드 마운트 유연성 상실 |
| 에이전트 코드 영향 | 커널 라이프사이클 관리의 전면 재작성 필요 |
| K8s 가시성 | 완전 — 커널 Pod이 K8s에서 가시적, 적절한 리소스 회계 |

**판정**: 유의미한 기능 퇴보(분할 GPU, 오버레이 네트워킹)와 막대한 엔지니어링 노력. 단기적으로는 권고하지 않음.

### 10.2 하이브리드: 호스트 에이전트 + K8s 컨트롤 플레인

컨트롤 플레인만 K8s에서 실행; 에이전트는 베어메탈/VM 호스트에 유지:

| 측면 | 평가 |
|---|---|
| 에이전트 관리 | 수동 (Ansible, systemd) — 현재와 변경 없음 |
| 컨트롤 플레인 | K8s 관리 — 운영 이점 |
| 커널 라이프사이클 | 변경 없음 (호스트 Docker) |
| 코드 변경 | 최소 (K8s Service 디스커버리를 위한 매니저 설정) |

**판정**: 최저 리스크, 최저 노력이지만 K8s 에이전트 라이프사이클 관리 이점을 확보하지 못함. 좋은 중간 단계.

### 10.3 K8s Operator 패턴

Custom Resource(BackendAISession, BackendAIAgent)를 관리하는 Backend.AI K8s Operator 구축:

| 측면 | 평가 |
|---|---|
| K8s 통합 | 가장 깊음 — 완전히 K8s 네이티브 |
| GPU 할당 | 구현에 따라 다름 (디바이스 플러그인 + MIG 사용 가능, 또는 오퍼레이터 Pod 내 DooD) |
| 엔지니어링 노력 | 매우 높음 (프로덕션급 오퍼레이터에 6-12개월) |
| 운영 모델 | kubectl / K8s API를 통한 K8s 네이티브 CRUD |

**판정**: 최적의 장기 아키텍처이지만 상당한 투자가 필요. 향후 진화로 고려.

---

## 11. 필요 실험

이 섹션은 제안된 설계에 확정하기 전에 핵심 아키텍처 가정을 검증하기 위해 수행해야 하는 실험을 정의한다. 각 실험은 특정 리스크 또는 미검증 주장을 대상으로 한다.

### 11.1 EXP-1: DooD 컨테이너에 대한 CNI 직접 호출

| 항목 | 값 |
|---|---|
| **목적** | containerd/Docker DooD로 생성된 비K8s 컨테이너에 호스트의 CNI 플러그인 바이너리를 직접 호출하여 Pod 네트워크 IP를 할당할 수 있는지 검증 |
| **우선순위** | 핵심 |
| **차단 요소** | 멀티 노드 세션을 위한 containerd DooD 실현 가능성 |

**가설**: CNI 플러그인(Calico, Cilium)은 CNI 스펙을 준수하는 독립 바이너리이다. kubelet뿐만 아니라 어떤 프로세스든 컨테이너의 네트워크 네임스페이스에 대한 네트워킹 설정을 위해 이를 호출할 수 있다.

**절차**:

1. Calico(또는 Cilium)를 CNI로 하는 2노드 K8s 클러스터를 구성한다.
2. Node A에서 `nerdctl`(containerd) 또는 `docker run`으로 `--net=none`(자동 네트워킹 없이) 컨테이너를 생성한다.
3. 컨테이너의 PID와 네트워크 네임스페이스 경로(`/proc/<pid>/ns/net`)를 얻는다.
4. CNI 플러그인 바이너리를 직접 호출한다:
   ```bash
   export CNI_COMMAND=ADD
   export CNI_CONTAINERID=test-kernel-001
   export CNI_NETNS=/proc/<pid>/ns/net
   export CNI_IFNAME=eth0
   export CNI_PATH=/opt/cni/bin
   cat /etc/cni/net.d/10-calico.conflist | /opt/cni/bin/calico
   ```
5. 검증: 컨테이너가 Pod CIDR에서 IP를 받고, 호스트의 `ip route`에 컨테이너로의 경로가 보이며, 같은 노드의 다른 K8s Pod에서 `ping`이 성공한다.
6. 정리: `CNI_COMMAND=DEL`을 호출하고 IP가 IPAM 풀로 반환되는지 확인한다.

**성공 기준**:
- 컨테이너가 CNI IPAM 풀에서 유효한 IP를 받음
- 같은 노드의 K8s Pod에서 컨테이너에 도달 가능
- `CNI_COMMAND=DEL`로 IP가 적절히 반환됨
- calico-node / cilium-agent 로그에 오류 없음

**핵심 주의사항**: DooD 컨테이너에 K8s Pod IP 범위와 분리된 **전용 IP 풀/CIDR**을 사용한다. Calico의 경우 전용 `IPPool` 리소스를 생성한다. Cilium의 경우 별도의 `--cluster-pool-ipv4-cidr` 범위를 구성한다. kubelet이 관리하는 Pod과 에이전트가 관리하는 커널 컨테이너 간에 동일한 IPAM 풀을 절대 공유하지 않는다.

**실패 시 영향**: CNI 직접 호출이 동작하지 않으면, containerd DooD 경로는 멀티 노드 세션을 위해 커스텀 네트워킹 솔루션(WireGuard, 수동 VXLAN)이 필요하다.

---

### 11.2 EXP-2: CNI IPAM과 K8s Pod의 공존

| 항목 | 값 |
|---|---|
| **목적** | DooD 컨테이너에 할당된 CNI IP가 K8s 관리 Pod에 할당된 IP와 충돌하지 않는지 검증 |
| **우선순위** | 핵심 |
| **차단 요소** | 동일 노드에서 DooD 커널 컨테이너와 K8s Pod의 안전한 공존 |

**가설**: CNI IPAM(Calico IPAM, Cilium IPAM)은 etcd 또는 K8s CRD를 통해 IP 할당을 중앙에서 관리한다. kubelet이든 직접 CNI 호출이든 모든 호출자가 동일한 IPAM 백엔드를 거치므로 DooD 컨테이너에 전용 IP 풀을 사용하는 전제 하에, kubelet의 알려지지 않은 엔드포인트 가비지 컬렉션과의 간섭을 방지하면서 이중 할당이 방지된다.

**절차**:

1. 전제조건: EXP-1이 성공적으로 완료됨.
2. Node A에서 10개의 K8s Pod을 생성한다(Deployment 경유).
3. Node A에서 CNI 직접 호출(EXP-1의 방법)로 10개의 DooD 컨테이너를 생성한다.
4. 검증: 20개의 컨테이너/Pod 모두 고유한 IP를 가짐.
5. IPAM 상태 검사:
   - Calico: `calicoctl ipam show --show-blocks`
   - Cilium: `cilium-dbg bpf ipcache list`
6. K8s Pod 5개와 DooD 컨테이너 5개를 삭제한다. 새로 10개(혼합)를 생성한다. IP 재사용 충돌이 없는지 확인.
7. 스트레스 테스트: K8s가 Pod을 스케일업/다운하는 동안 50개의 DooD 컨테이너를 빠르게 생성하고 삭제한다.

**성공 기준**:
- 모든 반복에서 IP 충돌 제로
- IPAM 상태가 K8s Pod과 DooD 컨테이너 모두를 올바르게 반영
- 예상 용량을 넘어서는 IPAM 풀 고갈 없음

---

### 11.3 EXP-3: 호스트 CNI를 통한 크로스 노드 연결

| 항목 | 값 |
|---|---|
| **목적** | Node A의 DooD 컨테이너(CNI 할당 IP)가 Node B의 DooD 컨테이너와 기존 CNI 오버레이/라우팅을 통해 통신할 수 있는지 검증 |
| **우선순위** | 핵심 |
| **차단 요소** | containerd DooD에서의 멀티 노드 세션 실현 가능성 |

**가설**: CNI 오버레이 인프라(Calico의 VXLAN 터널, Cilium의 eBPF 등)는 Pod별이 아닌 노드 레벨에서 설정된다. CNI 할당 IP를 가진 노드의 어떤 컨테이너든 K8s Pod인지 여부와 관계없이 기존 오버레이를 통해 라우팅 가능해야 한다.

**절차**:

1. 전제조건: Node A와 Node B 모두에서 EXP-1 완료.
2. Node A에서 CNI 할당 IP(예: 10.244.1.50)를 가진 DooD 컨테이너 `kernel-A`를 생성한다.
3. Node B에서 CNI 할당 IP(예: 10.244.2.30)를 가진 DooD 컨테이너 `kernel-B`를 생성한다.
4. `kernel-A`에서 실행:
   ```bash
   ping 10.244.2.30          # ICMP 연결성
   nc -zv 10.244.2.30 22     # TCP 연결성 (SSH 포트)
   iperf3 -c 10.244.2.30     # 처리량 테스트
   ```
5. Node A의 K8s Pod에서 Node B의 `kernel-B`를 ping(교차 타입 연결성).
6. 동일 노드에서의 K8s pod-to-pod 통신과 레이턴시 및 처리량을 비교 측정한다.

**성공 기준**:
- 서로 다른 노드의 DooD 컨테이너 간 양방향 ICMP 및 TCP 연결성
- 교차 타입 연결성(K8s Pod ↔ DooD 컨테이너) 동작
- K8s pod-to-pod 기준 대비 10% 이내의 처리량
- 지속적 부하 하에서 패킷 드롭 없음

**실패 시 영향**: DooD 컨테이너에 대한 크로스 노드 라우팅이 동작하지 않으면, CNI 오버레이가 K8s API를 통해 알려진 엔드포인트만 라우팅하는 것이며, 커스텀 오버레이 솔루션이 필요하다.

---

### 11.4 EXP-4: DooD 커널 컨테이너에서 GPU 디바이스 접근

| 항목 | 값 |
|---|---|
| **목적** | DooD로 생성된 커널 컨테이너가 NVIDIA K8s 디바이스 플러그인 없이 호스트 GPU에 접근할 수 있는지 검증 |
| **우선순위** | 높음 |
| **차단 요소** | DooD 아키텍처에서의 GPU 워크로드 지원 |

**절차**:

1. NVIDIA GPU가 있는 K8s 노드를 구성한다. 이 노드에 NVIDIA K8s 디바이스 플러그인을 설치하지 **않는다**.
2. `privileged: true` 및 호스트 디바이스 마운트를 가진 에이전트 DaemonSet Pod을 배포한다.
3. 에이전트 Pod에서 GPU 접근이 가능한 커널 컨테이너를 DooD로 생성한다:
   ```bash
   # Docker DooD
   docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi

   # containerd DooD (nerdctl)
   nerdctl run --rm --device /dev/nvidia0 --device /dev/nvidiactl \
     --device /dev/nvidia-uvm nvidia/cuda:12.0-base nvidia-smi
   ```
4. 멀티 GPU 테스트:
   ```bash
   docker run --rm --gpus '"device=0,1"' nvidia/cuda:12.0-base nvidia-smi
   ```
5. 분할 GPU 테스트(CUDA 훅 라이브러리 주입):
   ```bash
   docker run --rm --gpus all \
     -v /path/to/cuda-hook:/usr/local/cuda-hook \
     -e LD_PRELOAD=/usr/local/cuda-hook/libcuda_hook.so \
     -e CUDA_SHARES=0.5 \
     nvidia/cuda:12.0-base python -c "import torch; print(torch.cuda.memory_allocated())"
   ```
6. K8s 리소스 회계와 충돌이 없는지 확인한다(디바이스 플러그인이 설치되지 않았으므로 K8s가 DooD 컨테이너의 GPU 사용을 보지 않아야 함).

**성공 기준**:
- DooD 컨테이너에서 단일 GPU, 멀티 GPU, 분할 GPU 모두 동작
- 커널 컨테이너 내부의 `nvidia-smi`가 올바른 GPU(들)를 표시
- K8s 스케줄러의 GPU 리소스 추적에 간섭 없음(디바이스 플러그인이 설치되지 않았으므로)
- CUDA 훅 라이브러리 주입이 베어메탈 배포와 동일하게 동작

---

### 11.5 EXP-5: 에이전트 Pod 재시작 및 커널 복구

| 항목 | 값 |
|---|---|
| **목적** | 커널 컨테이너가 에이전트 Pod 재시작에서 살아남고 새 에이전트 인스턴스에 의해 적절히 복구되는지 검증 |
| **우선순위** | 높음 |
| **차단 요소** | 롤링 업데이트 및 장애 복구 실현 가능성 |

**절차**:

1. 에이전트 DaemonSet을 배포한다. Backend.AI API를 통해 5개의 커널 세션을 생성한다.
2. 5개의 커널 모두 실행 중이고 응답하는지 확인한다.
3. 에이전트 Pod을 삭제한다: `kubectl delete pod <agent-pod> --grace-period=30`
4. DaemonSet이 새 에이전트 Pod을 재스케줄할 때까지 대기한다.
5. 검증:
   - 5개의 커널 컨테이너 모두 호스트에서 계속 실행 중(`docker ps` / `nerdctl ps`).
   - 새 에이전트 Pod이 `DockerKernelRegistryRecovery`를 통해 기존 커널을 발견하고 재연결.
   - Backend.AI 매니저에서 세션이 RUNNING으로 보고됨.
   - 새 에이전트를 통해 `docker exec` / 대화형 세션 접근이 동작.
6. `kubectl drain <node>`로 반복(에이전트 Pod은 축출하지만 DooD 컨테이너는 축출하지 않음).
7. 노드를 uncordon하고, 에이전트 Pod이 돌아와서 복구하는지 확인.
8. 네트워크 상태 정리 확인: 에이전트 Pod 재시작 후 호스트에 고아 veth 쌍이나 누수된 IP가 남아있지 않은지 확인한다. `ip link show | grep veth`를 실행하고 실행 중인 커널 컨테이너와 비교한다. CNI IPAM 상태가 실제 컨테이너 수와 일치하는지 확인한다.

**성공 기준**:
- 에이전트 Pod 재시작 중 커널 컨테이너 손실 제로
- 새 에이전트 Pod이 준비된 후 30초 이내 복구 시간
- 사용자 개입 없이 모든 세션이 RUNNING 상태로 복귀
- 커널 스크래치 공간이나 vfolder 마운트에서 데이터 손실 없음
- 에이전트 복구 후 고아 veth 쌍이나 누수된 IP 없음

---

### 11.6 EXP-6: containerd DooD 기본 라이프사이클

| 항목 | 값 |
|---|---|
| **목적** | K8s에서 실행 중인 Pod이 소켓 마운트를 통해 호스트의 containerd에서 컨테이너를 생성, 관리, 삭제할 수 있는지 검증 |
| **우선순위** | 중간 |
| **차단 요소** | containerd 기반 DooD 경로 (Phase 3) |

**절차**:

1. 호스트에서 `/run/containerd/containerd.sock`이 마운트된 테스트 Pod을 배포한다.
2. Pod 내부에서 `nerdctl` 또는 `ctr`을 사용한다:
   ```bash
   # backendai 네임스페이스에 이미지 pull
   nerdctl --namespace backendai pull python:3.11-slim

   # 컨테이너 생성 및 시작
   nerdctl --namespace backendai run -d --name test-kernel python:3.11-slim sleep 3600

   # 컨테이너에 exec
   nerdctl --namespace backendai exec test-kernel python -c "print('hello')"

   # 로그 확인
   nerdctl --namespace backendai logs test-kernel

   # 통계 확인
   nerdctl --namespace backendai stats test-kernel --no-stream

   # 중지 및 삭제
   nerdctl --namespace backendai rm -f test-kernel
   ```
3. 모든 작업이 성공하는지 확인한다.
4. `backendai` 네임스페이스의 컨테이너가 `kubectl get pods`에 나타나지 않는지 확인한다(K8s 네임스페이스 격리).
5. 호스트 경로의 바인드 마운트를 테스트한다:
   ```bash
   nerdctl --namespace backendai run -d --name test-mount \
     -v /mnt/vfolder/user1/folder1:/home/work/folder1:rw \
     python:3.11-slim sleep 3600
   ```

**성공 기준**:
- K8s Pod 내부에서 전체 컨테이너 라이프사이클(생성, exec, 로그, 통계, 삭제) 동작
- containerd 네임스페이스 격리가 K8s 관리 컨테이너와의 간섭 방지
- 호스트 경로 바인드 마운트가 올바르게 동작
- 리소스 제한(CPU, 메모리)이 cgroup을 통해 적절히 적용

---

### 11.7 EXP-7: vfolder 바인드 마운트 경로 일관성

| 항목 | 값 |
|---|---|
| **목적** | 에이전트 Pod에 마운트된 호스트 경로가 에이전트가 DooD로 커널 컨테이너를 생성할 때 해석 가능하고 일관적인지 검증 |
| **우선순위** | 높음 |
| **차단 요소** | vfolder 마운트 정확성 |

**배경**: DooD에서 에이전트 Pod은 `hostPath` 마운트를 통해 호스트 파일시스템을 본다. 에이전트가 커널 컨테이너를 생성하고 바인드 마운트를 지정할 때(예: `-v /mnt/vfolder/user1/data:/home/work/data`), 이 경로는 에이전트 Pod의 파일시스템이 아닌 **호스트** 파일시스템을 가리킨다. 경로가 일관적이어야 한다.

**절차**:

1. 호스트에 CephFS가 `/mnt/vfolder`에 마운트되어 있다.
2. 에이전트 Pod이 `/mnt/vfolder`를 `hostPath`로 마운트한다.
3. 에이전트가 바인드 마운트를 가진 커널 컨테이너를 생성한다: `-v /mnt/vfolder/user1/testdata:/home/work/testdata`.
4. 커널 컨테이너 내부에서:
   ```bash
   ls /home/work/testdata     # 파일이 보이는지 확인
   echo "test" > /home/work/testdata/output.txt  # 쓰기가 동작하는지 확인
   ```
5. 호스트에서: `/mnt/vfolder/user1/testdata/output.txt`가 존재하는지 확인.
6. 에이전트 Pod에서: 동일한 파일이 마운트에서 보이는지 확인.
7. 읽기 전용 마운트 테스트: `-v /mnt/vfolder/user1/testdata:/home/work/testdata:ro`.
8. 스크래치 공간 테스트: 에이전트가 `/var/cache/backendai/scratches/<kernel-id>/`에 쓰고, 커널이 `/home/work/`에서 볼 수 있는지.

**성공 기준**:
- 호스트, 에이전트 Pod, 커널 컨테이너 간 양방향 파일 가시성
- 읽기 전용 마운트가 올바르게 적용됨
- 스크래치 공간 경로가 세 개 컨텍스트 모두에서 일관적
- 공유 파일에서 권한(UID/GID) 문제 없음

---

### 11.8 EXP-8: Docker Swarm Overlay와 K8s CNI의 공존

| 항목 | 값 |
|---|---|
| **목적** | Docker Swarm 오버레이 네트워크가 K8s CNI(Calico/Cilium)와 동일 노드에서 IP 범위 또는 라우팅 충돌 없이 공존할 수 있는지 검증 |
| **우선순위** | 높음 (Docker DooD Phase 2용) |
| **차단 요소** | Docker DooD 배포에서의 멀티 노드 세션 네트워킹 |

**절차**:

1. Calico CNI(Pod CIDR: `10.244.0.0/16`)를 사용하는 2노드 K8s 클러스터를 구성한다.
2. 동일 노드에서 Docker Swarm을 초기화한다(기본 오버레이 서브넷: `10.0.0.0/8` — **겹침 방지를 위해 재설정 필요**).
3. 충돌하지 않는 CIDR로 Docker Swarm 오버레이 네트워크를 생성한다:
   ```bash
   docker network create -d overlay --subnet=172.30.0.0/16 backendai-overlay
   ```
4. K8s Pod과 DooD 커널 컨테이너를 동시에 배포한다:
   - K8s Pod: 10개의 nginx Pod (Calico 네트워크)
   - DooD 커널: Swarm 오버레이의 10개 컨테이너
5. 검증:
   - K8s Pod이 노드 간에 서로 도달 가능(Calico 오버레이).
   - DooD 커널이 노드 간에 서로 도달 가능(Swarm 오버레이).
   - 교차 오염 없음: K8s Pod이 실수로 Swarm IP로 라우팅되거나 그 반대가 되지 않음.
   - 호스트의 `ip route`가 두 오버레이에 대해 별도의 라우팅 테이블을 표시.
6. 스트레스 테스트: 둘 다 50개 Pod/컨테이너로 확장하고 안정성을 확인.

**성공 기준**:
- 두 오버레이가 동일 노드에서 독립적으로 기능
- IP 범위 충돌 없음 (명시적 CIDR 계획 필요)
- 라우팅 테이블 손상 또는 패킷 오라우팅 없음
- 동시 확장 하에서 안정적

**실패 시 영향**: Swarm과 K8s CNI가 충돌하면, Docker DooD Phase 2는 (a) Swarm 오버레이를 사용하지 않거나(호스트 네트워킹 + 수동 포트 할당으로 폴백), (b) Docker DooD 단계에서도 CNI 직접 호출(EXP-1/EXP-3)을 사용해야 한다.

---

### 11.9 실험 실행 우선순위

| 순서 | 실험 | 단계 의존성 | 예상 소요 |
|---|---|---|---|
| 1 | EXP-7: vfolder 바인드 마운트 경로 | Phase 2 (Docker DooD) | 0.5일 |
| 2 | EXP-4: GPU 디바이스 접근 | Phase 2 (Docker DooD) | 0.5일 |
| 3 | EXP-8: Swarm + K8s CNI 공존 | Phase 2 (Docker DooD) | 1일 |
| 4 | EXP-5: 에이전트 재시작 복구 | Phase 2 (Docker DooD) | 1일 |
| 5 | EXP-1: CNI 직접 호출 | Phase 3 (containerd) | 0.5일 |
| 6 | EXP-2: IPAM 공존 | Phase 3 (containerd) | 0.5일 |
| 7 | EXP-3: 크로스 노드 CNI 연결 | Phase 3 (containerd) | 1일 |
| 8 | EXP-6: containerd DooD 라이프사이클 | Phase 3 (containerd) | 1일 |

EXP-1부터 EXP-3(CNI 직접 호출)이 아키텍처적으로 가장 중요한 실험이다. 이들의 결과가 containerd DooD가 멀티 노드 세션에 호스트 CNI를 사용할 수 있는지, 아니면 커스텀 오버레이 솔루션이 필요한지를 결정한다.

---

## 12. 결론 및 권고사항

### 12.1 발견 사항 요약

DooD 기반 아키텍처(에이전트를 K8s DaemonSet으로 + 커널은 호스트 컨테이너 런타임)는 K8s 운영 이점과 Backend.AI 기능 보존 사이의 최적 균형을 제공한다:

1. **완전한 GPU 기능 동등성**: 멀티 GPU, 분할 GPU, CUDA 훅 라이브러리, 모든 컴퓨트 플러그인이 변경 없이 동작.
2. **완전한 스토리지 기능 동등성**: vfolder 바인드 마운트, 스크래치 공간, 분산 파일시스템 마운트가 변경 없이 동작.
3. **최소한의 코드 변경**: 기존 `DockerAgent`가 DooD로 동작. 설정과 서비스 디스커버리가 주요 변경 사항.
4. **K8s 운영 이점**: 컨트롤 플레인과 에이전트 라이프사이클을 위한 롤링 업데이트, 자가 복구, 선언적 설정, Helm 기반 배포.
5. **알려진 트레이드오프**: 커널 컨테이너가 K8s에서 보이지 않아, 과다 할당 방지를 위해 Backend.AI 자체 리소스 관리가 필요.

### 12.2 권고 접근 방법

**Phase 1 (1-2개월): 하이브리드 — K8s에 컨트롤 플레인, 호스트에 에이전트**
- Manager, PostgreSQL, Redis, etcd를 K8s 워크로드로 배포.
- 에이전트는 베어메탈/VM 호스트에 유지, K8s 호스팅 컨트롤 플레인에 연결.
- 에이전트 리스크 없이 컨트롤 플레인 K8s 배포를 검증.

**Phase 2 (2-3개월): Docker를 사용한 DooD 에이전트 DaemonSet**
- Docker 소켓 마운트(DooD)를 가진 K8s DaemonSet으로 에이전트 배포.
- 커널 컨테이너 관리를 위해 Docker 데몬이 호스트에 유지.
- 멀티 노드 세션을 위한 Docker Swarm 오버레이.
- GPU 디바이스 플러그인 충돌 해결(에이전트 노드에서 K8s 디바이스 플러그인 비활성화).

**Phase 3 (6-12개월): containerd 마이그레이션 (선택)**
- Docker 데몬 의존성을 제거하는 containerd 네이티브 에이전트 백엔드 개발.
- 대안적 멀티 노드 세션 네트워킹(CNI 기반 또는 WireGuard) 구현.
- GPU 관리를 CDI로 마이그레이션.

### 12.3 컨테이너 런타임 권고

| 배포 시나리오 | 런타임 | 확신도 |
|---|---|---|
| 초기 K8s 마이그레이션 | **Docker** | 높음 |
| 단일 노드 세션만 (멀티 노드 없음) | **containerd** (중간 노력으로 현재 실현 가능) | 중간 |
| 장기적 목표 | **containerd** | 높음 |
| 멀티 노드 세션 (Swarm 오버레이 필요) | **Docker** (대안 오버레이가 구축될 때까지) | 높음 |

---

## 13. 참고 문헌

### Backend.AI 내부
1. Backend.AI Agent Docker 구현. `src/ai/backend/agent/docker/agent.py`
2. Backend.AI Agent Kubernetes 구현. `src/ai/backend/agent/kubernetes/agent.py`
3. Backend.AI Agent 타입 및 백엔드. `src/ai/backend/agent/types.py`
4. Kata Containers 기능 동등성 분석. `docs/reports/kata-containers-feature-parity-analysis.md`

### Kubernetes
5. Kubernetes DaemonSet 문서. https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/
6. Kubernetes Container Runtime Interface (CRI). https://kubernetes.io/docs/concepts/architecture/cri/
7. CloudNativePG Operator. https://cloudnative-pg.io/
8. NVIDIA GPU Operator for Kubernetes. https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/

### 컨테이너 런타임
9. containerd 아키텍처. https://github.com/containerd/containerd/blob/main/docs/getting-started.md
10. nerdctl: containerd용 Docker 호환 CLI. https://github.com/containerd/nerdctl
11. Container Device Interface (CDI) 사양. https://github.com/cncf-tags/container-device-interface
12. Docker Engine API 참조. https://docs.docker.com/engine/api/

### DooD 패턴
13. Docker-out-of-Docker 패턴. https://jpetazzo.github.io/2015/09/03/do-not-use-docker-in-docker-for-ci/
14. DooD 보안 고려사항. https://docs.docker.com/engine/security/
