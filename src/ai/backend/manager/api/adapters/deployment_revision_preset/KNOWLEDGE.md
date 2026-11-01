---
name: deployment-revision-preset-adapter-scenarios
type: reference
description: what the deployment revision preset adapter guarantees; the preset lives in the public scope, general users read it, and the bulk purge answers per preset
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

## 여럿 purge

여럿 연산은 호출 전체를 거부하지 않는다. 처리한 프리셋은 처리된 목록에, 처리하지 못한 것은
id 와 이유를 실패 목록에 싣는다.
