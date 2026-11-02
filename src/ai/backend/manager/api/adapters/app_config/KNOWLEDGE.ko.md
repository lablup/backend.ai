# app_config adapter: 배경

규칙은 상위 디렉터리의 `AGENTS.md` 에 있다. 이 문서와 실행 결과가 어긋나면 문장을 먼저 의심한다.

`app_config` 는 자기 row 가 없다. 조회할 때마다 `app_config_definitions`, `app_config_allow_list`, `app_config_fragments` 의 row 를 병합해 값을 생성하고, 그 값에 대응하는 row 는 없다. 세 테이블의 역할과 병합 규칙은 `../../../services/app_config/KNOWLEDGE.md` 가 정하므로 여기서 반복하지 않는다.

adapter 의 호출은 둘이다. `my_app_configs` 는 세션의 사용자와 도메인으로 조회하고, 그 사용자 자신의 스코프에 부여된 읽기 권한을 검사한다. `public_app_configs` 는 스코프를 지정하지 않고 조회하며 검사를 실행하지 않는다. 이 호출을 보호하는 것은 검사가 아니라 조회 방식이다. 스코프를 지정하지 않으므로 공개 `app_config_fragment` row 만 병합된다.

생성하고 다시 조회하는 row 가 없으므로 성공 시나리오의 모양이 다르다. `app_config_definition`, `app_config_allow_list` 항목, `fragment` 를 미리 저장한 뒤 조회하면 병합 결과가 나온다. 응답에는 `config_name` 필드와 병합된 `config` 필드만 있고 id 와 시각은 없으며, `config` 필드는 전체를 비교한다. 생성, 조회, 삭제 시나리오는 없다. `fragment` 나 `allow_list` 항목을 삭제한 뒤 병합이 달라지는 방식은 `app_config_fragment` 와 `app_config_allow_list` adapter 문서의 삭제 절이 다룬다.

## 자기 설정 조회

`rank` 값을 뒤집는 시나리오는 병합 순서를 `allow_list` 항목이 정하고 값의 소유자는 이를 변경할 수 없다는 것을 고정한다. `rank` 값은 `fragment` 가 아니라 `allow_list` 항목에 있다.

두 `fragment` 의 값을 합치는 방식(`dict` 안으로만 재귀하고 `list` 와 빈 값은 전체를 교체)은 시나리오로 두지 않는다. adapter 와 데이터베이스가 결과를 변경하지 않고 service 단위 테스트가 검사한다. 시나리오는 어떤 `fragment` 가 병합에 들어가고 어떤 순서로 들어가는지만 확인한다.

`definition` 이 없는 이름은 `fragment` 가 없는 이름과 같은 응답을 받는다. 이 조회는 `definition` 을 확인하지 않고 `fragment` 만 읽는다.

`allow_list` 항목이 없는 스코프의 `fragment` 가 병합에 들어가는 시나리오는 두지 않는다. 그런 `fragment` 는 사용할 수 없고, `allow_list` 항목을 삭제하면 `fragment` 도 함께 삭제되므로 그 상황이 생기지 않는다. `allow_list` 항목이 없는 스코프에 `fragment` 를 쓰는 시나리오는 `app_config_fragment` 문서에, `allow_list` 항목을 삭제하면 `fragment` 도 삭제되는 시나리오는 `app_config_allow_list` 문서에 있다.

같은 이름의 `allow_list` 항목 둘이 같은 `rank` 값을 가지면 어느 `fragment` 가 우선하는지 아직 정하지 않았다. 시나리오를 작성하기 전에 이를 정한다.

`config_names` 필드가 빈 요청은 시나리오로 두지 않는다. 요청 타입이 이미 거부하므로 adapter 가 보장하는 동작이 아니다.

## 공개 설정 조회

검사를 실행하지 않는다. 인증도 권한도 검사하지 않는다. 쓰기는 이 경로에 연결할 수 없으므로 검사 없이 호출되는 것은 조회뿐이다.

공개 `fragment` 가 없는 이름과 `definition` 이 없는 이름은 같은 응답을 받는다. 그래서 이 조회로는 어떤 이름이 등록되었는지 알 수 없다. 검사 없는 경로가 아무것도 노출하지 않는다는 근거가 이것이므로, 공개 `fragment` 가 없는 이름의 시나리오와 `definition` 이 없는 이름의 시나리오를 나란히 둔다.

로그인한 사용자의 시나리오는 이 조회가 호출자 정보를 전혀 사용하지 않는다는 것을 고정한다. 권한이 있어도 자기 `fragment` 가 병합에 들어가지 않고, 권한이 없어도 거부되지 않는다.
