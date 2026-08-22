---
name: domain-service-composition
type: decision-table
description: 도메인 처리기의 모양 선택, dotfile이 도메인 컬럼인 이유, 서비스가 남은 연산과 그 근거
scope: src/ai/backend/manager/services/domain
keywords:
  - DomainProcessors
  - DomainCreator
  - DomainUpdater
  - DomainDotfilesUpdater
  - dotfile
  - create_domain_node
  - RoleManagedEntityCreator
sources:
  - src/ai/backend/manager/services/domain/processors.py
  - src/ai/backend/manager/models/domain
generated:
  by: claude-code/opus-5
  at: 2026-08-19
status: draft
---

# 도메인 서비스

도메인은 다른 모든 것이 그 아래에 만들어지는 최상위 scope다. 아래에 놓일 상위 entity가
없으므로 생성은 global 모양이고, 이미 만들어진 도메인을 지목하는 연산은 single_entity다.

## 처리기 구성

배선된 목록은 `backend.ai mgr ops list --concern domain`이 낸다. entity type, 모양, 연산,
관문, 실행 주체는 그 출력이 답한다.

## 도메인은 role-managed entity다

`RoleManagedEntityCreator`를 구현하는 세 entity 중 하나다. 생성 시 자기 virtual scope
노드를 세우고 role preset이 요구하는 역할을 함께 만든다. `member_of`는 비어 있다.

## dotfile은 도메인 행의 컬럼이다

`domains.dotfiles`에 msgpack으로 묶여 저장되며 `DomainData`가 그 값을 들고 있다.
읽기는 도메인을 읽으면 딸려 오므로 별도 연산이 없고, 쓰기 셋만 존재한다.
중복 경로·개수·용량 판정은 I/O가 없으므로 `data/dotfile/types.py`의 `DotfileEntries`가
답하고, 세 저장 위치(도메인·프로젝트·키페어)가 같은 판정을 공유한다.

## 리소스 그룹은 도메인이 속하는 scope가 아니다

`search_rg_domains`는 scope 검색이 아니라 조건이 붙은 전역 검색이다. 리소스 그룹은
도메인을 담는 scope가 아니라 연관 테이블로 이어진 상대이므로, 그 연관은 searcher의
조건으로 표현한다.

## 서비스가 남은 연산

| 연산 | 남은 이유 |
|---|---|
| `create_domain` | 도메인마다 있는 model-store 프로젝트를 같은 트랜잭션에서 만든다 |
| `create_domain_node` / `update_domain_node` | 리소스 그룹 연관 행을 함께 쓴다 |
| `purge_domain` | 도메인이 남긴 커널 행을 먼저 지운다 |
| dotfile 쓰기 셋 | 읽고 병합한 뒤 쓴다 |

## 연관 행은 별도 트랜잭션이다

`ScalingGroupForDomainRow`는 도메인에도 리소스 그룹에도 속하지 않는 연관 행이라
v2 ops에 그 행을 쓰는 원시 연산이 없다. 도메인 노드 생성·수정은 도메인 쪽 쓰기와
연관 쪽 쓰기가 서로 다른 트랜잭션에서 일어난다.
