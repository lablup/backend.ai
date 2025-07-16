# Project Resource Policy Service Test Scenarios

## 서비스 개요
Project Resource Policy 서비스는 Backend.AI에서 프로젝트(그룹) 레벨의 리소스 정책을 관리합니다.
프로젝트별로 스토리지와 네트워크 리소스 제한을 설정하여 팀 단위의 리소스 관리를 지원합니다.

## 주요 기능 목록
1. Create Project Resource Policy - 새로운 프로젝트 리소스 정책 생성
   - Action: `CreateProjectResourcePolicyAction`
   - Result: `CreateProjectResourcePolicyActionResult`
2. Modify Project Resource Policy - 기존 정책 수정
   - Action: `ModifyProjectResourcePolicyAction`
   - Result: `ModifyProjectResourcePolicyActionResult`
3. Delete Project Resource Policy - 정책 삭제
   - Action: `DeleteProjectResourcePolicyAction`
   - Result: `DeleteProjectResourcePolicyActionResult`

## 테스트 시나리오

### 1. Create Project Resource Policy

#### 기능 설명
새로운 프로젝트 리소스 정책을 생성합니다.

#### 테스트 케이스

##### 1.1 정상적인 정책 생성
- **입력값**: 
  - `name`: "team-research-policy"
  - `max_vfolder_count`: 100
  - `max_quota_scope_size`: 1099511627776 (1TB)
  - `max_network_count`: 5
- **기대 출력값**: 
  - 생성된 정책 정보
  - 모든 설정값 정확히 저장
- **동작 근거**: 
  - 연구팀용 표준 정책 설정

##### 1.2 최소 설정 정책
- **입력값**: 
  - `name`: "minimal-project-policy"
  - 나머지 필드는 기본값 사용
- **기대 출력값**: 
  - 이름만 설정된 정책 생성
  - 나머지는 null 또는 시스템 기본값
- **동작 근거**: 
  - 선택적 필드 지원

##### 1.3 중복된 정책 이름
- **입력값**: 
  - `name`: "existing-project-policy" (이미 존재)
- **기대 출력값**: 
  - `DuplicatePolicyName` 예외
- **동작 근거**: 
  - 정책 이름은 고유해야 함

##### 1.4 음수 값 설정
- **입력값**: 
  - `max_vfolder_count`: -1
  - `max_network_count`: -5
- **기대 출력값**: 
  - 검증 에러
- **동작 근거**: 
  - 음수 제한은 무의미

##### 1.5 매우 큰 할당량
- **입력값**: 
  - `max_quota_scope_size`: 1125899906842624 (1PB)
- **기대 출력값**: 
  - 정책 생성 성공
  - 시스템 제한 내에서 허용
- **동작 근거**: 
  - 대규모 프로젝트 지원

### 2. Modify Project Resource Policy

#### 기능 설명
기존 프로젝트 리소스 정책을 수정합니다.

#### 테스트 케이스

##### 2.1 부분 업데이트
- **입력값**: 
  - `name`: "team-research-policy"
  - `modifier`: {"max_vfolder_count": 200}
- **기대 출력값**: 
  - vfolder 수 제한만 업데이트
  - 나머지 필드는 유지
- **동작 근거**: 
  - 선택적 필드 업데이트

##### 2.2 스토리지 할당량 증가
- **입력값**: 
  - `name`: "growing-team-policy"
  - `modifier`: {"max_quota_scope_size": 2199023255552} (2TB)
- **기대 출력값**: 
  - 스토리지 할당량 업데이트
- **동작 근거**: 
  - 팀 성장에 따른 할당량 조정

##### 2.3 null 값으로 초기화
- **입력값**: 
  - `modifier`: {"max_network_count": null}
- **기대 출력값**: 
  - 네트워크 제한 해제
- **동작 근거**: 
  - TriState를 통한 null 설정

##### 2.4 존재하지 않는 정책
- **입력값**: 
  - `name`: "non-existent-project-policy"
- **기대 출력값**: 
  - `ObjectNotFound` 예외
- **동작 근거**: 
  - 존재하는 정책만 수정 가능

##### 2.5 deprecated 필드 수정
- **입력값**: 
  - `modifier`: {"max_vfolder_size": 10737418240} (10GB)
- **기대 출력값**: 
  - 경고 메시지 (선택적)
  - 값은 저장됨
- **동작 근거**: 
  - 하위 호환성 유지

### 3. Delete Project Resource Policy

#### 기능 설명
프로젝트 리소스 정책을 삭제합니다.

#### 테스트 케이스

##### 3.1 정상적인 정책 삭제
- **입력값**: 
  - `name`: "unused-project-policy"
- **기대 출력값**: 
  - 삭제된 정책 정보 반환
- **동작 근거**: 
  - 사용하지 않는 정책 정리

##### 3.2 사용 중인 정책 삭제
- **입력값**: 
  - `name`: "active-project-policy" (프로젝트에 할당됨)
- **기대 출력값**: 
  - `PolicyInUse` 예외 또는 경고
- **동작 근거**: 
  - 참조 무결성 보호


##### 3.4 존재하지 않는 정책 삭제
- **입력값**: 
  - `name`: "non-existent-project-policy"
- **기대 출력값**: 
  - `ObjectNotFound` 예외
- **동작 근거**: 
  - 없는 정책은 삭제 불가


## 공통 에러 케이스


