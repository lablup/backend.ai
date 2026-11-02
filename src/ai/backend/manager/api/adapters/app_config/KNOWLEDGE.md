---
name: app-config-adapter-scenarios
type: reference
description: merged app config read contract, a value with no row of its own built by merging fragments in allow-list rank order, read at the caller's own scope or anonymously from the public fragments alone
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

`rank` 값을 뒤집는 시나리오가 있는 이유는, 병합 순서를 `allow_list` 항목이 결정하고 값의 소유자는
바꿀 수 없다는 것을 고정하기 위해서다. `rank` 값은 `allow_list` 항목에 있고 `fragment`에는 없다.

두 `fragment`의 값이 어떻게 합쳐지는지 — `dict` 안으로만 재귀하고 `list`와 빈 값은 통째로 바꾼다 — 는
시나리오로 두지 않는다. 어댑터와 데이터베이스가 결과를 바꾸지 않고, 서비스의 단위 테스트가 검사한다.
시나리오는 어느 `fragment`가 병합에 들어가고 어느 순서로 들어가는지만 확인한다.

`definition`조차 없는 이름의 시나리오는 `fragment`가 없는 이름과 같은 응답을 받는다. 이 조회는
`definition`을 확인하지 않고 `fragment`만 읽는다.

`allow_list` 항목이 없는 스코프의 `fragment`가 병합에 섞이는 시나리오는 두지 않는다. 그런 `fragment`는
쓸 수 없고, `allow_list` 항목이 삭제되면 `fragment`도 함께 삭제되므로 그 상황이 생기지 않는다.
`allow_list` 항목이 없는 스코프에 `fragment`를 쓰는 시나리오는 `app_config_fragment` 문서에,
`allow_list` 항목을 삭제하면 `fragment`도 함께 삭제되는 시나리오는 `app_config_allow_list` 문서에 있다.

같은 이름의 `allow_list` 항목 둘이 같은 `rank` 값을 가지면 어느 `fragment`가 우선하는지 정해져 있지
않다. 시나리오를 적기 전에 어느 쪽이 우선하는지 정한다.

`config_names` 필드가 빈 요청은 시나리오로 두지 않는다. 요청 타입이 이미 거부하므로 어댑터가 보장하는
것이 아니다.

## 공개 설정 조회

어떤 검사도 없다. 인증도 권한도 확인하지 않는다. 쓰기는 이 경로에 연결할 수 없게 막혀 있으므로, 검사 없이
호출되는 것은 조회뿐이다.

공개 `fragment`가 없는 이름과 `definition`조차 없는 이름이 같은 응답을 받는다. 그래서 이 조회로는
어떤 이름이 등록돼 있는지 알 수 없다. 그것이 검사 없는 경로가 아무것도 노출하지 않는다는
근거이므로, 공개 `fragment`가 없는 이름의 시나리오와 `definition`조차 없는 이름의 시나리오를 나란히
둔다.

로그인한 사용자의 시나리오는 이 조회가 호출자 정보를 전혀 사용하지 않는다는 것을 고정한다. 권한이
있어도 자기 `fragment`가 섞이지 않고, 없어도 거부되지 않는다.
