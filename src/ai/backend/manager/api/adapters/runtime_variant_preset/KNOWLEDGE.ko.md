# runtime_variant_preset adapter: 배경

규칙은 상위 디렉터리의 `AGENTS.md` 에 있다. 이 문서와 실행 결과가 어긋나면 문장을 먼저 검토한다.

`runtime_variant_preset` 엔티티는 `runtime_variant` 하나를 column 으로 참조하지만 그 스코프 안에서 생성되지는 않는다. row 는 global 과 public 양쪽에 속한다. 생성은 호출한 사용자가 superadmin 인지 검사한다. 수정과 삭제에 필요한 프리셋별 권한은 global 에서만 나오므로 superadmin 만 통과한다. 조회와 검색은 public 에서 READ 를 검사한다. 모든 계정이 public 소속 역할을 자동으로 받으므로 로그인한 사용자는 모두 읽을 수 있다.

`runtime_variant` adapter 의 시나리오는 `../runtime_variant/KNOWLEDGE.md` 에 있다.

## 생성

`rank` 값은 요청에서 정할 수 없다. 생성 시 같은 `runtime_variant` 에서 가장 큰 `rank` 값에 100을 더하며, 첫 프리셋의 `rank` 값은 100이 된다. 같은 `runtime_variant` 에 프리셋을 하나 더 생성하는 시나리오에서 이 간격을 검사한다.

`ui_type` 값은 요청에 별도 필드가 없으며 `ui_option` 필드에서 읽는다. `ui_option` 필드를 지정하면 `ui_type` 값이 응답에 포함되고, 필수 항목만 지정해 생성하는 시나리오처럼 `ui_option` 필드를 생략하면 `ui_type` 값도 비어 있다.

`value_type` 값이 `flag` 이면 `preset_target` 값이 `args` 여야 하고 `default_value` 값은 `value_type` 값에 맞아야 한다는 규칙은 생성 시나리오에 두지 않는다. 수락과 거부를 모두 생성 요청 타입이 판단하며, 요청 타입의 단위 테스트가 `value_type` 값마다 검사한다.

존재하지 않는 `runtime_variant_id` 값으로 생성하는 시나리오는 아직 포함하지 않는다. 프리셋의 `runtime_variant` column 에 외래 키가 마이그레이션에는 있지만 ORM 에는 없다. 따라서 마이그레이션으로 생성한 데이터베이스에서는 요청이 거부되지만 스키마를 한 번에 생성한 데이터베이스에서는 row 가 생성된다. 올바른 동작을 정한 뒤 시나리오를 작성한다.

## 조회

조회는 public 에서 READ 를 검사한다. public 조회 권한만 받은 사용자의 조회가 성공하는 시나리오로 이를 검증한다. 반면 생성 요청은 superadmin 이 아니면 거부된다. 존재하지 않는 ID 와 접근할 수 없는 ID 는 같은 이유로 거부된다.

여러 ID 를 한 번에 조회할 때는 ID 조건을 지정한 검색으로 실행한다. ID 마다 개별 조회하는 방식이 아니므로 존재하지 않는 ID 가 있어도 요청 전체를 거부하지 않고 해당 위치에 빈 항목을 반환한다.

인증되지 않은 호출은 시나리오로 두지 않는다. 시나리오는 항상 미리 저장한 사용자로 호출한다.

## 검색

`runtime_version` 필터는 `runtime_version` 값이 `added_version` 값 이상이고 `deprecated_version` 값 미만인 프리셋만 반환한다. `added_version` 값이 비어 있으면 하한 제한이 없고, `deprecated_version` 값이 비어 있으면 상한 제한이 없다. `runtime_version` 필터로 검색하는 시나리오에서는 `added_version` 값과 `deprecated_version` 값이 모두 있는 경우, `added_version` 값만 있는 경우, `deprecated_version` 값만 있는 경우, 어느 쪽도 없는 경우를 함께 검사한다.

## 수정

수정 요청에는 `preset_target` 값이나 `value_type` 값이 빠질 수 있어 요청 타입만으로는 저장된 값과의 조합을 검증할 수 없다. service 가 저장된 row 와 요청을 합쳐 같은 규칙을 검사하는데, 그 검사는 시나리오로 두지 않는다. adapter 와 데이터베이스가 결과를 변경하지 않고 service 의 단위 테스트가 검사한다.

`value_type` 값만 변경하는 요청은 저장된 `default_value` 값을 다시 검사하지 않는다. 현재는 `default_value` 값이 새 `value_type` 값과 어긋난 상태로 수정된다. 이를 거부하는 방안을 정한 뒤 시나리오를 작성한다.

## 여럿 수정

여럿 수정도 단건 수정과 같은 검사를 프리셋마다 한다. 검사에 걸린 프리셋은 그 이유로 실패 목록에 오고 나머지는 수정된다.

## 영구 삭제

여럿 연산은 호출 전체를 거부하지 않는다. 처리한 프리셋은 처리된 목록에, 처리하지 못한 항목은 ID 와 이유를 실패 목록에 담는다.

이 adapter 는 row 를 남기는 삭제를 지원하지 않는다.
