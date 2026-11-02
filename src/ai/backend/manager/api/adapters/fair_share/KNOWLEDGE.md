---
name: fair-share-adapter-scenarios
type: reference
description: "what the fair share adapter guarantees: the global authorization check on weight writes and the single transaction of bulk upsert"
scope: src/ai/backend/manager/api/adapters/fair_share
keywords: [fair share, weight, upsert, atomic bulk, scenario, adapter, rbac]
generated:
  by: claude-code/opus-5.5
  at: 2026-10-16
status: draft
---
# fair_share 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다. 여기 적힌 것과 실행 결과가 어긋나면 문장을 먼저
의심한다.

fair share 기록은 리소스 그룹과 도메인, 프로젝트, 사용자 중 하나를 함께 키로 갖는다. 가중치를
쓰는 문은 그 리소스 그룹을 지목하는 권한 검사지만, 검사하는 대상 타입이 리소스 그룹이 아니라
전역이다. 전역 타입 권한은 역할로 줄 수 없으므로, 그 그룹에 앉힌 역할로 수정 권한을 받은 사용자도
가중치를 쓰지 못한다. 지금 가중치를 쓸 수 있는 것은 슈퍼관리자뿐이다.

## 가중치 하나 정하기

## 가중치 여럿 한 번에 정하기

여럿 정하기는 한 트랜잭션이다. 항목마다 따로 답하지 않고, 실패하면 호출 전체가 거부된다.
