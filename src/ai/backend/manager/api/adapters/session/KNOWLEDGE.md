---
name: session-adapter-scenarios
type: reference
description: what the session adapter guarantees: project scope permissions, and how bulk terminate and terminate report their results
scope: src/ai/backend/manager/api/adapters/session
keywords: [session, scenario, adapter, rbac, enqueue]
generated:
  by: claude-code/opus-5
  at: 2026-09-10
status: draft
---
# 세션 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다.

세션은 자기가 속한 프로젝트를 이름으로 댄다. 그래서 세션 권한은 프로젝트 스코프에 앉고, 그
역할을 주는 일이 곧 그 사람을 프로젝트 명부에 올리는 일이 된다.

## 조회

필터 없는 전체 조회는 슈퍼관리자 역할로 막힌다. 스코프 권한으로 막히는 조회는 스코프를
받는 검색이다.

## 여럿 종료하기

여럿 종료는 호출 전체를 거부하지 않는다. 처리한 세션은 끝난 상태(취소됨, 종료 중, 강제 종료됨,
건너뜀)와 함께 처리된 목록에, 거부된 세션은 id 와 이유를 실패 목록에 싣는다. 이미 끝났거나 없는
세션은 건너뜀으로 처리된 목록에 온다.

## 종료하기 (옛 이름)

옛 종료는 여럿 종료와 같은 처리를 부르고 답을 끝난 상태별 목록으로 나눈다. 거부된 세션이
하나라도 있으면 호출 전체를 거부한다.
