# Docker ShmSize와 Memory 동작 검증

## 목적

Backend.AI Docker agent의 shmem 설정 로직이 올바른지 검증

---

## 결론 요약

**❌ 현재 Backend.AI 로직에 버그가 있음 - 불필요한 메모리 사전 차감**

| 구분 | 내용 |
|------|------|
| **Docker 동작** | shm과 app memory가 **Memory cgroup을 공유**하며, shm은 추가로 **ShmSize limit** 제한을 받음 |
| **문제** | Backend.AI가 설정 시점에 Memory에서 shmem을 미리 차감하여 cgroup 크기 자체를 줄임 |
| **결과** | 사용자가 요청한 메모리보다 적게 제공됨 |
| **해결** | `Memory -= shmem` 코드 제거 |

---

## AS-IS vs TO-BE

### AS-IS: 현재 코드 (잘못됨)

```python
# src/ai/backend/agent/docker/agent.py:1157-1161
if resource_opts and resource_opts.get("shmem"):
    shmem = int(resource_opts.get("shmem", "0"))
    self.computer_docker_args["HostConfig"]["ShmSize"] = shmem
    self.computer_docker_args["HostConfig"]["MemorySwap"] -= shmem  # ❌ 불필요
    self.computer_docker_args["HostConfig"]["Memory"] -= shmem      # ❌ 불필요
```

**User Request**: 4GB memory + 1GB shmem

```
AS-IS Flow:
┌────────────────────────────────────────────────────────────────┐
│ Step 1: Backend.AI Configuration                               │
│    Memory = 4GB - 1GB = 3GB (unnecessary pre-deduction)        │
│    ShmSize = 1GB                                               │
├────────────────────────────────────────────────────────────────┤
│ Step 2: Docker Container Creation                              │
│                                                                │
│    ┌─────────────── Memory cgroup: 3GB ───────────────┐        │
│    │                                                  │        │
│    │   ┌─────────┐    ┌──────────────────────────┐    │        │
│    │   │/dev/shm │    │      App RAM             │    │        │
│    │   │ (1GB)   │    │      (???)               │    │        │
│    │   └─────────┘    └──────────────────────────┘    │        │
│    │                                                  │        │
│    │   <────── shm + app share 3GB pool ──────>       │        │
│    └──────────────────────────────────────────────────┘        │
├────────────────────────────────────────────────────────────────┤
│ Step 3: Runtime shm 1GB usage                                  │
│    -> shm 1GB uses space from 3GB cgroup                       │
│    -> Remaining for app: 3GB - 1GB = 2GB                       │
├────────────────────────────────────────────────────────────────┤
│ Final Result: 2GB app + 1GB shm = 3GB total                    │
│               (NOT the intended 4GB!)                          │
└────────────────────────────────────────────────────────────────┘
```

→ cgroup 크기가 3GB로 줄어들어 사용자가 의도한 4GB가 아닌 3GB만 사용 가능 ❌
  - shm 미사용 시: app이 3GB 사용 가능
  - shm 1GB 사용 시: app이 **2GB만** 사용 가능 (1GB 부족)

### TO-BE: 수정 후 코드 (올바름)

```python
# 수정된 코드
if resource_opts and resource_opts.get("shmem"):
    shmem = int(resource_opts.get("shmem", "0"))
    self.computer_docker_args["HostConfig"]["ShmSize"] = shmem
    # Memory와 MemorySwap은 그대로 유지 (shm + app이 cgroup 공간 공유)
```

**User Request**: 4GB memory + 1GB shmem

```
TO-BE Flow:
┌────────────────────────────────────────────────────────────────┐
│ Step 1: Backend.AI Configuration                               │
│    Memory = 4GB (no pre-deduction)                             │
│    ShmSize = 1GB                                               │
├────────────────────────────────────────────────────────────────┤
│ Step 2: Docker Container Creation                              │
│                                                                │
│    ┌─────────────── Memory cgroup: 4GB ───────────────┐        │
│    │                                                  │        │
│    │   ┌─────────┐    ┌──────────────────────────┐    │        │
│    │   │/dev/shm │    │      App RAM             │    │        │
│    │   │ (1GB)   │    │      (3GB available)     │    │        │
│    │   └─────────┘    └──────────────────────────┘    │        │
│    │                                                  │        │
│    │   <────── shm + app share 4GB pool ──────>       │        │
│    └──────────────────────────────────────────────────┘        │
├────────────────────────────────────────────────────────────────┤
│ Step 3: Runtime shm 1GB usage                                  │
│    -> shm 1GB uses space from 4GB cgroup                       │
│    -> Remaining for app: 4GB - 1GB = 3GB                       │
├────────────────────────────────────────────────────────────────┤
│ Final Result: 3GB app + 1GB shm = 4GB total                    │
│               (Works as intended!)                             │
└────────────────────────────────────────────────────────────────┘
```

→ cgroup 4GB 전체를 shm + app이 공유하여 사용자가 의도한 대로 4GB 사용 가능 ✅
  - shm 미사용 시: app이 4GB 사용 가능
  - shm 1GB 사용 시: app이 **3GB** 사용 가능 (의도대로)

### 비교 요약

| 항목 | AS-IS (현재) | TO-BE (수정 후) |
|------|-------------|----------------|
| 사용자 요청 | 4GB + 1GB shmem | 4GB + 1GB shmem |
| Memory cgroup 설정 | 3GB (불필요한 사전 차감) | 4GB (차감 없음) |
| ShmSize 설정 | 1GB | 1GB |
| 런타임 shm 사용 | 1GB | 1GB |
| 가용 app RAM | **2GB** | **3GB** |
| 총 사용 가능 (shm + app) | **3GB** ❌ | **4GB** ✅ |

---

## 실험 결과

### 가설 1: shm과 app이 Memory cgroup을 공유하는지

**가설**: shm은 Memory cgroup limit과 **별개**로 동작한다 (app만 cgroup 제한을 받음)

| 설정 | 값 |
|------|-----|
| `--memory` | 1GB |
| `--shm-size` | 1GB |

| 테스트 | 가설이 맞다면 | 가설이 틀리다면 | 실제 결과 |
|--------|-------------|---------------|----------|
| shm 900MB + RAM 900MB | ✅ 성공 (별개) | ❌ OOM (합산) | ❌ **OOM** |
| RAM 1200MB (기준선) | ❌ OOM | ❌ OOM | ❌ OOM |

**결론**: ❌ **가설 기각** - shm과 app은 Memory cgroup을 **공유**함

---

### 가설 2: ShmSize 제한이 실제로 적용되는지

**가설**: `--shm-size` 제한을 초과하면 shm 할당이 **실패**한다

| 설정 | 값 |
|------|-----|
| `--memory` | 4GB |
| `--shm-size` | 512MB |

| 테스트 | 가설이 맞다면 | 가설이 틀리다면 | 실제 결과 |
|--------|-------------|---------------|----------|
| shm 400MB 할당 + 쓰기 | ✅ 성공 | ✅ 성공 | ✅ **성공** |
| shm 600MB 할당 + 쓰기 | ❌ 실패 | ✅ 성공 | ❌ **SIGBUS** |

**결론**: ✅ **가설 검증됨** - ShmSize 제한이 적용됨 (실제 쓰기 시 SIGBUS 발생)

---

### 가설 3: app memory가 shm 영역을 침범할 수 있는지

**가설**: shm을 사용하지 않아도 app memory는 **Memory limit까지만** 사용 가능하다

| 설정 | 값 |
|------|-----|
| `--memory` | 2GB |
| `--shm-size` | 1GB |

| 테스트 | 가설이 맞다면 | 가설이 틀리다면 | 실제 결과 |
|--------|-------------|---------------|----------|
| RAM 1800MB | ✅ 성공 | ✅ 성공 | ✅ **성공** |
| RAM 2500MB | ❌ OOM | ✅ 성공 | ❌ **OOM** |

**결론**: ✅ **가설 검증됨** - app은 Memory limit까지만 사용 가능 (shm 영역 침범 불가)

---

### 가설 4: shm 사용 시 app memory 최대량

**가설**: shm이 Memory와 **별개**라면, shm 사용 중에도 Memory limit까지 RAM 사용 가능

| 설정 | 값 |
|------|-----|
| `--memory` | 2GB |
| `--shm-size` | 1GB |

| 테스트 | 가설이 맞다면 | 가설이 틀리다면 | 실제 결과 |
|--------|-------------|---------------|----------|
| shm 800MB + RAM 1100MB (1.9GB) | ✅ 성공 | ✅ 성공 | ✅ **성공** |
| shm 800MB + RAM 1300MB (2.1GB) | ✅ 성공 | ❌ OOM | ❌ **OOM** |

**결론**: ❌ **가설 기각** - shm 사용량만큼 가용 RAM이 **감소**함

---

### 가설 5: shm 미사용 시 app memory 최대량

**가설**: shm 미사용 시 app memory는 **Memory limit까지** 사용 가능

| 설정 | 값 |
|------|-----|
| `--memory` | 2GB |
| `--shm-size` | 1GB |

| 테스트 | 가설이 맞다면 | 가설이 틀리다면 | 실제 결과 |
|--------|-------------|---------------|----------|
| RAM 1800MB | ✅ 성공 | ❌ OOM | ✅ **성공** |
| RAM 2500MB | ❌ OOM | ❌ OOM | ❌ **OOM** |

**결론**: ✅ **가설 검증됨** - shm 미사용 시 Memory limit까지 RAM 사용 가능

---

### 가설 6: 할당 순서가 결과에 영향을 주는지

**가설**: 할당 순서와 관계없이 shm + RAM 합계가 **Memory cgroup limit에 제한**됨

| 설정 | 값 |
|------|-----|
| `--memory` | 2GB |
| `--shm-size` | 1GB |

| 테스트 | 가설이 맞다면 | 가설이 틀리다면 | 실제 결과 |
|--------|-------------|---------------|----------|
| RAM 1100MB → shm 800MB (1.9GB) | ✅ 성공 | ✅ 성공 | ✅ **성공** |
| RAM 1300MB → shm 800MB (2.1GB) | ❌ 실패 | ✅ 성공 | ❌ **OOM** |
| shm 800MB → RAM 1100MB (1.9GB) | ✅ 성공 | ✅ 성공 | ✅ **성공** |
| shm 800MB → RAM 1300MB (2.1GB) | ❌ 실패 | ✅ 성공 | ❌ **OOM** |

**결론**: ✅ **가설 검증됨** - 할당 순서와 관계없이 동일한 결과, shm + RAM은 Memory cgroup 내에서 공유됨

---

### 가설 7: ShmSize > Memory 설정 시 동작

**가설**: ShmSize가 Memory보다 커도 실제 사용은 **Memory cgroup limit에 제한**됨

| 설정 | 값 |
|------|-----|
| `--memory` | 1GB |
| `--shm-size` | 2GB |

| 테스트 | 가설이 맞다면 | 가설이 틀리다면 | 실제 결과 |
|--------|-------------|---------------|----------|
| shm 800MB (Memory 이하) | ✅ 성공 | ✅ 성공 | ✅ **성공** |
| shm 1200MB (Memory 초과) | ❌ OOM | ✅ 성공 | ❌ **OOM** |
| shm 500MB + RAM 400MB (0.9GB) | ✅ 성공 | ✅ 성공 | ✅ **성공** |
| shm 500MB + RAM 700MB (1.2GB) | ❌ OOM | ✅ 성공 | ❌ **OOM** |

**결론**: ✅ **가설 검증됨** - ShmSize > Memory여도 Memory cgroup이 우선 적용됨

---

### 가설 8: shm 해제 후 메모리 반환 확인

**가설**: shm 해제 시 메모리가 **반환되어 RAM으로 재사용 가능**

| 설정 | 값 |
|------|-----|
| `--memory` | 1GB |
| `--shm-size` | 1GB |

| 테스트 | 가설이 맞다면 | 가설이 틀리다면 | 실제 결과 |
|--------|-------------|---------------|----------|
| shm 700MB 유지 + RAM 500MB | ❌ OOM | ❌ OOM | ❌ **OOM** |
| shm 700MB 해제 → RAM 500MB | ✅ 성공 | ❌ OOM | ✅ **성공** |
| shm 700MB 해제 → RAM 900MB | ✅ 성공 | ❌ OOM | ✅ **성공** |
| shm 700MB 해제 → RAM 1200MB | ❌ OOM | ❌ OOM | ❌ **OOM** |

**결론**: ✅ **가설 검증됨** - shm 해제 시 메모리가 정상적으로 반환되어 RAM으로 재사용 가능

---

## 실험 결과 요약

| 가설 | 결과 | 의미 |
|------|------|------|
| 1. shm과 app이 cgroup 공유? | ❌ 기각 | **shm과 app이 Memory cgroup 공유** |
| 2. ShmSize 제한 적용? | ✅ 검증 | shm은 추가로 ShmSize 제한 받음 (SIGBUS) |
| 3. app이 shm 침범 가능? | ✅ 검증 | 침범 불가 (Memory limit 적용) |
| 4. shm 사용 시 RAM 최대량 | ❌ 기각 | **shm 사용량만큼 app RAM 감소** |
| 5. shm 미사용 시 RAM 최대량 | ✅ 검증 | Memory limit까지 사용 가능 |
| 6. 할당 순서가 결과에 영향? | ✅ 검증 | **순서 무관, 동일 cgroup 공유** |
| 7. ShmSize > Memory 시? | ✅ 검증 | **Memory cgroup이 우선 적용됨** |
| 8. shm 해제 후 메모리 반환? | ✅ 검증 | **반환 후 app RAM으로 재사용 가능** |

**핵심 결론**: shm(tmpfs)과 app memory는 Docker Memory cgroup 공간을 **공유**함.
shm은 추가로 ShmSize limit 제한을 받음. Backend.AI의 사전 차감(`Memory -= shmem`)은
cgroup 크기 자체를 줄여서 **불필요하게 가용 메모리를 감소**시킴.

---

## Docker 메모리 구조 이해

```
┌────────────────────────────────────────────────────────────────┐
│                     Docker Container                           │
│                                                                │
│    ┌─────────────── Memory cgroup limit ───────────────┐       │
│    │                    (e.g. 4GB)                     │       │
│    │                                                   │       │
│    │    ┌────────────────┐    ┌─────────────────────┐  │       │
│    │    │   /dev/shm     │    │    App Memory       │  │       │
│    │    │   (tmpfs)      │    │    (heap, stack,    │  │       │
│    │    │                │    │     mmap, etc.)     │  │       │
│    │    │  ◄─ ShmSize ─► │    │                     │  │       │
│    │    │   limit (1GB)  │    │                     │  │       │
│    │    └────────────────┘    └─────────────────────┘  │       │
│    │                                                   │       │
│    │    <──────── shm + app share this pool ────────>  │       │
│    │                                                   │       │
│    └───────────────────────────────────────────────────┘       │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

**제한 구조**:
- **Memory cgroup** (`--memory`): shm + app 전체 합계 제한
- **ShmSize** (`--shm-size`): shm만 추가로 제한 (tmpfs 최대 크기)

**shm의 실제 사용 가능량** = `min(ShmSize, Memory cgroup 여유 공간)`

---

## OOM 발생 조건

Docker 컨테이너에서 메모리 관련 OOM은 두 가지 조건에서 발생합니다.

### OOM 발생 규칙

| 조건 | 신호 | Exit Code | 발생 시점 |
|------|------|-----------|----------|
| `shm + app > Memory cgroup limit` | SIGKILL | 137 | cgroup 메모리 초과 |
| `shm > min(ShmSize, Memory)` | SIGBUS | 135 | tmpfs 공간 초과 |

### Case 1: cgroup OOM (SIGKILL)

shm 사용량 + app memory 사용량이 Memory cgroup limit을 초과할 때 발생

```
Example: --memory=2g, --shm-size=1g

┌─────────────────────────────────────────────────────────────────┐
│                  Memory cgroup limit: 2GB                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│    shm 800MB        +        app 1300MB     =    2.1GB          │
│   ┌─────────┐              ┌─────────────┐                      │
│   │ /dev/shm│              │  App RAM    │                      │
│   │  800MB  │              │   1300MB    │                      │
│   └─────────┘              └─────────────┘                      │
│                                                                 │
│   <------------ Total: 2.1GB (exceeds 2GB) ----------->         │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ Result: SIGKILL (exit 137) - OOM Killer terminates process      │
└─────────────────────────────────────────────────────────────────┘
```

→ shm과 app memory 합계가 cgroup limit 초과 시 OOM Killer가 프로세스 종료

### Case 2: tmpfs OOM (SIGBUS)

shm 사용량이 ShmSize 또는 Memory cgroup limit 중 작은 값을 초과할 때 발생

```
Example A: ShmSize < Memory (ShmSize가 제한)
--memory=4g, --shm-size=512m

┌─────────────────────────────────────────────────────────────────┐
│                  Memory cgroup limit: 4GB                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────────┐                                           │
│   │   /dev/shm      │  Trying to write 600MB                    │
│   │   limit: 512MB  │  but ShmSize = 512MB                      │
│   │   ┌─────────┐   │                                           │
│   │   │XXXXXXXXX│   │  <- SIGBUS at ~512MB                      │
│   │   └─────────┘   │                                           │
│   └─────────────────┘                                           │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ Result: SIGBUS (exit 135) - tmpfs space exhausted               │
└─────────────────────────────────────────────────────────────────┘


Example B: Memory < ShmSize (Memory가 제한)
--memory=1g, --shm-size=2g

┌─────────────────────────────────────────────────────────────────┐
│                  Memory cgroup limit: 1GB                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────────┐                                           │
│   │   /dev/shm      │  Trying to write 1200MB                   │
│   │   limit: 2GB    │  but Memory cgroup = 1GB                  │
│   │   ┌─────────┐   │                                           │
│   │   │XXXXXXXXX│   │  <- OOM at ~1GB (cgroup limit)            │
│   │   └─────────┘   │                                           │
│   └─────────────────┘                                           │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ Result: SIGKILL (exit 137) - cgroup memory exhausted            │
└─────────────────────────────────────────────────────────────────┘
```

→ shm의 실제 사용 가능량 = **min(ShmSize, Memory cgroup limit)**

### OOM 조건 요약

```
Effective shm limit = min(ShmSize, Memory)

OOM 발생 조건:
┌─────────────────────────────────────────────────────────────────┐
│ 1. shm_usage > min(ShmSize, Memory)                             │
│    -> SIGBUS (tmpfs full) or SIGKILL (cgroup OOM)               │
│                                                                 │
│ 2. shm_usage + app_usage > Memory                               │
│    -> SIGKILL (cgroup OOM)                                      │
└─────────────────────────────────────────────────────────────────┘

Safe operation condition:
┌─────────────────────────────────────────────────────────────────┐
│ shm_usage ≤ min(ShmSize, Memory)                                │
│           AND                                                   │
│ shm_usage + app_usage ≤ Memory                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 레퍼런스 및 근거

### 1. Linux Kernel 문서 - cgroup v1 Memory (가장 직접적인 근거)

**출처**: [Memory Resource Controller - Linux Kernel Documentation](https://www.kernel.org/doc/Documentation/cgroup-v1/memory.txt)

**주요 내용**:

Section 2.3 - Shared Page Accounting:
> "Shared pages are accounted on the basis of the **first touch approach**. The cgroup that first touches a page is accounted for the page."

Section 8.2 - Type of charges which can be moved:
> "A charge of file pages (normal file, **tmpfs file (e.g. ipc shared memory)** and swaps of tmpfs file) mmapped by the target task"

**해석**:
- tmpfs/shm은 cgroup memory 공간에 속하는 메모리 타입임 (file pages의 일종)
- **first touch 원칙**: 해당 메모리를 처음 할당(touch)한 cgroup이 메모리 사용량에 대해 책임짐
- 따라서 컨테이너 내에서 shm을 할당하면 해당 컨테이너의 cgroup memory에 charge됨

---

### 2. Linux Kernel 문서 - cgroup v2 Memory Controller

**출처**: [Control Group v2 - Linux Kernel Documentation](https://docs.kernel.org/admin-guide/cgroup-v2.html)

**주요 내용**:
> "memory.max: Memory usage hard limit. If a cgroup's memory usage reaches this limit and can't be reduced, the OOM killer is invoked in the cgroup."

> "memory.stat: ... shmem: Amount of cached filesystem data that is swap-backed, such as **tmpfs, shm segments, shared anonymous mmap()s**"

**해석**:
- `memory.max`는 cgroup memory의 hard limit
- `shmem`은 `memory.stat`에 포함된 메모리 타입 중 하나 (anon, file 등과 동급)
- 따라서 shmem(tmpfs, shm 포함)은 **memory의 일부**로 계산되어 limit 적용을 받음

---

### 레퍼런스 요약

| 주장 | 근거 | 결론 |
|------|------|------|
| tmpfs/shm은 cgroup memory에 속함 | Kernel Docs (cgroup v1 §8.2) | ✅ 확인됨 |
| first touch한 cgroup이 charge 책임 | Kernel Docs (cgroup v1 §2.3) | ✅ 확인됨 |
| shmem은 memory.stat의 일부 | Kernel Docs (cgroup v2) | ✅ 확인됨 |
| shm + app이 Memory cgroup 공유 | 본 실험 결과 | ✅ 확인됨 |
| Backend.AI의 사전 차감은 불필요 | 위 모든 근거 | ✅ 확인됨 |

---

## 테스트 스크립트 실행 가이드

### 사전 요구사항

- Docker 설치 및 실행 중
- Bash 쉘
- 최소 4GB 여유 메모리

### 전체 테스트 실행

```bash
cd /path/to/backend.ai

# 실행 권한 부여
chmod +x scripts/docker_shm_test/*.sh

# 전체 테스트 실행
./scripts/docker_shm_test/run_all.sh
```

### 개별 시나리오 실행

```bash
# 시나리오 1: shm이 Memory에 포함되는지
./scripts/docker_shm_test/scenario1_shm_in_memory.sh

# 시나리오 2: ShmSize 제한 적용 여부
./scripts/docker_shm_test/scenario2_shm_limit.sh

# 시나리오 3: app이 shm 영역 침범 가능한지
./scripts/docker_shm_test/scenario3_app_invade_shm.sh

# 시나리오 4: shm 사용 시 app memory 최대량
./scripts/docker_shm_test/scenario4_shm_used_app_max.sh

# 시나리오 5: shm 미사용 시 app memory 최대량
./scripts/docker_shm_test/scenario5_shm_unused_app_max.sh

# 시나리오 6: RAM 먼저 할당 후 shm 할당
./scripts/docker_shm_test/scenario6_ram_first_then_shm.sh

# 시나리오 7: ShmSize > Memory 설정 시
./scripts/docker_shm_test/scenario7_shmsize_gt_memory.sh

# 시나리오 8: shm 해제 후 메모리 반환
./scripts/docker_shm_test/scenario8_shm_release_reclaim.sh
```

### 파일 구조

```
scripts/docker_shm_test/
├── README.md                         # 이 문서
├── allocate_memory.py                # Python 메모리 할당 테스트 스크립트
├── common.sh                         # 공통 함수 (run_test)
├── run_all.sh                        # 전체 테스트 실행
├── scenario1_shm_in_memory.sh        # shm이 Memory에 포함되는지
├── scenario2_shm_limit.sh            # ShmSize 제한 적용 여부
├── scenario3_app_invade_shm.sh       # app이 shm 영역 침범 가능한지
├── scenario4_shm_used_app_max.sh     # shm 사용 시 RAM 최대량
├── scenario5_shm_unused_app_max.sh   # shm 미사용 시 RAM 최대량
├── scenario6_ram_first_then_shm.sh   # RAM 먼저 할당 후 shm 할당
├── scenario7_shmsize_gt_memory.sh    # ShmSize > Memory 설정 시
└── scenario8_shm_release_reclaim.sh  # shm 해제 후 메모리 반환
```

---

## 기술적 배경

### POSIX Shared Memory와 Lazy Allocation

```python
from multiprocessing.shared_memory import SharedMemory

# 할당만 하면 실제 메모리 사용 안 됨 (lazy allocation)
shm = SharedMemory(create=True, size=500*1024*1024)

# 실제 쓰기를 해야 메모리가 할당됨
for i in range(0, len(shm.buf), 4096):
    shm.buf[i] = 0xFF  # 페이지 폴트 → 실제 할당
```

**주의**: 이 테스트 스크립트는 실제 쓰기를 수행하여 정확한 결과를 얻음.

### Exit Codes

| Exit Code | 신호 | 의미 |
|-----------|------|------|
| 0 | - | 성공 |
| 135 | SIGBUS (128+7) | tmpfs 공간 부족 |
| 137 | SIGKILL (128+9) | OOM Killer |

### SIGKILL vs SIGBUS 상세 비교

두 신호는 발생하는 레이어와 원인이 다릅니다.

**SIGKILL (Exit code 137 = 128 + 9)**

| 항목 | 내용 |
|------|------|
| 발생 원인 | Linux OOM Killer가 프로세스를 강제 종료 |
| 발생 레이어 | cgroup memory controller (커널 메모리 관리) |
| 발생 조건 | `shm + app > Memory cgroup limit` |
| 특징 | catch/block/ignore 불가능 |
| Docker 설정 | `--memory` 제한 초과 시 |

**SIGBUS (Exit code 135 = 128 + 7)**

| 항목 | 내용 |
|------|------|
| 발생 원인 | 메모리 접근 오류 (Bus Error) |
| 발생 레이어 | tmpfs 파일시스템 (mmap 레벨) |
| 발생 조건 | `shm > ShmSize` (단, ShmSize < Memory일 때) |
| 특징 | 기술적으로 catch 가능 (하지만 복구 불가) |
| Docker 설정 | `--shm-size` 제한 초과 시 |

**발생 레이어 다이어그램**

```
┌─────────────────────────────────────────────────────────────────┐
│                      User Process (Python/App)                  │
│                     malloc(), mmap(), shm_open()                │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      tmpfs (/dev/shm)                           │
│                                                                 │
│   ShmSize limit check                                           │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ shm write exceeds ShmSize?  ────────────→  SIGBUS (135) │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│   * tmpfs uses RAM as backing storage                           │
│   * SIGBUS on page fault when space exhausted                   │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                Memory cgroup (Docker --memory)                  │
│                                                                 │
│   cgroup limit check (shm + app memory combined)                │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Total exceeds Memory?  ─────────────────→  SIGKILL (137)│   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│   * OOM Killer terminates process                               │
│   * Kernel handles directly (process cannot catch)              │
└─────────────────────────────────────────────────────────────────┘
```

- tmpfs 레이어: ShmSize 제한 초과 시 SIGBUS 발생 (파일시스템 레벨)
- cgroup 레이어: shm + app 합계가 Memory 초과 시 SIGKILL 발생 (커널 레벨)

**실제 테스트 결과에서의 차이**

| 시나리오 | Memory | ShmSize | shm 할당 | 결과 | 이유 |
|---------|--------|---------|----------|------|------|
| S2-1 | 4g | 512m | 600MB | SIGBUS (135) | tmpfs limit(512m) 초과 |
| S7-1 | 1g | 2g | 1200MB | SIGKILL (137) | cgroup limit(1g) 초과 |
| S4-2 | 2g | 1g | shm 800 + app 1300 | SIGKILL (137) | 합계 2.1GB > cgroup 2g |

**핵심 차이 요약**

- **SIGBUS**: tmpfs 자체의 크기 제한에 걸림 (파일시스템 레벨 오류)
- **SIGKILL**: cgroup memory limit에 걸림 (커널 메모리 관리 레벨 강제 종료)

둘 다 "메모리 부족"으로 인한 종료이지만, 체크하는 제한 값이 다릅니다:
- SIGBUS: ShmSize만 체크
- SIGKILL: Memory cgroup limit (shm + app 합계) 체크

---

## 테스트 환경

- **Docker Runtime**: OrbStack (macOS), Docker Desktop, Native Linux Docker
- **Kernel**: Linux 6.x (cgroup v2)
- **Container Image**: python:3.11-slim
- **Memory Test**: `multiprocessing.shared_memory` + `bytearray`

---

## 참고 자료

### 공식 문서
- [Docker Resource Constraints](https://docs.docker.com/engine/containers/resource_constraints/)
- [Docker Runtime Metrics](https://docs.docker.com/engine/containers/runmetrics/)
- [Linux Kernel cgroup v2](https://docs.kernel.org/admin-guide/cgroup-v2.html)
- [Linux Kernel cgroup v1 Memory](https://docs.kernel.org/admin-guide/cgroup-v1/memory.html)

### 기술 블로그
- [Understanding Docker Shared Memory](https://blog.mikihands.com/en/whitedec/2025/11/5/docker-shm-size-ipc/)
- [LinkedIn - cgroups memory accounting](https://www.linkedin.com/blog/engineering/data-streaming-processing/overcoming-challenges-with-linux-cgroups-memory-accounting)
- [How to Configure Docker's /dev/shm](https://last9.io/blog/how-to-configure-dockers-shared-memory-size-dev-shm/)
