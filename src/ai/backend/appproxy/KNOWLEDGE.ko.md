# App Proxy: 배경

> 아직 이곳에 `AGENTS.md` 가 없다. 이 문서가 전제를 담는다.

## 이 컴포넌트가 있는 이유

외부 요청을 커널(세션의 service port)로 전달하는 트래픽 경로다. app 연결과 배포(model serving) 요청의 라우팅을 맡는다.

- **coordinator**: manager 에서 요청을 받아 라우팅 작업(circuit 생성과 종료, worker 배정)을 수행한다.
- **worker**: 실제 트래픽을 받아 커널로 전달한다.
- **traefik mode**: 트래픽 전달을 worker 대신 **Traefik 컴포넌트**가 맡는다. coordinator 가 route 를 발행하고 Traefik 이 읽는다.

## coordinator DB 는 제거 예정이다

- 장기적으로 coordinator 를 stateless 로 전환하고 자체 DB 를 완전히 제거한다.
- 그 일환으로 **worker 도 Traefik 처럼 라우팅 출처를 직접 읽어 트래픽을 전달하도록 전환**하는 작업을 계획한다. push 로 받은 circuit 을 보유하는 대신 출처를 조회한다.
- 그래서 스키마를 키우는 변경은 그 방향에 어긋난다. 아래에서 스키마를 동결하는 근본 이유다.

## 스키마를 동결로 다룬다

- coordinator 는 circuit 과 worker 등록을 manager 와 분리된 자체 DB 에 저장한다.
- migration 은 시작 시 적용하지 않는다. 운영자 수동 작업이며, 운영 환경에서는 아예 실행하지 않을 수 있다.
- 그 결과 오래된 스키마로 부팅하고 조회 시점에 실패할 수 있다. **table, column 추가는 금지**하며 불가피하면 nullable 이거나 default 가 있는 column 만 추가하고 운영자와 배포 일정을 맞춘다.
- native ENUM column 은 전면 금지한다(`StrEnumType` 을 사용한다).

## circuit 은 event bus 로 이동하며, stateful 출처 공유로 옮겨 간다

- 현재: coordinator 는 `SerializableCircuit` 을 담은 broadcast event 로 circuit 갱신을 push 하고, worker 는 자기 authority 로 필터 기반으로 받는다.
- worker 가 반드시 봐야 하는 attribute 는 `SerializableCircuit` 에도 추가해야 한다. 이전 worker 는 이를 조용히 무시하므로 하위 호환성이 필수다.
- 방향: circuit 공유는 **Traefik 과 같은 방식의 stateful 출처 조회**로 변경된다. worker 는 push 된 circuit 을 보유하는 대신 출처에서 라우팅 상태를 읽는다(위의 DB 제거와 같은 작업 흐름이다).

## worker 는 stateless 다

- 식별자는 설정된 `authority` 문자열이다. 부팅 때 다시 등록하고 circuit 을 다시 가져오며, 종료할 때 등록 해제한다.
- 생존 여부는 probe 가 아니라 worker→coordinator ping 으로 확인한다.
- worker 안의 어떤 것도 재시작 후 남지 않는다. 설계된 동작이다.

## 하나의 공유 secret, 호출자 구분 없음

- manager→coordinator 와 worker→coordinator 는 같은 API secret 으로 인증한다. 선언된 auth scope 는 metadata 일 뿐이다.
- 버전이 다른 manager 가 같은 coordinator 와 통신하므로 v1, v2 API module 쌍이 공존한다. 둘 다 유지한다.

## coordinator 복제본

- 여러 복제본을 전제한다. singleton 작업(port 수집, Traefik route 조정)은 DB advisory lock 아래에서 실행한다.
