---
name: resource-slot-adapter-scenarios
type: reference
description: what the resource slot adapter guarantees: the name-keyed slot type catalog with the superadmin role on create and update against the entity gate on purge and the rows that refuse a purge while referenced, the agent resource reads gated by a role in the agent's resource group, the kernel allocation reads gated by a role over the kernel's session with a lookup that answers a missing kernel and a missing permission alike, and the domain and project overviews gated by session read in that scope
scope: src/ai/backend/manager/api/adapters/resource_slot
keywords: [resource slot type, agent resource, kernel allocation, resource overview, scenario, adapter, superadmin, lookup, purge, in use, public read]
generated:
  by: claude-code/opus-5
  at: 2026-09-11
updated:
  by: claude-code/opus-5
  at: 2026-10-16
status: draft
---
# resource_slot 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다. 여기 적힌 내용과 실행 결과가 어긋나면 문장 쪽을 먼저
의심한다.

이 어댑터는 `resource_slot_type` 카탈로그, 에이전트가 보고한 리소스인 `agent_resource` 행의 조회,
커널이 할당받은 리소스인 `resource_allocation` 행의 조회, 그리고 도메인과 프로젝트의 리소스 개요를
다룬다.

`resource_slot_type` 행은 global 과 public 양쪽에 소속되어 만들어진다. 생성과 수정은 호출한
사용자가 슈퍼관리자인지 검사한다. 삭제만 그 `resource_slot_type` 행에 대한 HARD_DELETE 권한을
검사하는데, 그 권한은 global 에서만 나오므로 슈퍼관리자만 통과한다. 조회와 검색은 public 에서 READ 를 검사한다.
모든 계정이 public 소속 역할을 자동으로 받으므로 로그인한 사용자는 모두 읽을 수 있다.

`resource_slot_type` 의 조회와 수정은 이름을 받는다. 먼저 이름으로 id를 찾은 뒤 실제 연산을 실행한다.
삭제와 여럿 삭제는 id를 받는다. 이름을 받는 옛 삭제 호출(GQL `admin_purge_resource_slot_type`,
REST `DELETE /slot-types/{slot_name}`)은 이름으로 id 찾기를 먼저 부르고 같은 삭제로 잇는다.
쓰기는 호출한 사용자가 쓸 수 있는지를 대상을 찾기 전에 검사한다. 슈퍼관리자가 아니거나 권한이 없는
사용자는 대상이 있든 없든 같은 이유로 거부된다.

`agent_resource`·`resource_allocation` 전역 검색은 슈퍼관리자인지 검사하되, 검색은 읽기 연산이므로
모니터도 통과한다. 에이전트 하나를 지정하는 조회와 검색은 그 에이전트에 대한 권한을 검사한다.
에이전트는 자기 리소스 그룹 안에 만들어지므로, 그 권한은 리소스 그룹 범위의 역할이 부여한다. 커널
하나의 `resource_allocation` 조회는 그 커널이 속한 세션에 대한 권한을 검사한다. 세션은 자기 프로젝트
안에 만들어지므로, 그 권한은 프로젝트 범위나 그 도메인 범위의 역할이 부여한다. 개요는 도메인 또는
프로젝트 범위의 세션 조회 권한을 검사한다.

권한 검사 설정을 끄면 엔티티와 범위에 대한 권한 검사는 모두 통과하지만, 슈퍼관리자 검사는 그
설정을 읽지 않는다.

## 생성

이미 사용 중인 이름을 덮어쓰지 않고 거부하는 것은 이 행을
`agent_resources`·`resource_allocations`·`model_card_resource_requirements`·`preset_resource_slots`·`deployment_revision_resource_slots`
테이블이 참조하기 때문이다. 덮어쓰면 그 이름으로 기록된 할당량의 의미가 모두 바뀐다.

노드의 id는 uuid가 아니라 슬롯 이름이다. 다른 엔티티에서 id를 무시하는 검사를 여기 그대로
가져오면 이름 검사를 잃으므로, 이 엔티티에서는 id를 검사하고 uuid를 무시한다.

## 조회

조회는 public 에서 READ 를 검사한다. 이름으로 id를 찾는 단계도 찾아낸 대상에 권한 검사가 뒤따르므로,
존재하지 않는 이름과 닿을 수 없는 이름이 같은 이유로 거부된다. public 조회 권한만 받은 사용자가
성공하는 시나리오가 그것을 증명하고, 생성 절의 역할 부족으로 거부되는 시나리오와 대비된다.

인증되지 않은 호출은 시나리오로 두지 않는다. 시나리오는 언제나 미리 만들어 둔 사용자로 호출한다.

## 검색

요청 타입이 받는 필드는 모두 읽힌다. 이름·`slot_type`·`display_name` 필터와 `limit`·`offset`, 그리고
`first`·`after`·`last`·`before` 필드다. 받아 놓고 무시하는 필드는 없다.

## 수정

이름과 `slot_type` 값은 수정할 수 없다. 요청 타입이 그 둘을 받지 않으므로 시나리오로 두지 않는다.

슈퍼관리자가 아닌 사용자가 없는 이름을 수정하는 시나리오가 이 절의 핵심이다. 슈퍼관리자가 아닌
사용자는 이름이 있을 때와 같은 이유로 거부된다. 이름으로 id를 찾는 단계가 슈퍼관리자 검사보다 먼저
실행되면 대상을 찾을 수 없다는 거부 이유가 노출되는데, 그 순서가 아니라는 것을 이 행이 확인한다.
삭제 절의 같은 시나리오와 나란히 둔다.

## 이름으로 id 찾기

찾은 대상에 public 에서 READ 를 검사한다. 모든 계정이 그 권한을 받으므로 아무 권한도 받지 않은
사용자도 찾는다.

## 삭제

참조하는 테이블마다 시나리오를 하나씩 둔다.
`agent_resources`·`resource_allocations`·`model_card_resource_requirements`·`preset_resource_slots`·`deployment_revision_resource_slots`
검사가 각각 따로 실행되고, 어느 하나가 빠지면 그 경우는 거부가 아니라 제약 위반으로 실패한다.
한 시나리오로 합치면 그 검사 중 하나만 남아 있어도 통과한다.

수정과 삭제가 같은 `resource_slot_type` 행에 대해 서로 다른 이유로 거부한다. 수정은 역할 부족,
삭제는 권한 부족이다.

이 어댑터에는 soft delete가 없다.

## 여럿 삭제

여럿 삭제는 호출 전체를 거부하지 않는다. 처리한 `resource_slot_type` 은 처리된 목록에, 처리하지
못한 것은 id 와 이유를 실패 목록에 싣는다. 아직 참조 중인 `resource_slot_type` 도 그것만 실패
목록에 온다.

## `agent_resource` 조회

`agent_id` 값으로 에이전트를 찾는 단계는 인증만 확인한다. 아무 권한도 없는 사용자가 없는 `agent_id`
값으로 조회하면 대상을 찾을 수 없어 거부되는 것이 그 증거다. 권한은 찾은 에이전트에 대해, 슬롯을
찾기 전에 검사한다.

## `agent_resource` 검색

정렬을 지정하지 않으면 슬롯 이름 순서로 반환된다. 이 검색은 슬롯 순위를 보지 않는다.

## 지정한 에이전트의 `agent_resource` 검색

지정한 에이전트마다 권한을 검사하고, 하나라도 읽을 수 없으면 읽을 수 있는 쪽만 반환하지 않고
전체를 거부한다.

## `resource_allocation` 조회

커널 id로 세션을 찾는 단계가 그 세션에 대한 권한을 검사한다. 권한이 없을 때와 커널이 없을 때 같은
이유로 거부되므로, 거부 이유만으로는 그 커널이 있는지 알 수 없다. 모든 검사를 통과하는
슈퍼관리자에게만 커널이 없다는 사실이 그대로 드러난다.

## `resource_allocation` 검색

## 도메인 리소스 개요

개요는 리소스를 점유했거나 배정받은 커널만 세고, 요구만 하고 대기 중인 커널은 세지 않는다.
대기 중인 커널만 있는 도메인의 개요가 비어 있는 것이 그 증거다.

## 프로젝트 리소스 개요

도메인 범위의 세션 조회 권한은 그 안의 프로젝트에도 미치고, 프로젝트 범위의 권한은 도메인에
미치지 않는다. 이 절의 도메인 범위 시나리오와 도메인 개요 절의 프로젝트 범위 시나리오가 그것을
각각 확인한다.

프로젝트는 이름이 아니라 id로 지정하므로 id를 찾는 단계가 없고, 프로젝트가 있는지 확인하지
않는다. 존재하지 않는 id로 조회하면 거부가 아니라 빈 개요가 반환된다.
