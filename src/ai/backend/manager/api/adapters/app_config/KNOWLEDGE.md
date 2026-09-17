---
name: app-config-adapter-scenarios
type: reference
description: what the merged app config read guarantees, as scenarios; a value with no row of its own, built by merging fragments in allow-list rank order, read either at the caller's own scope or anonymously from the public fragments alone; the tests in tests/scenario/bai_scenario/manager/app_config match these one for one
scope: src/ai/backend/manager/api/adapters/app_config
keywords: [app config, scenario, adapter, merge, rank, anonymous, rbac]
generated:
  by: claude-code/opus-5
  at: 2026-09-11
status: draft
---
# app_config 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다. 여기 적힌 내용과 실행 결과가 어긋나면 문장 쪽을 먼저
의심한다.

`app_config`는 자체 행이 없다. 조회할 때마다 `app_config_definitions`, `app_config_allow_list`,
`app_config_fragments`의 행을 병합해 만들어지는 값이고, 어느 행도 그 값에 대응하지 않는다. 그 세
테이블의 역할과 병합 규칙은
`../../../services/app_config/KNOWLEDGE.md`가 정하므로 여기서 되풀이하지 않는다.

이 어댑터의 호출은 `my_app_configs`와 `public_app_configs` 둘뿐이다. `my_app_configs`는 세션의
사용자와 도메인으로 조회하고, 그 사용자 자신의 스코프에 부여된 읽기 권한을 검사한다.
`public_app_configs`는 아무 스코프도 지정하지 않고 조회하며, 어떤 검사도 없다. 이 호출을 보호하는
것은 검사가 아니라 조회 방식 자체다 — 스코프를 지정하지 않으므로 공개 `app_config_fragment`만
병합된다.

행이 없으므로 다른 어댑터의 시나리오와 형태가 다르다. 성공 시나리오는 "생성한 뒤 조회한다"가
아니라 "`app_config_definition`·`app_config_allow_list` 항목·`fragment`를 미리 만들어 두고 조회하면
병합 결과가 이렇게 나온다"이다. 응답은 `config_name` 필드와 병합된 `config` 필드 둘뿐이라 id도 시각도
없고, `config` 필드는 통째로 비교한다. 생성·조회·삭제 시나리오도 없다. `fragment`나 `allow_list` 항목을
삭제한 뒤 병합이 어떻게 달라지는지는 `app_config_fragment`·`app_config_allow_list` 어댑터 문서의
삭제 절이 다룬다.

## 자기 설정 조회

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| `fragment`가 하나도 없는 이름을 조회한다 | `definition` 하나, `allow_list` 항목도 `fragment`도 없음, 자기 스코프에 읽기 권한 있음 | 그 이름 하나로 조회 | 그 이름 하나, `config`는 빈 값. 응답에서 빠지지 않는다 |
| `definition`조차 없는 이름을 조회한다 | `definition` 없음, 읽기 권한 있음 | 이름 하나로 조회 | 빈 `config`. `definition`이 없다고 거부되지 않는다 |
| 공개 `fragment`만 있는 이름을 조회한다 | `definition` 하나, 공개 `allow_list` 항목 하나, 공개 `fragment` 하나, 읽기 권한 있음 | 조회 | `config`가 공개 `fragment`의 값과 같다 |
| 자기 `fragment`가 도메인 `fragment`를 덮어쓴다 | 도메인·사용자 `allow_list` 항목의 `rank` 값이 기본값, 겹치는 키를 가진 도메인 `fragment`와 자기 `fragment`, 읽기 권한 있음 | 조회 | 겹치는 키는 자기 값, 겹치지 않는 키는 양쪽 모두 남는다 |
| 도메인 `fragment`가 공개 `fragment`를 덮어쓴다 | 공개·도메인 `allow_list` 항목의 `rank` 값이 기본값, 겹치는 키를 가진 공개 `fragment`와 도메인 `fragment`, 읽기 권한 있음 | 조회 | 겹치는 키는 도메인 값 |
| 관리자가 `rank` 값을 뒤집으면 도메인 `fragment`가 자기 `fragment`를 덮어쓴다 | 도메인 `allow_list` 항목의 `rank` 값이 사용자 항목보다 큼, 겹치는 키를 가진 도메인 `fragment`와 자기 `fragment`, 읽기 권한 있음 | 조회 | 겹치는 키는 도메인 값 |
| 다른 사용자의 `fragment`는 섞이지 않는다 | 도메인 하나, 사용자 둘, 사용자 `allow_list` 항목 하나, 두 사용자 각자의 `fragment`, 읽기 권한 있음 | 조회 | 자기 `fragment`의 값만 (실행에서 뺌, 아래 참고) |
| 다른 도메인의 `fragment`는 섞이지 않는다 | 도메인 둘, 각 도메인의 `fragment`, 도메인 `allow_list` 항목 하나, 읽기 권한 있음 | 조회 | 자기 도메인 `fragment`의 값만 |
| 여러 이름을 한 번에 조회하면 요청한 순서대로 반환된다 | `definition` 셋, 각각의 `allow_list` 항목과 `fragment`, 읽기 권한 있음 | 이름 셋으로 조회 | 셋, 요청 순서대로, 각각 자기 병합 결과 |
| 같은 이름을 두 번 지정하면 두 번 반환된다 | `definition` 하나, `fragment` 하나, 읽기 권한 있음 | 같은 이름 둘로 조회 | 둘, 같은 값 |
| 읽기 권한이 없는 사용자가 조회한다 | `definition` 하나, 공개 `fragment` 하나, 자기 스코프에 권한 없음 | 조회 | 권한 부족으로 거부 |
| 권한 검사를 끄면 권한 없이도 조회된다 | 권한 검사 비활성화, 권한 없음 | 조회 | 병합 결과가 반환된다 |

`rank` 값을 뒤집는 시나리오가 있는 이유는, 병합 순서를 `allow_list` 항목이 결정하고 값의 소유자는
바꿀 수 없다는 것을 고정하기 위해서다. `rank` 값은 `allow_list` 항목에 있고 `fragment`에는 없다.

두 `fragment`의 값이 어떻게 합쳐지는지 — `dict` 안으로만 재귀하고 `list`와 빈 값은 통째로 바꾼다 — 는
시나리오로 두지 않는다. 어댑터와 데이터베이스가 결과를 바꾸지 않고, 서비스의 단위 테스트가 검사한다.
시나리오는 어느 `fragment`가 병합에 들어가고 어느 순서로 들어가는지만 확인한다.

`definition`조차 없는 이름의 시나리오는 `fragment`가 없는 이름과 같은 응답을 받는다. 이 조회는
`definition`을 확인하지 않고 `fragment`만 읽는다.

다른 사용자의 `fragment`가 섞이지 않는 시나리오는 현재 코드에서 실패하므로 실행에서 뺐다 (BA-7934).
도메인 스코프의 `fragment`를 고르는 조건이 도메인에 속한 모든 `fragment`를 포함하는데, 사용자는 자기
도메인에 속하므로 같은 도메인 사용자들의 `fragment`까지 그 조건에 포함된다. 도메인 조건은 도메인
스코프에 만든 `fragment`만, 사용자 조건은 그 사용자 스코프에 만든 `fragment`만 골라야 하고,
시나리오의 기대 결과는 그 기준으로 적었다. 고쳐지면 실행에 되돌린다.

`allow_list` 항목이 없는 스코프의 `fragment`가 병합에 섞이는 시나리오는 두지 않는다. 그런 `fragment`는
쓸 수 없고, `allow_list` 항목이 삭제되면 `fragment`도 함께 삭제되므로 그 상황이 생기지 않는다.
`allow_list` 항목이 없는 스코프에 `fragment`를 쓰는 시나리오는 `app_config_fragment` 문서에,
`allow_list` 항목을 삭제하면 `fragment`도 함께 삭제되는 시나리오는 `app_config_allow_list` 문서에 있다.

같은 이름의 `allow_list` 항목 둘이 같은 `rank` 값을 가지면 어느 `fragment`가 우선하는지 정해져 있지
않다. 시나리오를 적기 전에 어느 쪽이 우선하는지 정한다.

`config_names` 필드가 빈 요청은 시나리오로 두지 않는다. 요청 타입이 이미 거부하므로 어댑터가 보장하는
것이 아니다.

## 공개 설정 조회

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 로그인하지 않은 호출자가 공개 값을 조회한다 | `definition` 하나, 공개·도메인·사용자 `allow_list` 항목 셋, `fragment` 셋 | 이름 하나로 조회 | `config`가 공개 `fragment`의 값과 같다. 도메인과 사용자 `fragment`는 섞이지 않는다 |
| 공개 `fragment`가 없는 이름을 조회한다 | `definition` 하나, 사용자 `fragment`만 있음 | 조회 | 빈 `config` |
| `definition`조차 없는 이름을 조회한다 | `definition` 없음 | 조회 | 빈 `config` |
| 로그인한 사용자가 조회해도 같은 응답을 받는다 | 로그인하지 않은 호출자의 시나리오와 같은 공개·도메인·사용자 `fragment` 셋, 아무 권한도 없는 사용자 | 조회 | 공개 `fragment`의 값만 |
| 여러 이름을 한 번에 조회하면 요청한 순서대로 반환된다 | `definition` 셋, 각각의 공개 `fragment` | 이름 셋으로 조회 | 셋, 요청 순서대로 |

어떤 검사도 없다. 인증도 권한도 확인하지 않는다. 쓰기는 이 경로에 연결할 수 없게 막혀 있으므로, 검사 없이
호출되는 것은 조회뿐이다.

공개 `fragment`가 없는 이름과 `definition`조차 없는 이름이 같은 응답을 받는다. 그래서 이 조회로는
어떤 이름이 등록돼 있는지 알 수 없다. 그것이 검사 없는 경로가 아무것도 노출하지 않는다는
근거이므로, 공개 `fragment`가 없는 이름의 시나리오와 `definition`조차 없는 이름의 시나리오를 나란히
둔다.

로그인한 사용자의 시나리오는 이 조회가 호출자 정보를 전혀 사용하지 않는다는 것을 고정한다. 권한이
있어도 자기 `fragment`가 섞이지 않고, 없어도 거부되지 않는다.

## 아직 적지 않은 것

어댑터가 제공하는 `my_app_configs`와 `public_app_configs`가 모두 위에 있다. 실행 결과에 남는
`batch_load_fields`는 어댑터 공통 기반 클래스가 물려주는 필드 읽기이고, 이 엔티티는 필드를 갖지
않아 호출할 일이 없다.
