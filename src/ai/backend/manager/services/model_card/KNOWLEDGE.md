---
name: model-card-service-shapes
type: decision-table
description: 모델 카드 서비스 메서드로 남은 연산과 각각이 무엇을 검사하는지
scope: src/ai/backend/manager/services/model_card
keywords: [ModelCardCreator, ModelCardResourceRequirementCreator, bulk_scoped_search_ops, entity_create_with_fields_ops, ScanProjectModelCardsAction, AvailablePresetsAction]
sources:
  - src/ai/backend/manager/services/model_card
  - src/ai/backend/manager/models/model_card
  - src/ai/backend/manager/repositories/model_card
generated:
  by: claude-code/opus-5
  at: 2026-08-21
status: draft
---

# 모델 카드 서비스 — 배경 지식

> 규칙: `../AGENTS.md`. spec 선택: `../../models/specs/KNOWLEDGE.md`.

모델 카드는 VFolder에 담긴 모델을 프로젝트 안에서 가리키는 항목이다. 실행에 필요한
최소 자원 요구량을 함께 적으므로 이 패키지는 두 테이블을 다룬다.

## processor 필드

배선된 목록은 `backend.ai mgr ops list --concern model_card`가 낸다. entity type, 모양,
연산, 관문, 실행 주체는 그 출력이 답한다.

## 서비스 메서드로 남은 연산

| 연산 | 남은 이유 |
|---|---|
| `update` | 요구량 행을 지우고 다시 쓴다. 한 트랜잭션에 두 테이블이 걸린다 |
| `delete` / `bulk_delete` | 옵션이 켜져 있으면 카드가 쓰던 VFolder도 함께 지운다 |
| `scan` | VFolder를 훑어 이미 있는 카드 이름과 대조하고 나머지를 만든다 |
| `available_presets` | 카드가 요구하는 자원을 담을 수 있는 프리셋만 고른다 |

생성은 서비스가 필요 없다. `entity_create_with_fields_ops`가 카드와 요구량 행을 한
트랜잭션에 넣는다.
