# User Resource Policy Service Test Scenarios

## 서비스 개요
User Resource Policy 서비스는 Backend.AI에서 개별 사용자 레벨의 리소스 정책을 관리합니다.
사용자별 스토리지 할당, 커스텀 이미지 제한, 모델 서빙 세션 제한 등을 설정합니다.

## 주요 기능 목록
1. Create User Resource Policy - 새로운 사용자 리소스 정책 생성
   - Action: `CreateUserResourcePolicyAction`
   - Result: `CreateUserResourcePolicyActionResult`
2. Modify User Resource Policy - 기존 정책 수정
   - Action: `ModifyUserResourcePolicyAction`
   - Result: `ModifyUserResourcePolicyActionResult`
3. Delete User Resource Policy - 정책 삭제
   - Action: `DeleteUserResourcePolicyAction`
   - Result: `DeleteUserResourcePolicyActionResult`

## 테스트 시나리오

### 1. Create User Resource Policy

#### 기능 설명
새로운 사용자 리소스 정책을 생성합니다.

#### 테스트 케이스

##### 1.1 정상적인 정책 생성
- **입력값**: 
  - `name`: "standard-user-policy"
  - `max_vfolder_count`: 20
  - `max_quota_scope_size`: 107374182400 (100GB)
  - `max_session_count_per_model_session`: 3
  - `max_customized_image_count`: 5
- **기대 출력값**: 
  - 생성된 정책 정보
  - 모든 설정값 정확히 저장
- **동작 근거**: 
  - 일반 사용자용 표준 정책

##### 1.2 ML 엔지니어용 정책
- **입력값**: 
  - `name`: "ml-engineer-policy"
  - `max_vfolder_count`: 50
  - `max_quota_scope_size`: 1099511627776 (1TB)
  - `max_session_count_per_model_session`: 10
  - `max_customized_image_count`: 20
- **기대 출력값**: 
  - ML 작업에 적합한 높은 제한값
- **동작 근거**: 
  - 고급 사용자 요구사항


##### 1.4 중복된 정책 이름
- **입력값**: 
  - `name`: "existing-user-policy" (이미 존재)
- **기대 출력값**: 
  - `DuplicatePolicyName` 예외
- **동작 근거**: 
  - 정책 이름은 고유해야 함

##### 1.5 음수 값 설정
- **입력값**: 
  - `max_customized_image_count`: -1
- **기대 출력값**: 
  - 검증 에러
- **동작 근거**: 
  - 음수 제한은 무의미

### 2. Modify User Resource Policy

#### 기능 설명
기존 사용자 리소스 정책을 수정합니다.

#### 테스트 케이스

##### 2.1 부분 업데이트
- **입력값**: 
  - `name`: "standard-user-policy"
  - `modifier`: {"max_customized_image_count": 10}
- **기대 출력값**: 
  - 커스텀 이미지 제한만 업데이트
  - 나머지 필드는 유지
- **동작 근거**: 
  - 선택적 필드 업데이트

##### 2.2 모델 서빙 제한 조정
- **입력값**: 
  - `name`: "ml-engineer-policy"
  - `modifier`: {"max_session_count_per_model_session": 20}
- **기대 출력값**: 
  - 모델 서빙 세션 제한 증가
- **동작 근거**: 
  - 서비스 확장 요구

##### 2.3 스토리지 할당량 축소
- **입력값**: 
  - `name`: "overuse-user-policy"
  - `modifier`: {"max_quota_scope_size": 53687091200} (50GB)
- **기대 출력값**: 
  - 스토리지 할당량 감소
  - 기존 사용량 초과 시 경고
- **동작 근거**: 
  - 리소스 사용 제한

##### 2.4 null 값으로 초기화
- **입력값**: 
  - `modifier`: {"max_session_count_per_model_session": null}
- **기대 출력값**: 
  - 모델 서빙 제한 해제
- **동작 근거**: 
  - TriState를 통한 null 설정

##### 2.5 deprecated 필드 수정
- **입력값**: 
  - `modifier`: {"max_vfolder_size": 5368709120} (5GB)
- **기대 출력값**: 
  - 값은 저장됨
- **동작 근거**: 
  - 하위 호환성 유지

### 3. Delete User Resource Policy

#### 기능 설명
사용자 리소스 정책을 삭제합니다.

#### 테스트 케이스

##### 3.1 정상적인 정책 삭제
- **입력값**: 
  - `name`: "unused-user-policy"
- **기대 출력값**: 
  - 삭제된 정책 정보 반환
- **동작 근거**: 
  - 사용하지 않는 정책 정리

##### 3.2 사용 중인 정책 삭제
- **입력값**: 
  - `name`: "active-user-policy" (사용자에게 할당됨)
- **기대 출력값**: 
  - `PolicyInUse` 예외 또는 경고
- **동작 근거**: 
  - 참조 무결성 보호


##### 3.4 존재하지 않는 정책 삭제
- **입력값**: 
  - `name`: "non-existent-user-policy"
- **기대 출력값**: 
  - `ObjectNotFound` 예외
- **동작 근거**: 
  - 없는 정책은 삭제 불가


## 공통 에러 케이스


