# Storage Proxy: 배경

> 규칙은 같은 디렉터리의 `AGENTS.md` 에 있다.

## 이 컴포넌트가 존재하는 이유

Backend.AI 와 실제 filesystem, object storage 사이의 stateless data plane 이다. file upload, download, streaming 과 vfolder/quota 수명 주기를 처리하고, 벤더별 구현을 하나의 volume interface 뒤에 둔다.

## API 둘, 신뢰 모델 둘

- 신뢰할 수 없는 network 에 있는 storage proxy client API 는 스스로 인증하지 않는다. 모든 요청이 **manager 가 발급한** 수명이 짧은 JWT 를 가지며, payload 에 volume/vfolder/path/size 가 들어 있다.
- authorization 은 발급 시점에 이미 결정되었고, proxy 는 signature 만 검증한다.
- 신뢰할 수 있는 network 에 있는 storage proxy manager API 는 shared secret header 를 사용한다.
- 그러므로 client endpoint 를 추가한다는 것은 permission 검사를 추가하는 일이 아니라 **token type 과 manager 쪽 issuer 를 추가하는 일**이다.

## 구조상 stateless 다

- relational DB 가 없다. 지속 metadata 는 manager 의 DB 에 있고, proxy 는 etcd(configuration)와 Valkey(events, background tasks, TUS offsets, volume statistics)만 사용한다.
- TUS offset 을 Valkey lease 로 관리하는 것은 proxy replica 여럿이 같은 upload session 을 처리할 수 있게 하기 위해서다.
- table 을 추가하지 않는다. 지속 상태는 manager 에 속한다.

## quota 단위는 folder 가 아니라 quota scope 다

- quota 단위는 quota scope(`(type, uuid)`, user 또는 project)이고, vfolder path 는 그 scope 아래에서 파생된다.
- quota 지원은 보장이 아니라 **backend 별 capability**(`CAP_QUOTA`)다. code 는 분기하고 그 부재를 허용해야 한다.

## 벤더별 구현은 volume interface 뒤에 있다

- 모든 벤더는 `AbstractVolume` + `AbstractQuotaModel` + `AbstractFSOpModel` 뒤에 있다.
- backend 는 host 상태를 변경할 수 있다. XFS 는 sudo 로 `/etc/projects` 를 수정한다.
- proxy 자체에서 root 가 필요한 연산은 opt-in watcher subprocess(ZeroMQ IPC, task object)를 거친다. handler 안에서 sudo 를 직접 실행하지 않는다.

## 시작은 하나로 조립된 의존성 그래프다

- `StorageDependencyComposer` 가 모든 시작 resource 를 가지고, server, `dependencies verify`, `health check` 가 모두 이를 구동한다. 한 경로에서 직접 조립한 resource 는 다른 경로에서 보이지 않는다.
- plugin context 는 한 번 조립해 주입한다. volume registry 는 plugin group 을 스스로 load 하지 않고 필요한 backend class 를 받는다.
- `RootContext` 는 조립된 resource 로 `server.py` 에서 조립된다. stage 가 아니라 값을 전달하는 객체다.

## volume registry 는 `VolumePool` 하나다

- 설정된 모든 volume 은 `VolumePool.create()` 가 한 번 생성하고 `init()` 하며, noop volume 도 여기서 등록한다. volume 은 `[volume.<name>]` configuration key 로 찾는다. request 경로에서 volume 을 생성하는 곳은 없다.
- configuration key 는 system 전체에서 유일한 volume 이름(`StorageVolumeName`)이고, `get_volume_by_name()` 이 그 key 로 volume 을 조회한다. `get_volume(VolumeID)` 는 deprecate 된 `VolumeService` 에만 남아 있다.
- 초기화가 eager 이므로 mount 가 깨진 volume 은 첫 request 에서 실패하는 대신 전체 시작을 실패시킨다.
