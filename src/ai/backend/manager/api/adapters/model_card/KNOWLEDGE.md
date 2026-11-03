---
name: model-card-adapter-scenarios
type: reference
description: what the model card adapter guarantees; update and purge authorization, and the partial bulk result shape
scope: src/ai/backend/manager/api/adapters/model_card
keywords: [model card, scenario, adapter, rbac, purge, partial_bulk]
generated:
  by: claude-code/opus-5
  at: 2026-10-16
status: draft
---
# 모델 카드 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다.

## 조회

## 수정

카드는 프로젝트에 놓인 폴더 위에 얹는다. 카드를 만든 사람과 부르는 사람은 다르다. 권한은 카드가
놓인 프로젝트에서 받는다. 수정은 고친 카드를 최소 자원 요구와 함께 읽어 답하므로 읽기 권한도
필요하다.

## purge

purge 는 카드 행을 지운다. 옵션을 주면 카드가 얹힌 폴더를 휴지통으로 옮긴다.

## 여럿 수정하기

## 여럿 purge

여럿 연산은 호출 전체를 거부하지 않는다. 처리한 카드는 처리된 목록에, 처리하지 못한 것은 id 와
이유를 실패 목록에 싣는다. purge 된 카드의 최소 자원 요구는 카드와 함께 지워져 처리된 목록에
싣지 않는다.
