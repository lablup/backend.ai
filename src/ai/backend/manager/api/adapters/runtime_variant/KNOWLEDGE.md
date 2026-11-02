---
name: runtime-variant-adapter-scenarios
type: reference
description: what the runtime variant adapter guarantees; the superadmin role on create, the entity gate nobody but a superadmin passes on update and purge, the reads answered in the public scope, the partial bulk update and purge that answer per id
scope: src/ai/backend/manager/api/adapters/runtime_variant
keywords: [runtime variant, scenario, adapter, superadmin, public read, lookup, bulk delete, partial bulk update, partial bulk purge]
generated:
  by: claude-code/opus-5
  at: 2026-09-11
updated:
  by: claude-code/opus-5
  at: 2026-10-16
status: draft
---
# runtime_variant 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다. 여기 적힌 내용과 실행 결과가 어긋나면 문장 쪽을 먼저
의심한다.

`runtime_variant` 행은 global 과 public 양쪽에 소속되어 만들어진다. 생성은 호출한 사용자가
슈퍼관리자인지 검사하고, 하나를 지정해 수정·삭제하는 호출은 그 `runtime_variant` 행에 부여된 권한을
검사한다. 그 권한은 global 에서만 나오므로 슈퍼관리자만 통과하며, 생성과 수정·삭제의 거부 이유는
서로 다르다. id 조회, 이름을 id로 변환, 여러 id 조회, 검색은 public 에서 READ 를 검사한다. 모든
계정이 public 소속 역할을 자동으로 받으므로 로그인한 사용자는 모두 읽을 수 있다.

`runtime_variant` 하위의 preset은 자기 어댑터를 가지므로 `../runtime_variant_preset/KNOWLEDGE.md`에
있다.

## 생성

`default_model_definition` 필드와 `reads_vfolder_config_files` 값은 요청으로 정할 수 없다. 생성이
값을 고정하고, 어느 호출도 그 둘을 바꾸지 않는다. 생성 시점의 값이 그대로 유지되므로
"슈퍼관리자가 이름만 지정해 생성한다" 시나리오가 둘을 함께 검사한다.

이름이 비어 있거나 길이 제한을 넘는 요청은 시나리오로 두지 않는다. 요청 타입이 이미 거부하므로
어댑터가 보장하는 것이 아니다.

## 조회

조회는 public 에서 READ 를 검사한다. public 조회 권한만 받은 사용자가 성공하는 시나리오가 그것을
증명한다. 같은 사용자가 조회는 할 수 있고 생성은 할 수 없다. 그에 대응하는 거부 시나리오는 생성
절의 역할 부족으로 거부되는 시나리오다.

존재하지 않는 id와 닿을 수 없는 id는 같은 이유로 거부된다. 권한 검사가 먼저 실행되는데 없는 행에는
부여된 권한도 없기 때문이다. 이름을 id로 변환하는 호출도 변환한 대상에 권한 검사가 뒤따르므로,
존재하지 않는 이름과 접근할 수 없는 이름을 같은 이유로 거부한다.

인증되지 않은 호출은 시나리오로 두지 않는다. 시나리오는 언제나 미리 만들어 둔 사용자로 호출한다.

## 검색

## 수정

## 여럿 수정하기

설명은 세 가지(생략·비우기·값 지정)를 받고 이름은 생략과 값 지정 둘뿐이다. 그래서 비우는
시나리오는 설명에만 둔다.

존재하지 않는 id는 슈퍼관리자와 그 밖의 사용자에게 서로 다른 이유로 거부된다. 권한 검사가 먼저
실행되는데 없는 행에는 부여된 권한도 없으므로, 그 검사를 통과하는 슈퍼관리자만 대상을 찾을 수
없어 거부된다. 삭제 절의 같은 시나리오도 마찬가지다.

이름 중복은 생성할 때와 수정할 때 서로 다른 오류로 거부된다. 생성은 이 엔티티의 오류로 거부하고,
수정은 저장소의 제약 위반을 그대로 전파한다. 시나리오를 적기 전에 하나로 맞출 것인지 정한다.

## purge

단건 purge 와 여럿 purge 는 `purge`, `partial_bulk_purge` 다. 옛 일괄 삭제(`bulk_delete`)는 같은
processor 를 부르고 id 목록과 삭제 수로 답한다. 표의 여럿을 삭제하는 행 셋이 그 길이다.

일괄 삭제는 id마다 따로 답하는 partial bulk purge다. 권한 검사도 id마다이고, 거부된 id와 없는
id는 실패 목록에 들어가며 호출 자체는 거부되지 않는다. 삭제된 id는 요청한 순서대로 삭제된
목록에 담기고, 삭제 수는 그 목록의 길이다. `runtime_variant` 행마다 자기 savepoint 안에서
preset과 함께 지워지므로, 하나가 실패해도 나머지는 삭제된 채 남는다.

삭제는 `runtime_variant` 하위의 preset을 먼저 지우고 `runtime_variant` 행을 지운다. preset을 가진
`runtime_variant` 행을 삭제하는 시나리오는 `test_retiring.py`에 주석 처리해 두었다. preset seed가
`../runtime_variant_preset`의 시나리오와 함께 추가되고, preset의 `runtime_variant` 컬럼이 ORM에서도
마이그레이션과 같은 외래 키를 갖게 되면(BA-7931) 주석을 해제한다.

이 어댑터에는 soft delete가 없다. 삭제하면 행이 사라지고 되살리는 호출도 없다.
