---
name: huggingface-registry-adapter-scenarios
type: reference
description: what the huggingface registry adapter guarantees for update, purge and their partial bulk forms, as scenarios; the tests in tests/scenario/bai_scenario/manager/huggingface_registry match these one for one
scope: src/ai/backend/manager/api/adapters/huggingface_registry
keywords: [huggingface registry, artifact registry, scenario, adapter, rbac, partial bulk, purge]
generated:
  by: claude-code/opus-5
  at: 2026-10-16
status: draft
---
# HuggingFace 레지스트리 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다. 여기 적힌 것과 실행 결과가 어긋나면 문장을 먼저
의심한다.

레지스트리는 global 스코프에 만들어진다. 레지스트리 하나는 연결 설정을 싣는 행과 이름을 싣는
행, 두 행이고 한 연산으로 함께 쓰이고 함께 지워진다. 개별 레지스트리를 고치고 지우는 문은 권한
그래프가 지킨다. 권한을 받은 사용자는 global 에 앉은 역할로 아티팩트 레지스트리 권한을 받는다.

## 수정하기

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 수정 권한을 받은 사용자가 주소를 바꾼다 | 레지스트리 하나, 수정 권한을 받은 사용자 | 주소 수정 | 그 레지스트리가 새 주소로, 이름과 토큰은 그대로 |
| 아무 권한도 받지 않은 사용자가 주소를 바꾼다 | 같은 레지스트리 | 주소 수정 | 권한 부족으로 거부 |

## purge

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| purge 권한을 받은 사용자가 purge 한다 | 레지스트리 하나, purge 권한을 받은 사용자 | purge | purge 한 레지스트리의 id |
| 아무 권한도 받지 않은 사용자가 purge 한다 | 같은 레지스트리 | purge | 권한 부족으로 거부 |

단건 purge 와 여럿 purge 모두 purge 권한을 본다.

## 여럿 수정하기

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 수정 권한을 받은 사용자가 여럿의 주소를 한 번에 바꾼다 | 레지스트리 둘, 수정 권한을 받은 사용자 | 둘의 주소 수정 | 둘 다 새 주소로 오고 실패한 것은 없음 |
| 아무 권한도 받지 않은 사용자가 여럿을 수정한다 | 같은 레지스트리 둘 | 둘의 주소 수정 | 수정된 것 없이 둘 다 권한 부족 이유로 실패 목록에 옴 |

## 여럿 purge

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| purge 권한을 받은 사용자가 여럿을 한 번에 purge 한다 | 레지스트리 둘, purge 권한을 받은 사용자 | 둘 purge | 둘의 id 가 처리된 목록에 오고 실패한 것은 없음 |
| 슈퍼관리자가 둘과 없는 id 하나를 한 번에 purge 한다 | 레지스트리 둘 | 셋 purge | 둘의 id 는 처리된 목록에, 없는 id 는 대상 없음 이유로 실패 목록에 옴 |
| 아무 권한도 받지 않은 사용자가 여럿을 purge 한다 | 같은 레지스트리 둘 | 둘 purge | purge 된 것 없이 둘 다 권한 부족 이유로 실패 목록에 옴 |

여럿 연산은 호출 전체를 거부하지 않는다. 처리한 레지스트리는 처리된 목록에, 처리하지 못한 것은
id 와 이유를 실패 목록에 싣는다. 레지스트리마다 따로 쓰므로 하나가 실패해도 나머지는 반영된다.
여럿 purge 의 처리된 목록은 지운 레지스트리의 id 만 싣는다.

없는 id 행의 행위자가 슈퍼관리자인 이유는, 슈퍼관리자가 검사를 모두 통과해 대상 없음이 그대로
드러나기 때문이다. 권한을 받은 사용자에게 없는 id 는 권한 그래프에 없는 대상이다.

## 아직 적지 않은 것

어느 시나리오도 부르지 않는 어댑터 호출이다. 실행 결과가 이 목록을 함께 낸다.

| 호출 | 이유 |
|---|---|
| `create` | 이 문서의 시나리오는 미리 만든 레지스트리에서 시작한다. 만들기 시나리오는 아직 적지 않았다 |
| `search` | 아직 적지 않았다 |
| `get` | 아직 적지 않았다 |
| `get_many` | 아직 적지 않았다 |
| `batch_load_by_ids` | 아직 적지 않았다 |
| `batch_load_fields` | 공통 베이스가 내놓는 호출이라 레지스트리 시나리오가 부르지 않는다 |
