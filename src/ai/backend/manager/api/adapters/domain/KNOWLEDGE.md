---
name: domain-adapter-scenarios
type: reference
description: what the domain adapter guarantees about creation, reads, name lookup, updates, deletion, and search
scope: src/ai/backend/manager/api/adapters/domain
keywords: [domain, scenario, adapter, rbac, superadmin, lookup_name, scoped_search]
generated:
  by: claude-code/opus-5
  at: 2026-09-28
status: draft
---
# 도메인 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다. 여기 적힌 것과 실행 결과가 어긋나면 문장을 먼저
의심한다.

도메인에는 권한 그래프로 권한을 줄 수 없다. 어느 스코프에도 속하지 않게 만들어지고 자기 아래
하위 엔티티를 갖지 않는다. 그래서 생성과 전체 조회는 전역 superadmin 역할이 지키고, 개별
도메인을 읽고 고치는 문은 권한 그래프가 지킨다. 두 문이 서로 다른 것으로 거부하므로 짝을 따로
적는다. 권한을 받은 사용자가 나오는 곳은 리소스 그룹 범위의 조회뿐이다.

공통 계약(대상 존재, 일괄 구성, 페이지)은 프레임워크 계약 테스트가 확인한다. 여기에는 연산마다
대표 성공과 대표 실패, 그리고 도메인 규칙이 만드는 차이만 적는다.

## 만들기

집행을 끄는 줄이 따로 있는 이유는, 이 문이 권한 그래프가 아니라 역할이라 집행 스위치와
무관하다는 것을 못박기 위해서다.

만들기는 리소스 그룹을 연결하지 않는다. 연결은 리소스 그룹 쪽 허용 목록 호출이 하고, 그
시나리오는 리소스 그룹 어댑터 문서에 있다.

레거시 GQL `CreateDomainNode`·`ModifyDomainNode`는 도메인 만들기·수정과 리소스 그룹 연결을 따로
부른다. 연결이 실패하면 만들기·수정만 반영된 도메인이 남는다.

## 읽기

없는 대상과 권한 없음이 서로 다른 것으로 거부되어야 한다. 하나로 뭉치면 어느 쪽으로 막혔는지
호출자가 알 수 없다.

## 여럿 읽기

여럿 읽기는 호출 전체를 거부하지 않고 자리마다 답한다.

## 이름으로 id 찾기

두 호출 모두 인증만 본다. 권한은 그 id를 받는 호출이 본다. 그래서 권한이 없어도 이름이
있는지는 드러나며, 설계상 허용한다. 다른 엔티티의 REST handler와 GQL resolver는 도메인 이름을
id로 풀 때 이 호출을 먼저 부른다. GQL은 여럿 찾기를 이름 → id 로더로 써서 id로 여럿 읽기로
잇는다.

## 수정하기

수정도 리소스 그룹을 더하거나 빼지 않는다. 만들기와 같이 리소스 그룹 쪽 허용 목록 호출이 한다.

수정의 활성 플래그는 deprecated 다. 내리면 soft delete, 올리면 restore 를 부르고, 이미 그 상태면
부르지 않는다. 나머지 필드는 수정으로 반영한다. 상태는 노드에 실리지 않아 시나리오는 활성 플래그로
본다.

## soft delete, restore, purge

soft delete 와 restore 는 지금 상태를 보지 않는다. 이미 그 상태여도 했다는 답이 온다. purge 도
soft delete 되었는지를 보지 않는다. 딸린 것이 없으면 활성 도메인도 purge 된다.

soft delete 는 활성 플래그를 내리고 상태를 삭제로 바꾼다. restore 는 둘을 되돌린다.

단건 수정, soft delete, restore 는 id 를 받는다. 이름을 받는 옛 REST 경로와 GQL mutation 은
이름으로 id 찾기를 먼저 부르고 같은 호출로 잇는다. 위 표의 이름으로 부르는 행이 그 길이다. purge 는
이름을 받는다.

## 여럿 수정하기

여럿 수정은 항목마다 단건 수정과 같은 기준으로 soft delete 와 restore 를 부른다. 실패는 항목마다
실패 목록에 싣는다.

## 여럿 soft delete, restore

여럿 연산은 호출 전체를 거부하지 않는다. 처리한 도메인은 처리된 목록에, 처리하지 못한 것은 id 와
이유를 실패 목록에 싣는다. 여럿 purge 는 없다.

## search

## 리소스 그룹 범위에서 search

리소스 그룹 이름으로 묻는 GQL resolver는 리소스 그룹 adapter의 이름으로 id 찾기를 먼저 부르고,
얻은 id를 범위로 넘긴다. 도메인 adapter는 리소스 그룹 이름을 풀지 않는다.
