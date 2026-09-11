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
