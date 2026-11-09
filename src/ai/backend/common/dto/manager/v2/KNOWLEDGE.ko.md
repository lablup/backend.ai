# DTO v2: 배경

> 규칙은 같은 디렉터리의 `AGENTS.md` 에 있다.

## 이 패키지가 있는 이유

v2 연산 모두의 단일 wire schema 다. GraphQL type, REST v2 handler, client SDK 가 모두 여기에서 파생한다. field 를 정의하는 곳을 하나로 모아 각 표면이 갈라지지 않게 한다.

## schema 는 additive-only 다

- 이 schema 는 WebUI(GQL)와 CLI(REST)를 동시에 지원한다. 어느 표면도 breaking change 를 혼자 흡수할 수 없다.
- 릴리스 version branch 가 additive-only 정책을 강제한다.
- schema inspector 는 합성된 supergraph 를 통해서만 v2 type 을 본다. 이름과 type 변경이 늦게, 큰 비용으로 드러난다.
- field 를 추가하고 오래된 field 를 지원 중단한다. field 의 이름과 용도를 변경하지 않는다.

## update field 는 `Unset` 으로 생략과 null 을 구분한다

- update field 는 `X | None | Unset = Field(default=UNSET)` 이다. 생략하면 변경 없음, null 이면 비움, 값이면 설정.
- 생략한 field 는 wire 에도 JSON schema 에도 아무것도 두지 않는다.
- column 이 null 과 unset 중 무엇을 따를지에 대한 결정은 adapter 가 한다. 규칙 표는 `../../AGENTS.md` 의 "Update" 절에, sentinel 의 근거는 [`../../../tristate/KNOWLEDGE.md`](../../../tristate/KNOWLEDGE.md) 에 있다.
- 레거시 `Sentinel` enum 으로 선언된 field 는 도메인 하나씩 이관 중이다. 새로 추가하지 않는다.
