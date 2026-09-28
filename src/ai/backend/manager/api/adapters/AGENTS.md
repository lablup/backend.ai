# 어댑터 — 가드레일

배경은 이 디렉터리의 `KNOWLEDGE.md`에 있다.

## 엔티티마다 시나리오를 적는다

- 엔티티 패키지마다 `KNOWLEDGE.md`가 있다. 그 엔티티의 어댑터가 무엇을 보장하는지 시나리오로
  적는다. 코드보다 먼저 적는다.
- `TODO`만 있는 파일은 아직 아무도 적지 않았다는 뜻이다. 그 엔티티에는 시나리오 테스트가 없다.
- `adapter.py`가 내놓는 호출을 전부 훑고, 호출마다 시나리오를 적는다. 적을 수 없는 호출이
  있으면 그 이유를 "아직 적지 않은 것"에 남긴다.
- 한 시나리오는 네 부분이다. 무엇을 보장하는지 한 문장, 요청 시점에 이미 참인 것,
  누가 무엇을 부르는지, 그리고 답 또는 거부.
- 한글로 먼저 적고, 리뷰를 통과한 뒤 영문으로 옮긴다.
- 식별자를 적지 않는다. 필드명, 예외 클래스, 파일 경로는 시나리오의 말이 아니다.
- 권한이 있는 경우와 없는 경우를 짝으로 적는다. 한쪽만 적으면 권한을 과하게 줬는지 알 수
  없다.

## 연산 이름

- adapter 연산, processor 필드, service 메서드는 같은 이름을 쓴다.

  | 대상 | 이름 |
  |---|---|
  | id 여럿 읽기 | `bulk_get_ids` |
  | 자연 키 여럿 읽기 | `bulk_lookup_names`. 자연 키가 이름이 아니면 `bulk_lookup_<키>` |
  | 자연 키 하나로 id 찾기 | `lookup_name`. 엔티티마다 자기 adapter가 내놓는다 |
  | 전역 검색 | `global_search` |
  | 스코프 검색 | `scoped_search` |
  | 쓰기 | `create` / `update` / `delete` / `restore` / `purge` |

- `admin_`을 붙이지 않는다.
- adapter 연산, processor 필드, Action 이름에 `node`를 넣지 않는다.
- DTO 이름, REST 경로와 핸들러 이름, GQL 필드 이름은 이 규칙으로 바꾸지 않는다.

## 자기 엔티티의 processor만 받는다

- adapter는 자기 엔티티의 processor만 받는다.
- 자기 엔티티의 이름은 DTO가 이름을 싣는 연산 안에서 푼다.
- 다른 엔티티의 이름은 adapter가 풀지 않는다. REST handler와 GQL resolver가 그 엔티티
  adapter의 `lookup_name`을 먼저 부르고 id를 넘긴다.

## adapter는 current_user()를 읽지 않는다

- adapter는 `current_user()`를 읽지 않는다. scope를 입력으로 받는 연산(`scoped_search` 등)만
  제공한다.
- `my_*` 연산을 adapter에 두지 않는다.
- 본인 대상 조회는 REST handler와 GQL resolver가 `current_user()`의 user id를 scope 값으로 넣어
  adapter의 scoped 연산을 부른다.
- 권한 판단은 validator가 요청 문맥의 `current_user()`로 한다. 권한 판단용 `UserInfo`를 adapter
  인자로 넘기지 않는다.

## 응답 노드는 행의 식별자를 싣는다

- `EntityData`에서 만든 응답 노드는 `entity_id`, `FieldData`에서 만든 노드는 `field_id`를 싣는다.
  타입은 `UUID`, 값은 데이터 클래스에서 그대로 실어 온다. `id`를 다시 파싱하지 않는다.
- 새 식별자 필드 이름에 `uuid`를 쓰지 않는다.
- 행 자체의 id가 없는 데이터 클래스는 이 규칙에서 빠진다. 빠지는 목록은 스윕 테스트가 들고 있다.

## 시나리오와 테스트를 맞춘다

- 시나리오를 적은 뒤 `tests/scenario/`에 그대로 옮긴다. 규칙은 그쪽 `AGENTS.md`에 있다.
- 적어둔 시나리오와 실행 결과가 어긋나면 둘 중 하나가 틀린 것이다. 문장이 의도이고 표가
  구현이므로, 문장을 먼저 의심한다.

## 실행 결과는 `report.md`에 둔다

- 엔티티 패키지의 `report.md`는 실행이 낸 것이다. 손으로 문장을 짓지 않는다. `KNOWLEDGE.md`와
  섞지도 않는다. 한쪽은 의도이고 한쪽은 실행 결과다.
- 시나리오를 옮긴 뒤 실행하고 뽑는다.

  ```bash
  BACKEND_SCENARIO_LOG=dist/scenarios.jsonl pants test tests/scenario::
  python scripts/scenario-report.py dist/scenarios.jsonl --split src/ai/backend/manager/api/adapters
  ```

- `report.md`가 실행과 어긋나면 알린다. 조용히 덮어쓰지 않는다.

  ```bash
  python scripts/scenario-report.py dist/scenarios.jsonl --verify src/ai/backend/manager/api/adapters
  ```

- 어긋났다는 말을 보면 무엇이 달라졌는지 먼저 읽는다. 시나리오를 고친 결과면 뽑아서 맞추고,
  고친 적이 없는데 달라졌으면 동작이 바뀐 것이다.
- 어느 시나리오도 부르지 않은 어댑터 호출은 `report.md`가 함께 적는다. 그 목록을 지우지 않는다.
