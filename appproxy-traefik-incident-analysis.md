# App Proxy Traefik 장애 분석

## 장애 보고용 요약

- 관측된 증상은 “모델 A 엔드포인트 요청에 모델 A/B 응답이 섞여 반환되고, `라우트 동기화` 후 즉시 정상화”였습니다.
- 이 증상은 애플리케이션 내부 추론 오류보다는, App Proxy Traefik 제어 평면의 stale 라우팅 상태로 설명하는 것이 가장 자연스럽습니다.
- 원인 축은 하나가 아니라 세 가지였습니다.
  - 같은 circuit에 대한 route propagation race
  - 같은 slot을 공유하는 서로 다른 circuit 간 race
  - etcd partial-write / stale metadata 잔존
- `BA-5499`는 같은 circuit update race를 줄였고, `2394e909c`는 같은 slot race를 줄였습니다.
- 이번 추가 수정은 `delete_prefixes()`와 `replace_prefix()`를 도입해 etcd partial-write 문제를 직접 해결하고, unload 실패 시 예외를 다시 올려 DB/etcd 불일치를 막는 방향입니다.
- 현재 수정으로 대표적인 실전 버그는 상당 부분 해결되지만, distributed multi-coordinator 환경, crash ordering, reconcile 전 stale 상태 같은 잔여 리스크는 남아 있습니다.
- 따라서 현재 수정은 “운영에서 실제 터졌던 핵심 버그를 해결하는 단계”로는 충분히 의미가 크지만, 장기적으로는 DB 정본 + reconcile/outbox 중심 구조가 더 강한 해법입니다.

## 개요

이 문서는 이번 조사에서 정리된 App Proxy Traefik 모드의 장애 유형을 정리한 문서입니다.

- 관측된 증상
- 가능한 원인
- 실제로 발생 가능한 케이스
- 취약했던 코드 경로
- 최근 수정으로 해결된 부분
- 아직 남아 있는 한계
- 추가된 테스트가 무엇을 검증하는지

주요 관심사는 다음과 같습니다.

- 사용자가 의도한 모델이 아닌 다른 모델의 응답을 받는 문제
- coordinator DB 상태와 Traefik이 참조하는 etcd 상태가 어긋나는 문제

## 관측된 증상

보고된 운영 장애의 증상은 다음과 같습니다.

- 모델 A의 엔드포인트로 요청했는데 모델 A와 모델 B 응답이 섞여 반환됨
- 서비스 로그에는 뚜렷한 에러 없이 정상 `200` 응답이 번갈아 보임
- WebUI의 `라우트 동기화`를 실행하면 즉시 정상화됨

이 증상은 애플리케이션 내부 추론 실패보다는, 제어 평면의 라우팅 상태가 잘못되어 있었을 가능성을 강하게 시사합니다.

## 구조 배경

Traefik 모드에서는 Backend.AI Python 코드가 요청을 직접 프록시하지 않습니다.

트래픽 흐름은 다음과 같습니다.

```text
사용자 요청
    |
    v
Traefik
    |
    | etcd에 기록된 router / service 설정을 읽음
    v
커널 host:port
```

즉:

- coordinator DB는 내부 정본입니다.
- etcd는 Traefik이 직접 보는 실시간 반영본입니다.
- DB와 etcd가 어긋나면 Traefik은 stale 상태를 기준으로 계속 라우팅할 수 있습니다.

## 라우트 업데이트 흐름

Traefik route update 흐름은 아래와 같습니다.

```text
Manager / WebUI
    |
    | 1. 라우트 동기화 또는 내부 route update 트리거
    v
Manager Registry
    |
    | 2. DB에서 endpoint 조회
    | 3. 최신 route_connection_info 생성
    | 4. redis_live에 최신 route 스냅샷 기록
    | 5. EndpointRouteListUpdatedEvent(endpoint_id) 발행
    v
Event Bus
    |
    v
App Proxy Coordinator
    |
    | 6. EndpointRouteListUpdatedEvent 수신
    | 7. redis_live에서 최신 route 정보 조회
    | 8. coordinator DB에서 endpoint + circuit 조회
    | 9. circuit.route_info 갱신
    | 10. DB commit
    | 11. Traefik 반영 호출
    v
CircuitManager.update_circuit_routes()
    |
    | 12. slot/circuit lock 획득
    v
update_traefik_circuit_routes()
    |
    | 13. etcd prefix 계산
    | 14. 새 service 설정 생성
    | 15. etcd에 service subtree 교체
    v
etcd
    |
    | 16. Traefik이 etcd 변경 감시
    v
Traefik
    |
    | 17. 메모리의 router / service backend 갱신
    v
커널 host:port
```

문제는 과거 구현에서 15번이 하나의 원자적 작업이 아니었다는 점입니다.

## 장애 유형 구분

이번에 다룬 문제는 하나가 아니라 서로 다른 세 부류입니다. 서로 섞어 보면 안 됩니다.

### 1. 같은 circuit에 대한 Traefik route propagation race

이 문제는 `BA-5499`가 겨냥한 버그입니다.

과거에는:

- 같은 circuit에 대해 `update_circuit_routes()`가 동시에 호출될 수 있었고
- Traefik etcd 쓰기가 여러 async 단계로 나뉘어 있었기 때문에
- 늦게 끝난 stale update가 최신 상태를 덮어쓸 수 있었습니다.

영향:

- circuit의 backend route 목록이 잘못 남음
- stale backend가 살아남음
- DB의 최신 상태와 Traefik이 보는 상태가 어긋남

### 2. 같은 slot을 공유하는 서로 다른 circuit 간 race

이 문제는 `2394e909c`가 해결하려 한 버그입니다.

과거에는:

- lock이 `circuit.id` 기준이었고
- `worker + port/subdomain`이 같은 서로 다른 circuit 간에는 직렬화가 되지 않았습니다.

그래서 같은 slot에서:

- circuit A를 unload하는 작업
- circuit B를 create / register하는 작업

이 동시에 들어오면 서로 섞일 수 있었습니다.

영향:

- 같은 frontend slot에 대해 Traefik router가 두 개 동시에 노출될 수 있음
- worker 메모리에서는 `circuit_B`와 `backend_A`가 잘못 짝지어질 수 있음
- 모델 A 요청이 실제로는 모델 B backend로 갈 수 있음

### 3. etcd partial-write / stale metadata 불일치

이 문제는 위의 두 race와는 별개입니다.

과거에는:

- Traefik 설정 삭제가 여러 번의 `delete_prefix()` 호출로 분리되어 있었고
- route update가 `delete_prefix()` 후 `put_prefix()`로 분리되어 있었고
- `unload_circuits()`는 예외를 잡고 삼켰습니다.

영향:

- DB에서는 circuit이 삭제됐는데 etcd엔 stale router / service key가 남을 수 있음
- stale metadata가 다음 reconcile 또는 수동 sync 전까지 유지될 수 있음
- 어떤 키가 남았는지에 따라 증상이 달라짐
  - cross-routing
  - stale service 참조
  - empty backend로 인한 503

## 증상과 원인 연결

### A/B가 번갈아 `200` 응답을 주는 경우

이 증상은 아래 둘 중 하나로 설명하는 것이 자연스럽습니다.

1. 같은 slot race로 인해 router 또는 worker slot 상태가 꼬인 경우
2. stale router metadata가 etcd에 남아 있고, 그 router가 가리키던 host:port가 나중에 다른 endpoint의 kernel로 재사용된 경우

이 증상은 단순히 `delete old service -> put new service` 실패만으로는 잘 설명되지 않습니다.
그 경로는 대체로 503이나 empty backend 증상으로 이어집니다.

### 503 / backend 없음

이 증상은 보통 다음 흐름과 더 잘 맞습니다.

- 기존 service subtree 삭제 성공
- 새 service subtree 쓰기 실패
- router는 남아 있지만 service backend 목록이 비거나 깨짐

## 취약했던 코드 경로

### Route update

현재 수정된 경로:

- [src/ai/backend/appproxy/coordinator/types.py](/Users/daemyung/develop/lablup/backend.ai/src/ai/backend/appproxy/coordinator/types.py:204)

과거 취약 경로:

```text
update_traefik_circuit_routes()
    delete_prefix(service subtree)
    put_prefix(new service subtree)
```

위험:

- delete는 성공
- put은 실패
- Traefik에 empty service 또는 missing service가 보임

### Circuit unload

현재 수정된 경로:

- [src/ai/backend/appproxy/coordinator/types.py](/Users/daemyung/develop/lablup/backend.ai/src/ai/backend/appproxy/coordinator/types.py:249)
- [src/ai/backend/appproxy/coordinator/types.py](/Users/daemyung/develop/lablup/backend.ai/src/ai/backend/appproxy/coordinator/types.py:293)

과거 취약 경로:

```text
unload_traefik_circuit()
    delete router prefix
    delete service prefix
    delete middleware prefix
    delete middleware_go prefix

unload_circuits()
    Exception catch
    로그만 남김
    정상 반환
```

위험:

- 일부 prefix만 지워짐
- 일부 prefix는 살아남음
- 호출자는 성공처럼 인식
- DB transaction은 commit
- DB와 etcd가 불일치

### Delete API 경로

- [src/ai/backend/appproxy/coordinator/api/circuit_v2.py](/Users/daemyung/develop/lablup/backend.ai/src/ai/backend/appproxy/coordinator/api/circuit_v2.py:67)

중요한 점:

- DB row 삭제와 unload는 하나의 논리 작업입니다.
- unload 실패를 swallow하면 DB 삭제만 commit될 수 있습니다.

## 최근 수정이 해결한 것

### 수정 1: `BA-5499`

의도:

- 같은 circuit에 대한 Traefik route propagation race 완화

효과:

- 같은 circuit에 대한 중복 update가 서로 섞이는 문제를 줄임

한계:

- 같은 slot을 공유하는 다른 circuit 간 race는 완전히 막지 못함
- etcd 다중 delete / replace의 원자성 문제는 해결하지 못함

### 수정 2: `2394e909c`

의도:

- register / unload / update를 `circuit.id`가 아니라 slot 기준으로 직렬화
- worker 메모리에서 slot 상태가 일관되게 보이도록 보강

효과:

- 같은 slot에서 create(B)와 unload(A)가 섞이지 않음
- worker가 `circuit_B + backend_A`를 노출하지 않음
- Traefik publish와 unload가 같은 slot에서 교차하지 않음

한계:

- etcd delete / replace 자체를 원자적으로 만들지는 못함
- unload 예외 swallow 문제를 직접 고치지는 못함

### 수정 3: atomic etcd subtree 연산 + unload retry / re-raise

현재 워크트리에는 다음 변경이 들어 있습니다.

- `TraefikEtcd.delete_prefixes()`
- `TraefikEtcd.replace_prefix()`
- unload retry 후 최종 실패 시 re-raise

관련 파일:

- [src/ai/backend/appproxy/common/etcd.py](/Users/daemyung/develop/lablup/backend.ai/src/ai/backend/appproxy/common/etcd.py:1)
- [src/ai/backend/appproxy/coordinator/types.py](/Users/daemyung/develop/lablup/backend.ai/src/ai/backend/appproxy/coordinator/types.py:204)

효과:

- unload 시 router / service / middleware 삭제가 하나의 etcd txn으로 처리됨
- route update 시 외부에 보이는 `delete -> empty -> put` 창이 사라짐
- 일시적 오류는 재시도
- 재시도 후에도 실패하면 예외를 다시 던져 DB transaction이 rollback되도록 함

이 변경은 stale-key / partial-write 문제를 직접 해결합니다.

## 수정 전후 비교

### 수정 전

```text
Unload:
    delete router
    delete service
    delete middleware
    delete middleware_go
    중간 실패 가능
    예외 swallow 가능
    DB는 commit될 수 있음

Update:
    delete service subtree
    put service subtree
    put 실패 시 empty service 노출 가능
```

### 수정 후

```text
Unload:
    필요한 prefix들을 하나의 etcd txn으로 atomic delete
    transient error는 retry
    최종 실패 시 raise
    DB commit 차단

Update:
    service subtree를 하나의 etcd txn으로 atomic replace
    외부에 노출되는 empty-service 창 제거
```

## 장애 시나리오 다이어그램

### 과거 stale-key 불일치

```text
DB transaction
    |
    | circuit row 삭제
    | unload_circuits() 호출
    v
unload_traefik_circuit()
    |
    | delete router prefix      OK
    | delete service prefix     FAIL
    v
unload_circuits()
    |
    | 예외 catch
    | 로그만 남김
    | 정상 반환
    v
DB commit

결과:
    DB: circuit 삭제됨
    etcd: stale service / router 일부 잔존 가능
```

### 과거 update 중 empty-service 창

```text
update_traefik_circuit_routes()
    |
    | delete old bai_service_{id}   OK
    | put new bai_service_{id}      FAIL
    v
Traefik은 router는 보지만 backend가 비어있는 service를 참조
```

### 같은 slot race

```text
Circuit A가 slot 10640 사용 중
Circuit B가 slot 10640 재사용

create(B) --------------------+
                              | interleave
unload(A) --------------------+

수정 전 가능한 결과:
    - 같은 slot에 매칭되는 router 두 개 노출
    - worker 메모리에서 circuit_B + backend_A 조합
    - 잘못된 모델 응답
```

## 왜 라우트 동기화로 해결되었는가

`라우트 동기화`가 효과 있었던 이유는 소스와 잘 맞습니다.

manager 쪽 force sync는:

- DB 기준 최신 route 상태를 다시 계산하고
- app proxy에 그 상태를 다시 밀어 넣습니다.

coordinator 쪽 reconcile은:

- DB에 존재하는 circuit 기준으로 Traefik service 상태를 다시 맞추고
- etcd에 남아 있는 orphan stale key를 제거합니다.

즉 장애 원인이 stale metadata 또는 stale route state였다면, route sync로 즉시 회복되는 것이 자연스럽습니다.

## 남아 있는 한계

이번 수정으로 많이 좋아졌지만, 이론적으로 남는 edge case는 있습니다.

### 1. enumerate 후 delete txn 사이의 창

`delete_prefixes()`는:

- 먼저 prefix 아래 실제 key들을 열거하고
- 그 key 집합을 하나의 txn으로 삭제합니다.

즉:

- 열거 이후 txn commit 전 사이에 새 key가 들어오면 이번 삭제 대상에는 포함되지 않습니다.

완화 요소:

- 같은 slot에 대한 정상 경로는 slot lock으로 직렬화됨

남는 우려:

- 분산 multi-coordinator 환경에서는 더 강한 보장이 필요함

### 2. DB와 etcd 사이의 crash ordering

etcd 연산이 더 좋아졌더라도, 프로세스가 DB와 etcd 반영 사이에서 죽으면 여전히:

- DB가 더 최신일 수도 있고
- etcd가 더 최신일 수도 있습니다.

복구는 다음에 의존합니다.

- reconcile loop
- route sync
- retry 가능한 control-plane 설계

### 3. 분산 coordinator 환경

여러 coordinator 인스턴스가 같은 slot / keyspace를 동시에 만질 수 있다면, 프로세스 내부 `asyncio.Lock`만으로는 충분하지 않습니다.

필요한 것:

- 실제 distributed slot lock
- 또는 outbox / reconcile 중심 구조

## 현재 해결책으로도 완전히 해결되지 않는 상황

현재 수정은 다음 문제를 직접 해결합니다.

- 같은 slot / circuit에서의 in-process race
- route update 시 `delete -> put` 사이의 empty service 노출
- unload 중 partial delete 후 예외 swallow로 인한 대표적인 DB/etcd 불일치

하지만 아래 상황은 여전히 완전히 닫히지 않았습니다.

### 1. multi-coordinator 동시 갱신

현재 slot lock은 프로세스 내부 lock입니다.

따라서 아래 조건이면 여전히 경합이 가능합니다.

- coordinator 인스턴스가 여러 개 떠 있음
- 같은 worker / slot 또는 같은 circuit subtree를 서로 다른 프로세스가 동시에 갱신함

이 경우 현재 수정만으로는 보장되지 않습니다.

- 한 프로세스가 enumerate한 key 집합
- 다른 프로세스가 그 직후 새로 넣은 key

가 서로 엇갈릴 수 있습니다.

즉, 현재 수정은 **single-process coordinator 기준**으로는 강하지만, **distributed coordinator 기준**으로는 추가 보장이 필요합니다.

### 2. enumerate 후 txn commit 전 새 key 유입

`delete_prefixes()`는 구현상 다음 순서입니다.

1. prefix 아래 현재 key들을 열거
2. 그 key 집합을 하나의 txn으로 삭제

이 방식은 “열거된 key 집합”에 대해서는 atomic하지만, “prefix 전체 공간”에 대해 완전한 range-delete atomicity를 제공하는 것은 아닙니다.

따라서 아래 상황은 여전히 가능합니다.

- key enumeration 완료
- 그 직후 다른 writer가 같은 prefix 아래 새 key 생성
- txn commit
- 방금 생성된 key는 삭제 대상에 포함되지 않음

다만 이 점은 **현재 구조에서는 우선순위가 낮은 이론적 리스크**에 가깝습니다.

이유는 다음과 같습니다.

- 정상 경로에서는 같은 slot / circuit 작업이 lock으로 직렬화됨
- coordinator가 사실상 해당 keyspace의 유일한 writer라는 가정이 강함
- `replace_prefix()`는 delete action과 put action을 같은 txn에 담아 외부에 중간 상태를 노출하지 않음

즉, single-coordinator + coordinator-only-writer 가정이 유지되는 한 이 문제는 쉽게 드러나지 않습니다.

이 리스크가 현실적인 문제가 되는 경우는 주로 다음과 같습니다.

- multi-coordinator
- coordinator 외부 writer 존재
- lock 범위 밖의 다른 경로가 같은 prefix를 수정

따라서 현재 수정 이후 기준으로는, 이 항목은 “남아 있는 가능성”으로 기록할 가치는 있지만, 운영상 가장 먼저 의심해야 하는 주원인 축은 아닙니다.

### 3. DB commit / etcd 반영 사이 프로세스 크래시

현재 수정은 etcd 연산 실패를 DB rollback으로 연결하는 방향입니다. 하지만 아래 순서의 crash는 별개입니다.

- DB 변경은 commit됨
- etcd 반영 전에 프로세스가 죽음

또는 반대로:

- etcd는 반영됨
- DB commit 전에 프로세스가 죽음

이 경우 현재 수정만으로는 “DB와 etcd가 항상 즉시 일치한다”는 강한 보장을 주지 못합니다. 복구는 다음 메커니즘에 의존합니다.

- 주기적 reconcile
- 수동/자동 route sync
- 재시도 가능한 control-plane 설계

즉, 현재 수정은 불일치 가능성을 크게 줄이지만, **크래시 복구까지 포함한 완전한 원자성**을 제공하는 것은 아닙니다.

### 4. reconcile 실행 전까지 남는 일시적 불일치

현재 수정으로도 다음 상황은 남습니다.

- 이전 장애나 외부 요인으로 이미 stale key가 남아 있음
- 이번 수정 이후에는 새 stale을 덜 만들더라도, 기존 stale은 즉시 사라지지 않음

따라서 시스템은 여전히 다음에 의존합니다.

- `라우트 동기화`
- coordinator reconcile loop

즉, “이 수정이 들어가면 기존에 남아 있던 잘못된 etcd 상태가 즉시 정정된다”는 의미는 아닙니다. 새로 깨질 가능성을 줄이는 것이고, 이미 깨진 상태를 정리하는 것은 별도 경로입니다.

### 5. Traefik watch / apply 지연

etcd 반영이 atomic해도 Traefik은 watcher를 통해 상태를 반영합니다.

따라서 매우 짧은 시간 동안은:

- etcd의 최신 상태
- Traefik 내부 메모리 상태

가 완전히 같지 않을 수 있습니다. 이것은 partial-write bug와는 다르지만, “수정 직후에도 짧은 전환창이 왜 남느냐”를 설명하는 operational limitation입니다.

보통은 짧고 self-healing이지만, 고부하나 watch 지연이 있으면 관측될 수 있습니다.

### 6. 외부에서 etcd를 직접 만지는 경우

현재 설계는 coordinator가 Traefik 관련 keyspace의 유일한 writer라는 가정이 강합니다.

만약 아래가 있으면 현재 수정의 가정이 깨집니다.

- 운영 스크립트
- 수동 etcd 조작
- 다른 control-plane 컴포넌트

이 경우 atomic helper를 써도 외부 writer와의 경쟁은 막을 수 없습니다.

## 의미 정리

현재 해결책의 의미는 다음과 같습니다.

- 기존의 대표적인 in-process race와 partial-write 문제는 실질적으로 크게 줄였다
- 하지만 완전한 의미의 “DB와 etcd 사이 전역 원자성” 또는 “분산 환경까지 포함한 절대적 직렬화”는 아직 제공하지 않는다

즉, 현재 수정은 **중요한 실전 버그를 해결하는 단계**로는 충분히 가치가 크지만, **최종 형태의 아키텍처적 해법**은 아닙니다.

## 현재 시점에서 더 우선적으로 보는 잔여 리스크

현재 수정 이후 기준으로, 우선순위를 매기면 잔여 리스크는 대략 다음 순서로 보는 것이 맞습니다.

1. multi-coordinator 또는 외부 writer가 있는 환경에서의 경쟁
2. DB commit / etcd 반영 사이의 crash ordering
3. reconcile이 돌기 전까지 남아 있는 기존 stale metadata
4. Traefik watch / apply 지연
5. `enumerate -> txn commit` 사이의 새 key 유입 가능성

즉, `enumerate 후 delete` 패턴은 문서상 언급할 필요는 있지만, 현재 수정으로 인한 실제 운영 리스크의 중심이라고 보기는 어렵습니다.

## 추가된 테스트 설명

새 테스트 파일:

- [tests/unit/appproxy/coordinator/test_traefik_stale_keys.py](/Users/daemyung/develop/lablup/backend.ai/tests/unit/appproxy/coordinator/test_traefik_stale_keys.py:1)

이 파일은 stale-key 계열 문제를 직접 검증합니다.

### 테스트 의도

- etcd write 실패를 제어된 방식으로 주입
- unload가 성공적으로 끝나면 etcd가 깨끗해야 함을 보장
- route update replacement가 partially deleted service 상태를 노출하지 않음을 검증

### fake etcd가 하는 일

fake etcd는 다음 메서드에 대해 실패 주입을 지원합니다.

- `put_prefix`
- `delete_prefix`
- `delete_prefixes`
- `replace_prefix`

이를 통해 다음 상황을 결정적으로 재현할 수 있습니다.

- transient delete 실패
- transient replace 실패
- stale key가 남는 조건

### 테스트 클래스 설명

`TestUnloadAbsorbsTransientFailure`

- unload 중 일시적 실패가 발생했을 때 retry가 동작하는지 검증
- unload가 정상 반환했다면 해당 circuit의 etcd key가 모두 사라졌는지 확인

이 테스트군이 보장하려는 핵심은 다음입니다.

- 성공적으로 끝난 unload 이후 stale key가 남지 않아야 함
- 같은 slot republish 이후 과거 stale metadata와 공존하지 않아야 함
- replace 실패 시 empty service 상태가 외부에 노출되지 않아야 함

## 최종 판단

최종적으로 정리하면:

- `BA-5499`는 같은 circuit update race를 줄였습니다.
- `2394e909c`는 같은 slot race를 줄였습니다.
- 현재 워크트리의 atomic etcd subtree 변경은 partial-write와 stale-key 불일치를 직접 해결합니다.

원래 관측된 “모델 A 요청에 모델 A/B가 번갈아 `200` 응답” 증상에 대해서는:

- stale etcd metadata는 충분히 그럴듯한 control-plane 원인입니다.
- same-slot race 역시 충분히 그럴듯한 원인입니다.
- `라우트 동기화`로 복구되었다는 사실은 stale control-plane 상태 가설을 강하게 지지합니다.

현재 워크트리는 이 세 가지 축 모두를 이전보다 훨씬 안전하게 만들지만, 장기적으로 가장 강한 해법은 여전히 다음 방향입니다.

- DB를 유일한 source of truth로 두고
- etcd는 파생 상태로 취급하고
- reconcile / outbox 기반으로 전파하며
- 필요한 경우 distributed slot lock을 추가하는 구조

