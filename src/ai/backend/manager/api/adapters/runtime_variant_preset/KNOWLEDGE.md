---
name: runtime-variant-preset-adapter-scenarios
type: reference
description: what the runtime variant preset adapter guarantees, as scenarios; the rank the insert fills in, the value-type rule checked by the request on create and by the service on update, the batch read that is a search, the variant column with no foreign key in the ORM
scope: src/ai/backend/manager/api/adapters/runtime_variant_preset
keywords: [runtime variant preset, scenario, adapter, superadmin, rank, value type, flag, public read]
generated:
  by: claude-code/opus-5
  at: 2026-09-11
updated:
  by: claude-code/opus-5
  at: 2026-09-21
status: draft
---
# runtime_variant_preset 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다. 여기 적힌 내용과 실행 결과가 어긋나면 문장을 먼저
검토한다.

`runtime_variant_preset` 엔티티는 `runtime_variant` 하나를 컬럼으로 참조하지만 그 스코프 안에서
생성되지는 않는다. 행은 global 과 public 양쪽에 소속된다. 생성은 호출한 사용자가 슈퍼관리자인지
검사한다. 수정과 삭제에 필요한 프리셋별 권한은 global 에서만 나오므로 슈퍼관리자만 통과한다. 조회와
검색은 public 에서 READ 를 검사한다. 모든 계정이 public 소속 역할을 자동으로 받으므로 로그인한
사용자는 모두 읽을 수 있다.

`runtime_variant` 어댑터의 시나리오는 `../runtime_variant/KNOWLEDGE.md`에 있다.

## 생성

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 필수 항목만 지정해 생성한다 | `runtime_variant` 하나, 해당 `runtime_variant`에 프리셋이 없음, 슈퍼관리자 | 이름과 `runtime_variant_id`·`preset_target`·`value_type`·`key` 필드만 지정하여 생성 | `rank` 값은 100이고 `required` 값은 false이며, 나머지 선택 항목은 비어 있음 |
| 같은 `runtime_variant`에 하나 더 생성한다 | 해당 `runtime_variant`에 프리셋 하나, 슈퍼관리자 | 생성 | 새 프리셋의 `rank` 값이 기존 프리셋보다 100 큼 |
| `preset_target`·`value_type`·`default_value`·`key` 필드를 모두 지정해 생성한다 | `runtime_variant` 하나, 슈퍼관리자 | `preset_target`·`value_type`·`default_value`·`key` 필드를 모두 지정하여 생성 | 지정한 `preset_target`·`value_type`·`default_value`·`key` 값이 `target_spec` 하나로 묶여 반환됨 |
| `ui_option` 필드를 지정해 생성한다 | `runtime_variant` 하나, 슈퍼관리자 | `ui_option`에 `slider` 옵션을 추가하여 생성 | `ui_option` 필드에서 읽은 `ui_type` 값이 응답 노드에 함께 포함됨 |
| 같은 `runtime_variant` 안에서 이름이 중복된다 | 해당 `runtime_variant`에 같은 이름의 프리셋이 있음, 슈퍼관리자 | 생성 | 이름 중복으로 거부 |
| 다른 `runtime_variant`에 속하면 같은 이름을 쓸 수 있다 | `runtime_variant` 둘, 한쪽에만 프리셋 하나, 슈퍼관리자 | 다른 `runtime_variant`에 같은 이름으로 생성 | 생성됨 |
| 슈퍼관리자가 아닌 사용자가 생성한다 | `runtime_variant` 하나, 슈퍼관리자 아님 | 생성 | 역할 부족으로 거부 |
| 권한 검사를 꺼도 슈퍼관리자가 아니면 생성할 수 없다 | 권한 검사 비활성화, 슈퍼관리자 아님 | 생성 | 역할 부족으로 거부 |

`rank` 값은 요청에서 정할 수 없다. 생성 시 같은 `runtime_variant`에서 가장 큰 `rank` 값에 100을
더하며, 첫 프리셋의 `rank` 값은 100이 된다. 같은 `runtime_variant`에 프리셋을 하나 더 생성하는
시나리오에서 이 간격을 검사한다.

`ui_type` 값은 요청에 별도 필드로 없으며 `ui_option` 필드에서 읽는다. `ui_option` 필드를 지정하면
`ui_type` 값이 응답에 포함되고, 필수 항목만 지정해 생성하는 시나리오처럼 `ui_option` 필드를 생략하면
`ui_type` 값도 비어 있다.

`value_type` 값이 `flag`이면 `preset_target` 값이 `args`여야 하고 `default_value` 값은 `value_type`
값에 맞아야 한다는 규칙은 생성 시나리오에 두지 않는다. 받아들이는 쪽도 거부하는 쪽도 생성 요청
타입이 판단하며, 요청 타입의 단위 테스트가 `value_type` 값마다 검사한다.

존재하지 않는 `runtime_variant_id` 값으로 생성하는 시나리오는 아직 포함하지 않는다. 프리셋의
`runtime_variant` 컬럼에 외래 키가 마이그레이션에는 있지만 ORM에는 없다. 따라서 마이그레이션으로
만든 데이터베이스에서는 요청이 거부되지만 스키마를 한 번에 만든 데이터베이스에서는 생성된다. 올바른
동작을 정한 뒤 시나리오를 작성한다.

## 조회

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| public 에서 읽는 사용자가 ID로 조회한다 | 프리셋 하나, public 조회 권한만 있음 | ID로 조회 | 해당 프리셋 전체 |
| 존재하지 않는 ID로 조회한다 | 다른 프리셋만 있음 | ID로 조회 | 권한 부족으로 거부 |
| 존재하는 ID와 존재하지 않는 ID를 함께 조회한다 | 프리셋 둘, public 조회 권한만 있음 | 세 ID를 한 번에 조회 | 요청한 순서대로 반환되며, 존재하지 않는 ID 자리에는 거부가 담긴다 |
| 빈 목록으로 조회한다 | 프리셋 하나 | 빈 ID 목록으로 조회 | 빈 응답을 반환하고 하위 계층을 호출하지 않음 |

조회는 public 에서 READ 를 검사한다. public 조회 권한만 받은 사용자의 조회가 성공하는 시나리오로
이를 검증한다. 반면 생성 요청은 슈퍼관리자가 아니면 거부된다. 존재하지 않는 ID와 닿을 수 없는 ID는
같은 이유로 거부된다.

여러 ID를 한 번에 조회할 때는 ID 조건을 지정한 검색으로 실행한다. ID마다 개별 조회하는 방식이
아니므로 존재하지 않는 ID가 있어도 요청 전체를 거부하지 않고 해당 위치에 빈 항목을 반환한다.

인증되지 않은 호출은 시나리오로 두지 않는다. 시나리오는 언제나 미리 만들어 둔 사용자로 호출한다.

## 검색

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 아무 권한도 없는 사용자가 검색한다 | 프리셋 둘, 아무 권한도 없음 | 전체 조회 | 두 프리셋이 모두 반환됨 |
| `runtime_variant_id` 필터로 검색한다 | 프리셋이 `runtime_variant` 둘에 나뉘어 있음 | `runtime_variant_id` 필터로 조회 | 해당 `runtime_variant`의 프리셋만 반환됨 |
| `runtime_version` 필터로 검색한다 | `added_version` 값과 `deprecated_version` 값이 서로 다른 프리셋 여러 개 | `runtime_version` 필터로 조회 | 해당 버전에 유효한 프리셋만 반환됨 |
| 페이지 크기를 생략한다 | 프리셋 11개 | 페이지 크기 없이 조회 | 10건을 반환하고 다음 페이지가 있음을 표시함 |

`runtime_version` 필터는 `added_version` 값 이상이고 `deprecated_version` 값 미만인 프리셋만
반환한다. `added_version` 값이 비어 있으면 하한 제한이 없고, `deprecated_version` 값이 비어 있으면
상한 제한이 없다. `runtime_version` 필터로 검색하는 시나리오에서는 `added_version` 값과
`deprecated_version` 값이 모두 있는 경우, `added_version` 값만 있는 경우, `deprecated_version`
값만 있는 경우, 어느 쪽도 없는 경우를 함께 검사한다.

## 수정

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 이름만 바꾼다 | 프리셋 하나, 슈퍼관리자 | 이름 수정 | 이름만 변경되고 나머지는 유지됨 |
| 설명을 지운다 | 설명이 있는 프리셋, 슈퍼관리자 | 설명을 비우도록 수정 | 설명이 없어짐 |
| `rank` 값을 바꾼다 | 프리셋 하나, 슈퍼관리자 | `rank` 값 수정 | `rank` 값이 변경된 노드 |
| 변경할 값을 지정하지 않는다 | 프리셋 하나, 슈퍼관리자 | 빈 수정 요청 | 아무것도 바뀌지 않은 노드 |
| 존재하지 않는 ID를 수정한다 | 다른 프리셋만 있음, 슈퍼관리자 | 이름 수정 | 대상을 찾을 수 없어 거부 |
| 아무 권한도 없는 사용자가 수정한다 | 해당 프리셋에 아무 권한도 없음 | 이름 수정 | 권한 부족으로 거부 |
| 권한 검사를 끄면 권한 없이도 수정된다 | 권한 검사 비활성화, 아무 권한도 없음 | 이름 수정 | 이름이 변경된 노드 |

수정 요청에는 `preset_target` 값이나 `value_type` 값이 빠질 수 있어 요청 타입만으로는 저장된 값과의
조합을 검증할 수 없다. 서비스가 저장된 행과 요청을 합쳐 같은 규칙을 검사하는데, 그 검사는 시나리오로
두지 않는다. 어댑터와 데이터베이스가 결과를 바꾸지 않고, 서비스의 단위 테스트가 검사한다.

`value_type` 값만 바꾸는 요청은 저장된 `default_value` 값을 다시 검사하지 않는다. 현재는
`default_value` 값이 새 `value_type` 값과 어긋난 상태로 수정된다. 이를 거부할지 정한 뒤 시나리오를
작성한다.

## 삭제

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 삭제한다 | 프리셋 하나, 슈퍼관리자 | 삭제 | 삭제한 프리셋의 ID를 담은 응답 |
| 존재하지 않는 ID를 삭제한다 | 다른 프리셋만 있음, 슈퍼관리자 | 삭제 | 대상을 찾을 수 없어 거부 |
| 아무 권한도 없는 사용자가 삭제한다 | 해당 프리셋에 아무 권한도 없음 | 삭제 | 권한 부족으로 거부 |
| 권한 검사를 끄면 권한 없이도 삭제된다 | 권한 검사 비활성화, 아무 권한도 없음 | 삭제 | 삭제한 프리셋의 ID를 담은 응답 |

이 어댑터는 soft delete를 지원하지 않는다.

## 아직 적지 않은 것

없다. 어댑터가 제공하는 `create`, `get`, `search`, `batch_load_by_ids`, `update`, `delete`가 모두 위에
있다.

`batch_load_fields`는 모든 어댑터가 상속받는 공용 메서드이며 이 엔티티 고유의 호출이 아니다.
보고서의 호출 목록에는 포함되지만 별도로 작성할 시나리오는 없다.
