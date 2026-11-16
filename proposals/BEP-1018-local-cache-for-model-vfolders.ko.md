# 모델 vfolder 의 로컬 cache

## 동기

Backend.AI 에서 model deployment 는 "vfolders" 로 마운트한 원격 filesystem 에서 모델 파라미터(checkpoint)와 실행 설정을 읽는다.
이 방식은 모델 vfolder 를 정리하고 RBAC 를 한곳에 모으는 데 편리하지만, 여러 container 가 동시에 모델을 읽을 때 대용량 I/O 로 불안정의 원인이 될 수 있다.
또한 production 에서 여러 network/filesystem 문제로 인한 _mountpoint loss_ 이슈를 많이 관찰했다.

배포는 고객 매출에 직접 영향을 주므로 매우 안정적이어야 한다.
이런 의미에서 @inureyes 는 배포에 사용하는 모델 vfolder 의 로컬 cache 를 두자고 제안했다.


## 가능한 설계

* **명시적 파일 복사**: Backend.AI agent 가 container 시작 시 모델 vfolder 내용을 복사하게 한다.

  - 모델 서비스 시작에 명시적인 지연이 생긴다. 배포를 "healthy" 로 표시하기 전에 진행률 추적 같은 기능을 추가해야 할 수 있다.

* **Caching FUSE**: [catfs](https://github.com/kahing/catfs/) 나 [mcachefs](https://github.com/Doloops/mcachefs) 같은 fuse filesystem 을 넣어 파일을 처음 읽을 때 대상 파일을 로컬 디렉터리로 투명하게 복사한다.

  - 이런 "caching" fuse 구현이 여럿 있으므로 성능과 안정성 면에서 어느 것이 더 나은지 조사해야 한다.

  - 구현은 더 단순하지만 APC 팀의 배포 절차와 설치 도구를 갱신해야 한다.


## 관련 작업

현재 NVIDIA DGX OS 의 [`cachefilesd` 설정](https://docs.nvidia.com/dgx/dgx-os-6-user-guide/installing_on_ubuntu.html#configuring-data-drives)을 따라 [`fsc`](https://docs.kernel.org/filesystems/caching/fscache.html) 에 _권장_ 설정을 두고 있다.
`cachefilesd` 는 kernel 수준 `fsc` 계층과 상호작용하는 사용자 수준 service 다.

다만 NFS mount 같은 원격 filesystem 에서만 동작하고 `s3fs` 같은 FUSE 기반 filesystem 의 caching 에는 사용할 수 없다.


## 제안 설계

object storage 지원([BA-255](https://lablup.atlassian.net/browse/BA-255) 또는 lablup/backend.ai#665)과 함께 `catfs` 를 사용하는 FUSE 기반 방식을 선호한다.

### 확인할 항목

- container 를 시작할 때 `open()` 을 시도해 모든 파일을 미리 읽는 방식과 요청 시 읽는 방식에 대한 결정이 필요하다

- `catfs` 가 unmount 시 cache data 정리를 보장하는지 확인이 필요하다

### 배포 시 고려할 항목 (cc: APC 팀)

- `catfs` 는 cache volume 의 여유 공간을 백분율로 유지하는 설정이 있다. 공간 한도에 도달하면 `catfs` 가 일부 파일을 축출할 수 있다.
  축출 가능성 때문에 모든 모델 vfolder mount 가 항상 전부 cache 에 저장된다고 보장하지 않는다.

### 기존 vfolder subsystem 에 미치는 영향

- 기본으로 배포 container 의 주요 모델 vfolder 에만 mount caching 을 활성화해야 한다.

- 사용자별 vfolder 접근 기록 속성을 추가해 로컬 caching 적용 여부를 제어할 수 있다(비 POSIX I/O 동작에 대한 경고와 설명 포함).
