# KeyPair Resource Policy Service Test Scenarios

## 서비스 개요
KeyPair Resource Policy 서비스는 Backend.AI에서 API 액세스 키(KeyPair)에 적용되는 리소스 정책을 관리합니다.
각 정책은 컴퓨팅 리소스 사용량, 세션 제한, 스토리지 할당 등을 제어합니다.

## 주요 기능 목록
1. Create KeyPair Resource Policy - 새로운 키페어 리소스 정책 생성
   - Action: `CreateKeyPairResourcePolicyAction`
   - Result: `CreateKeyPairResourcePolicyActionResult`
2. Modify KeyPair Resource Policy - 기존 정책 수정
   - Action: `ModifyKeyPairResourcePolicyAction`
   - Result: `ModifyKeyPairResourcePolicyActionResult`
3. Delete KeyPair Resource Policy - 정책 삭제
   - Action: `DeleteKeyPairResourcePolicyAction`
   - Result: `DeleteKeyPairResourcePolicyActionResult`

## 테스트 시나리오

### 1. Create KeyPair Resource Policy

#### 기능 설명
새로운 키페어 리소스 정책을 생성합니다.

#### 테스트 케이스

##### 1.1 정상적인 정책 생성
- **입력값**: 
  - `name`: "dev-policy"
  - `allowed_vfolder_hosts`: ["storage1", "storage2"]
  - `default_for_unspecified`: "LIMITED"
  - `idle_timeout`: 3600
  - `max_concurrent_sessions`: 5
  - `max_containers_per_session`: 3
  - `max_pending_session_count`: 10
  - `max_pending_session_resource_slots`: {"cpu": "10", "memory": "64G"}
  - `max_session_lifetime`: 86400
  - `total_resource_slots`: {"cpu": "50", "memory": "256G", "gpu": "4"}
- **기대 출력값**: 
  - 생성된 정책 정보
  - 모든 설정값 정확히 저장
- **동작 근거**: 
  - 개발자용 표준 정책 설정

##### 1.2 최소 설정 정책
- **입력값**: 
  - `name`: "minimal-policy"
  - 나머지 필드는 기본값 사용
- **기대 출력값**: 
  - 이름만 설정된 정책 생성
  - 나머지는 시스템 기본값
- **동작 근거**: 
  - 선택적 필드 지원

##### 1.3 중복된 정책 이름
- **입력값**: 
  - `name`: "existing-policy" (이미 존재)
- **기대 출력값**: 
  - `DuplicatePolicyName` 예외
- **동작 근거**: 
  - 정책 이름은 고유해야 함

##### 1.4 잘못된 리소스 슬롯 형식
- **입력값**: 
  - `total_resource_slots`: {"invalid": "format"}
- **기대 출력값**: 
  - 형식 검증 에러
- **동작 근거**: 
  - 유효한 리소스 타입만 허용

##### 1.5 음수 값 설정
- **입력값**: 
  - `max_concurrent_sessions`: -1
  - `idle_timeout`: -3600
- **기대 출력값**: 
  - 검증 에러
- **동작 근거**: 
  - 음수 제한은 무의미

### 2. Modify KeyPair Resource Policy

#### 기능 설명
기존 키페어 리소스 정책을 수정합니다.

#### 테스트 케이스

##### 2.1 부분 업데이트
- **입력값**: 
  - `name`: "dev-policy"
  - `modifier`: {"max_concurrent_sessions": 10}
- **기대 출력값**: 
  - 해당 필드만 업데이트
  - 나머지 필드는 유지
- **동작 근거**: 
  - 선택적 필드 업데이트

##### 2.2 리소스 슬롯 전체 변경
- **입력값**: 
  - `name`: "prod-policy"
  - `modifier`: {"total_resource_slots": {"cpu": "100", "memory": "512G", "gpu": "8"}}
- **기대 출력값**: 
  - 전체 리소스 슬롯 교체
- **동작 근거**: 
  - 리소스 할당 조정

##### 2.3 null 값으로 초기화
- **입력값**: 
  - `modifier`: {"max_session_lifetime": null, "idle_timeout": null}
- **기대 출력값**: 
  - 해당 필드들 null로 설정
  - 무제한 의미
- **동작 근거**: 
  - TriState를 통한 null 설정

##### 2.4 존재하지 않는 정책
- **입력값**: 
  - `name`: "non-existent-policy"
- **기대 출력값**: 
  - `ObjectNotFound` 예외
- **동작 근거**: 
  - 존재하는 정책만 수정 가능

##### 2.5 deprecated 필드 수정
- **입력값**: 
  - `modifier`: {"max_vfolder_size": 1000000}
- **기대 출력값**: 
  - 경고 메시지 (선택적)
  - 값은 저장됨
- **동작 근거**: 
  - 하위 호환성 유지

### 3. Delete KeyPair Resource Policy

#### 기능 설명
키페어 리소스 정책을 삭제합니다.

#### 테스트 케이스

##### 3.1 정상적인 정책 삭제
- **입력값**: 
  - `name`: "unused-policy"
- **기대 출력값**: 
  - 삭제된 정책 정보 반환
- **동작 근거**: 
  - 사용하지 않는 정책 정리

##### 3.2 사용 중인 정책 삭제
- **입력값**: 
  - `name`: "active-policy" (키페어에 할당됨)
- **기대 출력값**: 
  - `PolicyInUse` 예외 또는 경고
- **동작 근거**: 
  - 참조 무결성 보호

##### 3.3 시스템 기본 정책 삭제
- **입력값**: 
  - `name`: "default" (시스템 기본 정책)
- **기대 출력값**: 
  - `SystemPolicyNotDeletable` 예외
- **동작 근거**: 
  - 시스템 정책 보호

##### 3.4 존재하지 않는 정책 삭제
- **입력값**: 
  - `name`: "non-existent-policy"
- **기대 출력값**: 
  - `ObjectNotFound` 예외
- **동작 근거**: 
  - 없는 정책은 삭제 불가

## 정책 적용 시나리오

### 리소스 제한 계층
1. **세션 생성 시 검증**
   - total_resource_slots 초과 여부
   - max_concurrent_sessions 도달 여부
   - max_pending_session_count 확인

2. **런타임 제한**
   - idle_timeout 경과 시 세션 종료
   - max_session_lifetime 도달 시 강제 종료

3. **스토리지 제한**
   - allowed_vfolder_hosts 외 접근 차단
   - max_vfolder_count 초과 방지

### 정책 우선순위
1. 키페어에 직접 할당된 정책
2. 사용자 기본 정책
3. 도메인 기본 정책
4. 시스템 기본 정책

## 공통 에러 케이스

### 데이터베이스 제약 위반
- **상황**: 고유 제약조건 위반
- **기대 동작**: 
  - IntegrityError 변환
  - 의미 있는 에러 메시지

### 동시성 문제
- **상황**: 동일 정책 동시 수정
- **기대 동작**: 
  - 트랜잭션 재시도
  - 최종 일관성 보장

### 순환 참조
- **상황**: 정책 A가 B 참조, B가 A 참조
- **기대 동작**: 
  - 순환 참조 감지
  - 생성/수정 차단

