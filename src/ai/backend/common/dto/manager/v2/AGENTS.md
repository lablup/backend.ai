# DTO v2 — 가드레일

## 단일 진실 원천 (Single Source of Truth)

이 패키지의 DTO는 GraphQL(Strawberry)과 REST v2 API가 공유하는 스키마다.
필드 이름·enum 값·구조는 안정적으로 유지해야 한다 — 두 API가 모두 의존한다.
여기서 호환성을 깨는 변경은 GQL 타입과 REST v2 핸들러의 조율된 갱신을 요구한다.

## 네이밍

- Input(요청): `Create{Entity}Input`, `Update{Entity}Input`, `Delete{Entity}Input`, `Purge{Entity}Input`
- Node(응답): `{Entity}Node`, 중첩 서브모델: `{Entity}{Group}Info`
- Payload(뮤테이션 결과): `Create{Entity}Payload`, `Update{Entity}Payload`, `Delete{Entity}Payload`, `Purge{Entity}Payload`

## 파일 구조

도메인별: `v2/{domain}/types.py`, `request.py`, `response.py`, `__init__.py`

- `types.py` — `common/data/`의 도메인 enum re-export + DTO 전용 enum(정렬 필드, 방향)과
  중첩 서브모델(예: `PermissionSummary`) 정의
- `request.py` — Input 모델(GQL `@strawberry.input` 타입과 1:1 매핑)
- `response.py` — Node 모델(엔티티 표현)과 Payload 모델(뮤테이션 결과)
- `__init__.py` — re-export는 가능하면 쓰지 않고 모듈을 직접 import한다. 기존 단일 파일을 패키지로
  분리하면서 호환이 어려운 경우에 한해 re-export하며, 그 이후로는 가능하면 re-export하지 않는다.

## 베이스 클래스

- Input 모델: `BaseRequestModel`(`ai.backend.common.api_handlers`) 상속
- Node/Payload 모델: `BaseResponseModel`(`ai.backend.common.api_handlers`) 상속

## 중첩

- 의미상 관련된 필드는 서브모델로 묶는다(예: `UserBasicInfo`, `UserSecurityInfo`).
- 필드 5개 미만이고 논리적 그룹이 없을 때만 평평한 구조를 쓴다.
- 중첩 서브모델도 `BaseResponseModel`을 상속해야 한다.
- 직렬화를 예측 가능하게 유지하려 2단계 초과 깊은 중첩을 피한다.

## 검증

- `Field()` 제약을 쓴다: `min_length`, `max_length`, `ge`, `le`, `pattern`.
- 교차 필드/포맷 검증은 `field_validator`를 쓴다(예: 공백 제거, strip 후 비어있지 않은지 검증).
- nullable-clearable 필드: SENTINEL 패턴(센티넬 값 = "이 필드를 지움", None = "변경 없음").
- 모든 선택적 update 필드는 "변경 없음"을 뜻하도록 기본값 `None`.

## 변환

- DTO는 순수 데이터 구조 — DTO 안에 변환 로직 금지.
- 도메인 Data 타입 → DTO 변환은 Adapter 레이어(`manager/api/adapters/{domain}.py`)에서 한다.
- DTO 모듈에서 DB 모델이나 도메인 Data 타입을 직접 import 금지.
