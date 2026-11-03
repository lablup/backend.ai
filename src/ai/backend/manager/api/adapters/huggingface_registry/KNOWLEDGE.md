---
name: huggingface-registry-adapter-scenarios
type: reference
description: what the huggingface registry adapter guarantees for update, purge and their partial bulk forms
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

## purge

단건 purge 와 여럿 purge 모두 purge 권한을 본다.

## 여럿 수정하기

## 여럿 purge

여럿 연산은 호출 전체를 거부하지 않는다. 처리한 레지스트리는 처리된 목록에, 처리하지 못한 것은
id 와 이유를 실패 목록에 싣는다. 레지스트리마다 따로 쓰므로 하나가 실패해도 나머지는 반영된다.
여럿 purge 의 처리된 목록은 지운 레지스트리의 id 만 싣는다.

없는 id 행의 행위자가 슈퍼관리자인 이유는, 슈퍼관리자가 검사를 모두 통과해 대상 없음이 그대로
드러나기 때문이다. 권한을 받은 사용자에게 없는 id 는 권한 그래프에 없는 대상이다.
