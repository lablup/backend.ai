---
name: runtime-variant-adapter-scenarios
type: reference
description: what the runtime variant adapter guarantees, as scenarios; the superadmin role on create, the entity gate nobody but a superadmin passes on update and delete, the reads open to every authenticated user, the bulk delete that answers per id
scope: src/ai/backend/manager/api/adapters/runtime_variant
keywords: [runtime variant, scenario, adapter, superadmin, public read, lookup, bulk delete, partial bulk purge]
generated:
  by: claude-code/opus-5
  at: 2026-09-11
updated:
  by: claude-code/opus-5
  at: 2026-09-18
status: draft
---
# runtime_variant 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다. 여기 적힌 내용과 실행 결과가 어긋나면 문장 쪽을 먼저
의심한다.

`runtime_variant` 행은 어느 스코프에도 속하지 않게 만들어진다. 생성은 호출한 사용자가 슈퍼관리자인지
검사하고, 하나를 지정해 수정·삭제하는 호출은 그 `runtime_variant` 행에 부여된 권한을 검사한다. 그런데
역할은 스코프에 속하고 `runtime_variant` 행은 어느 스코프에도 없으므로, 그 권한을 받을 방법이
없다. 생성과 수정·삭제 모두 슈퍼관리자만 통과하지만 거부 이유가 서로 다르다. id 조회, 이름을 id로
변환, 여러 id 조회는 어떤 검사도 없이 인증만 확인한다.

`runtime_variant` 하위의 preset은 자기 어댑터를 가지므로 `../runtime_variant_preset/KNOWLEDGE.md`에
있다.

## 생성

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 이름만 지정해 생성한다 | `runtime_variant` 없음, 슈퍼관리자 | 이름만 지정해 생성 | 설명은 비어 있고, `reads_vfolder_config_files` 값은 false이며, `default_model_definition` 필드는 코드가 정해 둔 기본값인 노드 |
| 이름과 설명을 함께 지정해 생성한다 | `runtime_variant` 없음, 슈퍼관리자 | 이름과 설명으로 생성 | 지정한 값이 그대로 담긴 노드 |
| 이미 사용 중인 이름으로 생성한다 | 그 이름의 `runtime_variant` 행 있음, 슈퍼관리자 | 생성 | 이름 중복으로 거부 |
| 슈퍼관리자가 아닌 사용자가 생성한다 | 슈퍼관리자 아님 | 생성 | 역할 부족으로 거부 |
| 권한 검사를 꺼도 슈퍼관리자가 아니면 생성할 수 없다 | 권한 검사 비활성화, 슈퍼관리자 아님 | 생성 | 역할 부족으로 거부 |

`default_model_definition` 필드와 `reads_vfolder_config_files` 값은 요청으로 정할 수 없다. 생성이
값을 고정하고, 어느 호출도 그 둘을 바꾸지 않는다. 생성 시점의 값이 그대로 유지되므로
"슈퍼관리자가 이름만 지정해 생성한다" 시나리오가 둘을 함께 검사한다.

이름이 비어 있거나 길이 제한을 넘는 요청은 시나리오로 두지 않는다. 요청 타입이 이미 거부하므로
어댑터가 보장하는 것이 아니다.

## 조회

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 아무 권한도 없는 사용자가 id로 조회한다 | `runtime_variant` 하나, 아무 권한도 없음 | id로 조회 | 그 `runtime_variant` 노드 전체 |
| 존재하지 않는 id로 조회한다 | 다른 `runtime_variant` 행만 있음 | id로 조회 | 대상을 찾을 수 없어 거부 |
| 이름으로 id를 얻는다 | `runtime_variant` 하나, 아무 권한도 없음 | 이름을 id로 변환 | 그 `runtime_variant` 행의 id |
| 존재하지 않는 이름을 변환한다 | 다른 `runtime_variant` 행만 있음 | 이름을 id로 변환 | 대상을 찾을 수 없어 거부 |
| 있는 것과 없는 것을 섞어 조회한다 | `runtime_variant` 둘, 아무 권한도 없음 | 세 id를 한 번에 | 요청한 순서대로 반환되고, 없는 id에 해당하는 항목은 비어 있다 |
| 빈 목록을 준다 | `runtime_variant` 하나 | 빈 id 목록 | 빈 응답. 하위 계층을 호출하지 않는다 |

조회에는 권한 검사가 없다. 아무 권한도 없는 사용자가 성공하는 시나리오가 그것을 증명하므로, 이
절에는 권한 부족으로 거부되는 시나리오가 없다. 그에 대응하는 시나리오는 생성 절의 역할 부족으로
거부되는 시나리오다. 같은 사용자가 조회는 할 수 있고 생성은 할 수 없다.

이름을 id로 변환하는 호출에는 뒤따르는 권한 검사가 없다. 그래서 존재하지 않는 이름은 그대로
대상을 찾을 수 없어 거부된다. 권한 검사가 뒤따르는 변환은 존재하지 않는 키와 접근할 수 없는 키를
같은 이유로 거부하지만, 이 변환은 그 경우에 해당하지 않는다.

인증되지 않은 호출은 시나리오로 두지 않는다. 시나리오는 언제나 미리 만들어 둔 사용자로 호출한다.

## 검색

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 아무 권한도 없는 사용자가 검색한다 | `runtime_variant` 둘, 아무 권한도 없음 | 전체 조회 | 둘 다 반환된다 |
| 이름 필터로 검색한다 | 이름이 다른 `runtime_variant` 여럿 | 이름 필터 조회 | 그 이름의 `runtime_variant` 노드만 반환된다 |
| 페이지 크기를 생략한다 | `runtime_variant` 11개 | 크기 없이 조회 | 10건까지 반환되고 다음 페이지가 있다고 응답한다 |

## 수정

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 이름만 바꾼다 | 설명이 있는 `runtime_variant` 하나, 슈퍼관리자 | 이름 수정 | 이름은 새 값, 설명은 그대로 |
| 설명을 지운다 | 설명이 있는 `runtime_variant`, 슈퍼관리자 | 설명을 비우는 수정 | 설명이 없어진다 |
| 값을 하나도 지정하지 않는다 | `runtime_variant` 하나, 슈퍼관리자 | 빈 수정 | 아무것도 바뀌지 않은 노드 |
| 이미 사용 중인 이름으로 바꾼다 | `runtime_variant` 둘, 슈퍼관리자 | 한쪽 이름을 다른 쪽 이름으로 수정 | 이름 중복으로 거부 |
| 존재하지 않는 id를 수정한다 | 다른 `runtime_variant` 행만 있음, 슈퍼관리자 | 이름 수정 | 대상을 찾을 수 없어 거부 |
| 아무 권한도 없는 사용자가 수정한다 | 같은 `runtime_variant`, 아무 권한도 없음 | 이름 수정 | 권한 부족으로 거부 |
| 아무 권한도 없는 사용자가 없는 id를 수정한다 | 다른 `runtime_variant` 행만 있음, 아무 권한도 없음 | 이름 수정 | 권한 부족으로 거부 |
| 권한 검사를 끄면 권한 없이도 수정된다 | 권한 검사 비활성화, 아무 권한도 없음 | 이름 수정 | 이름이 새 값인 노드 |

설명은 세 가지(생략·비우기·값 지정)를 받고 이름은 생략과 값 지정 둘뿐이다. 그래서 비우는
시나리오는 설명에만 둔다.

존재하지 않는 id는 슈퍼관리자와 그 밖의 사용자에게 서로 다른 이유로 거부된다. 권한 검사가 먼저
실행되는데 없는 행에는 부여된 권한도 없으므로, 그 검사를 통과하는 슈퍼관리자만 대상을 찾을 수
없어 거부된다. 삭제 절의 같은 시나리오도 마찬가지다.

이름 중복은 생성할 때와 수정할 때 서로 다른 오류로 거부된다. 생성은 이 엔티티의 오류로 거부하고,
수정은 저장소의 제약 위반을 그대로 전파한다. 시나리오를 적기 전에 하나로 맞출 것인지 정한다.

## 삭제

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 삭제한다 | `runtime_variant` 하나, 슈퍼관리자 | 삭제 | 삭제한 id를 담은 응답 |
| 존재하지 않는 id를 삭제한다 | 다른 `runtime_variant` 행만 있음, 슈퍼관리자 | 삭제 | 대상을 찾을 수 없어 거부 |
| 아무 권한도 없는 사용자가 삭제한다 | 같은 `runtime_variant`, 아무 권한도 없음 | 삭제 | 권한 부족으로 거부 |
| 권한 검사를 끄면 권한 없이도 삭제된다 | 권한 검사 비활성화, 아무 권한도 없음 | 삭제 | 삭제한 id를 담은 응답 |
| 여럿을 한 번에 삭제한다 | `runtime_variant` 둘, 슈퍼관리자 | 두 id를 한 번에 | 둘 다 삭제된 목록에 담기고 실패 목록은 비어 있다 |
| 없는 id가 섞인 목록을 삭제한다 | `runtime_variant` 하나, 슈퍼관리자 | 있는 id 뒤에 없는 id를 붙여 한 번에 | 있는 것은 삭제된 목록에, 없는 id는 실패 목록에 담긴다 |
| 아무 권한도 없는 사용자가 여럿을 삭제한다 | `runtime_variant` 둘, 아무 권한도 없음 | 두 id를 한 번에 | 둘 다 실패 목록에 담기고 아무것도 삭제되지 않는다 |

일괄 삭제는 id마다 따로 답한다. 권한 검사도 id마다이고, 거부된 id는 실패 목록에 들어가며
호출 자체는 거부되지 않는다. 없는 id도 실패 목록에 들어간다. 삭제된 것은 요청한 순서대로
삭제된 목록에 노드로 담기고, 삭제 수는 그 목록의 길이다. `runtime_variant` 행마다 자기
savepoint 안에서 preset과 함께 지워지므로, 하나가 실패해도 나머지는 삭제된 채 남는다.

삭제는 `runtime_variant` 하위의 preset을 먼저 지우고 `runtime_variant` 행을 지운다. preset을 가진
`runtime_variant` 행을 삭제하는 시나리오는 `test_retiring.py`에 주석 처리해 두었다. preset seed가
`../runtime_variant_preset`의 시나리오와 함께 추가되고, preset의 `runtime_variant` 컬럼이 ORM에서도
마이그레이션과 같은 외래 키를 갖게 되면(BA-7931) 주석을 해제한다.

이 어댑터에는 soft delete가 없다. 삭제하면 행이 사라지고 되살리는 호출도 없다.

## 아직 적지 않은 것

없다. 어댑터가 제공하는 `create`, `get`, `resolve_by_name`, `batch_load_by_ids`, `search`,
`update`, `delete`, `bulk_delete`가 모두 위에 있다.

`batch_load_fields`는 모든 어댑터가 물려받는 공용 헬퍼이지 이 엔티티의 호출이 아니다. 리포트에서는
함께 세지만 시나리오로 적을 것은 없다.
