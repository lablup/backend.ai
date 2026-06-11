# Common DTO — 가드레일

> 이 패키지는 모든 컴포넌트가 공유한다. 여기 변경은 manager, agent, storage, client SDK에 동시에
> 영향을 준다 — 필드 수정 전 모든 호출자를 확인한다.

## 목적

여러 backend.ai 컴포넌트(manager, agent, storage, client SDK)가 공유하는 DTO. 단일 컴포넌트에서만
쓰는 DTO는 그 컴포넌트의 `dto/` 디렉터리에 둔다.

## 디렉터리 구조

대상 컴포넌트별로 둔다: `common/dto/{manager|agent|storage|clients|internal}/`.

## 규칙

- 모든 DTO는 `BaseRequestModel`(Pydantic v2)을 상속해야 한다.
- 비즈니스 로직 금지 — 검증·직렬화만.
- 필드 수정 전 컴포넌트 전반의 모든 호출자를 확인한다.
- `v2/` DTO만 쓴다(예: `common/dto/manager/v2/`). `v2/` 밖의 DTO는 deprecated이며 새 코드에서 쓰지 않는다.
