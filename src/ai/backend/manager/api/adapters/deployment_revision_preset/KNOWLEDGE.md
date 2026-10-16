---
name: deployment-revision-preset-adapter-scenarios
type: reference
description: what the deployment revision preset adapter guarantees, as scenarios; only the partial bulk writes are written so far
scope: src/ai/backend/manager/api/adapters/deployment_revision_preset
keywords: [deployment revision preset, scenario, adapter, partial bulk]
generated:
  by: claude-code/opus-5
  at: 2026-10-16
status: draft
---
# deployment_revision_preset 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다. 여기 적힌 것과 실행 결과가 어긋나면 문장을 먼저
의심한다.

프리셋은 공개 스코프에 있다. 일반 사용자는 읽기만 받고, 수정과 purge 는 프리셋의 권한 검사를
통과한 사람만 한다.

## 여럿 수정하기

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 여럿의 설명을 한 번에 바꾼다 | 같은 변형의 프리셋 둘 | 둘의 설명 수정 | 둘 다 새 설명으로 오고 실패한 것은 없음 |
| 프리셋을 읽기만 하는 사용자가 여럿을 수정한다 | 같은 프리셋 둘 | 둘의 설명 수정 | 수정된 것 없이 둘 다 권한 부족 이유로 실패 목록에 옴 |

## 여럿 purge

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 둘과 없는 id 하나를 한 번에 purge 한다 | 같은 변형의 프리셋 둘 | 셋 purge | 둘은 purge 되기 전 모습으로 오고, 없는 id 는 대상 없음 이유로 실패 목록에 옴 |
| 프리셋을 읽기만 하는 사용자가 여럿을 purge 한다 | 같은 프리셋 둘 | 둘 purge | purge 된 것 없이 둘 다 권한 부족 이유로 실패 목록에 옴 |

여럿 연산은 호출 전체를 거부하지 않는다. 처리한 프리셋은 처리된 목록에, 처리하지 못한 것은
id 와 이유를 실패 목록에 싣는다.

## 아직 적지 않은 것

어느 시나리오도 부르지 않는 어댑터 호출이다.

- `search`, `available_presets`, `get`, `batch_load_by_ids`, `create`, `update`, `purge`,
  `search_resource_slots`
