---
name: prometheus-query-preset-category-adapter-scenarios
type: reference
description: what the prometheus query preset category adapter guarantees; the catalog reads open to every authenticated caller, the superadmin role on create, the entity gate on purge that no role reaches, the unique name, the purge that empties the category of the presets pointing at it
scope: src/ai/backend/manager/api/adapters/prometheus_query_preset_category
keywords: [prometheus query preset category, scenario, adapter, superadmin, public, unique name, purge]
generated:
  by: claude-code/opus-5
  at: 2026-09-11
updated:
  by: claude-code/opus-5
  at: 2026-10-16
status: draft
---
# prometheus_query_preset_category 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다. 여기 적힌 내용과 실행 결과가 어긋나면 문장 쪽을 먼저
의심한다.

카테고리는 `prometheus_query_preset`(이하 프리셋)을 묶는 단위다. 프리셋과 마찬가지로 행은 global 과
public 양쪽에 소속된다. 권한 검사는 호출마다 다르다. 조회와 검색은 public 에서 READ 를 검사하고,
생성은 호출한 사용자가 슈퍼관리자인지 검사하며, 삭제에 필요한 권한은 global 에서만 나온다. 모든
계정이 public 소속 역할을 자동으로 받으므로 로그인한 사용자는 모두 읽을 수 있다.

수정 호출이 없다. 이름이나 설명을 바꾸려면 삭제하고 다시 생성하는 수밖에 없다. 그래서 프리셋
문서에 있는 "값을 생략하면 바뀌지 않는다" 같은 수정 시나리오가 여기에는 없다.

카테고리를 참조하는 프리셋은 `../prometheus_query_preset/KNOWLEDGE.md`에 있다. 여기서는
카테고리를 삭제할 때 그 프리셋이 어떻게 되는지만 적는다.

## 생성

이름 중복은 저장소의 유일 제약이 거부하며, 도메인 오류로 매핑돼 있지 않다. 프리셋의 이름에는 유일
제약이 없으므로 두 엔티티가 반대로 동작한다.

이름이 공백뿐인 요청은 시나리오에 넣지 않는다. 요청 타입이 먼저 거부하므로 어댑터가 보장하는
동작이 아니다.

## 조회

조회는 public 에서 READ 를 검사한다. 권한 검사가 먼저 실행되고 없는 행에는 부여된 권한도 없으므로,
존재하지 않는 id와 닿을 수 없는 id는 같은 이유로 거부된다.

## 검색

## 여러 id로 조회

요청한 id마다 결과가 하나씩 반환되는 조회다. id마다 권한을 검사하므로 없는 id 자리에는 그 id를
읽을 수 없다는 거부가 담긴다.

## 삭제

삭제에 충돌 검사가 없다. 프리셋이 아직 참조하고 있어도 카테고리는 삭제되고, 그 프리셋은
`category_id`가 NULL이 된 채 남는다. 참조하는 프리셋이 있을 때 삭제를 막을지는 정해지지 않았다.
"프리셋이 참조하는 카테고리를 삭제한다" 시나리오는 현재 동작을 그대로 적은 것이다.

존재하지 않는 id는 슈퍼관리자와 그 밖의 사용자에게 서로 다른 이유로 거부된다. 권한 검사가 먼저
실행되는데 없는 행에는 부여된 권한도 없으므로, 그 밖의 사용자는 권한 부족으로 거부되고 그 검사를
통과하는 슈퍼관리자만 대상을 찾을 수 없어 거부된다.

이 어댑터에는 soft delete가 없다. 삭제하면 행이 바로 지워지고, 복구하는 호출도 없다.
삭제는 purge 다. 옛 GQL mutation 과 REST 경로는 deprecated 이고 같은 호출로 잇는다.

## 여럿 삭제

여럿 연산은 호출 전체를 거부하지 않는다. 처리한 카테고리는 처리된 목록에, 처리하지 못한 것은 id 와
이유를 실패 목록에 싣는다.
