# User Service Test Scenarios

## 서비스 개요
User 서비스는 Backend.AI의 사용자 계정 관리를 담당하는 핵심 서비스입니다.
사용자 생성, 수정, 삭제, 리소스 정리 및 사용량 통계 기능을 제공합니다.

## 주요 기능 목록
1. Create User - 새로운 사용자 계정 생성
   - Action: `CreateUserAction`
   - Result: `CreateUserActionResult`
2. Modify User - 사용자 정보 및 권한 수정
   - Action: `ModifyUserAction`
   - Result: `ModifyUserActionResult`
3. Delete User - 사용자 소프트 삭제
   - Action: `DeleteUserAction`
   - Result: `DeleteUserActionResult`
4. Purge User - 사용자 및 관련 리소스 영구 삭제
   - Action: `PurgeUserAction`
   - Result: `PurgeUserActionResult`
5. User Month Stats - 사용자 월간 사용량 통계
   - Action: `UserMonthStatsAction`
   - Result: `UserMonthStatsActionResult`
6. Admin Month Stats - 시스템 전체 월간 통계
   - Action: `AdminMonthStatsAction`
   - Result: `AdminMonthStatsActionResult`

## 테스트 시나리오

### 1. Create User

#### 기능 설명
새로운 사용자 계정을 생성하고 기본 키페어를 자동 생성합니다.

#### 테스트 케이스

##### 1.1 정상적인 사용자 생성
- **입력값**: 
  - `email`: "newuser@example.com"
  - `password`: "SecurePass123!"
  - `username`: "newuser"
  - `full_name`: "New User"
  - `role`: "user"
  - `domain_name`: "default"
  - `group_ids`: ["default-group"]
  - `resource_policy`: "default-user-policy"
- **기대 출력값**: 
  - 생성된 사용자 UUID
  - 자동 생성된 키페어 정보
  - 상태: ACTIVE
- **동작 근거**: 
  - 표준 사용자 등록 프로세스

##### 1.2 관리자 권한 사용자
- **입력값**: 
  - `email`: "admin@example.com"
  - `role`: "admin"
  - `domain_name`: "research"
  - `sudo_session_enabled`: true
- **기대 출력값**: 
  - 도메인 관리자 권한 부여
  - sudo 세션 활성화
- **동작 근거**: 
  - 권한 있는 사용자 생성

##### 1.3 중복 이메일
- **입력값**: 
  - `email`: "existing@example.com" (이미 존재)
- **기대 출력값**: 
  - `DuplicateEmail` 예외
- **동작 근거**: 
  - 이메일은 고유 식별자

##### 1.4 잘못된 이메일 형식
- **입력값**: 
  - `email`: "invalid-email"
- **기대 출력값**: 
  - `InvalidEmailFormat` 예외
- **동작 근거**: 
  - 이메일 형식 검증

##### 1.5 컨테이너 UID/GID 설정
- **입력값**: 
  - `uid`: 2000
  - `gid`: 2000
  - `container_registry`: {"docker.io": "user/pass"}
- **기대 출력값**: 
  - 커스텀 UID/GID 설정
  - 레지스트리 인증 정보 저장
- **동작 근거**: 
  - 컨테이너 권한 관리

##### 1.6 리소스 정책 할당
- **입력값**: 
  - `resource_policy`: "limited-user-policy"
  - `allowed_client_ip`: ["192.168.1.0/24"]
- **기대 출력값**: 
  - 제한된 리소스 정책 적용
  - IP 기반 접근 제한
- **동작 근거**: 
  - 세밀한 접근 제어

### 2. Modify User

#### 기능 설명
기존 사용자의 정보와 권한을 수정합니다.

#### 테스트 케이스

##### 2.1 기본 정보 수정
- **입력값**: 
  - `email`: "user@example.com"
  - `props`: {
      "full_name": "Updated Name",
      "description": "Senior Developer"
    }
- **기대 출력값**: 
  - 업데이트된 사용자 정보
- **동작 근거**: 
  - 프로필 정보 변경

##### 2.2 권한 상승
- **입력값**: 
  - `email`: "user@example.com"
  - `props`: {"role": "admin"}
- **기대 출력값**: 
  - 사용자 권한이 admin으로 변경
- **동작 근거**: 
  - 승진 또는 권한 부여

##### 2.3 그룹 변경
- **입력값**: 
  - `props`: {
      "group_ids": ["new-team", "research-team"]
    }
- **기대 출력값**: 
  - 그룹 멤버십 업데이트
  - 이전 그룹에서 제거
- **동작 근거**: 
  - 조직 변경

##### 2.4 상태 변경
- **입력값**: 
  - `props`: {"status": "INACTIVE"}
- **기대 출력값**: 
  - 계정 비활성화
  - 로그인 차단
- **동작 근거**: 
  - 일시적 계정 중지

##### 2.5 TOTP 설정
- **입력값**: 
  - `props`: {
      "totp_key": "base32secret",
      "need_password_change": true
    }
- **기대 출력값**: 
  - 2단계 인증 활성화
  - 다음 로그인 시 비밀번호 변경 강제
- **동작 근거**: 
  - 보안 강화

### 3. Delete User

#### 기능 설명
사용자를 소프트 삭제하여 deleted 상태로 변경합니다.

#### 테스트 케이스

##### 3.1 정상적인 사용자 삭제
- **입력값**: 
  - `email`: "leaving@example.com"
- **기대 출력값**: 
  - 상태: DELETED
  - 키페어 비활성화
  - 데이터는 보존
- **동작 근거**: 
  - 감사 추적 유지

##### 3.2 이미 삭제된 사용자
- **입력값**: 
  - `email`: "deleted@example.com"
- **기대 출력값**: 
  - 성공 (멱등성)
- **동작 근거**: 
  - 중복 삭제 요청 처리

##### 3.3 활성 세션이 있는 사용자
- **입력값**: 
  - 실행 중인 세션이 있는 사용자
- **기대 출력값**: 
  - 사용자 삭제 성공
  - 세션은 계속 실행 (소프트 삭제)
- **동작 근거**: 
  - 작업 중단 방지

### 4. Purge User

#### 기능 설명
사용자와 모든 관련 리소스를 영구적으로 삭제합니다.

#### 테스트 케이스

##### 4.1 완전한 사용자 퍼지
- **입력값**: 
  - `email`: "purge@example.com"
- **기대 출력값**: 
  - 사용자 레코드 삭제
  - 모든 키페어 삭제
  - VFolder 삭제/이전
  - 세션 강제 종료
  - 통계 데이터 삭제
- **동작 근거**: 
  - GDPR 준수, 완전 삭제

##### 4.2 공유 VFolder 처리
- **입력값**: 
  - `email`: "sharing@example.com"
  - `migrate_shared_vfolders`: "admin@example.com"
- **기대 출력값**: 
  - 개인 VFolder 삭제
  - 공유 VFolder 소유권 이전
- **동작 근거**: 
  - 공유 데이터 보존

##### 4.3 모델 서비스 위임
- **입력값**: 
  - `email`: "ml-engineer@example.com"
  - `delegate_model_service_to`: "team-lead@example.com"
- **기대 출력값**: 
  - 실행 중인 모델 서비스 위임
  - 새 소유자에게 권한 이전
- **동작 근거**: 
  - 서비스 연속성 유지

##### 4.4 강제 리소스 정리
- **입력값**: 
  - 많은 활성 리소스를 가진 사용자
- **기대 출력값**: 
  - 모든 세션 강제 종료
  - 엔드포인트 삭제
  - 에러 로그 정리
- **동작 근거**: 
  - 완전한 정리 보장


### 5. User Month Stats

#### 기능 설명
사용자의 지난 한 달간 리소스 사용량 통계를 조회합니다.

#### 테스트 케이스

##### 5.1 정상적인 통계 조회
- **입력값**: 
  - `email`: "active@example.com"
  - `month`: null (현재 월)
- **기대 출력값**: 
  - 15분 단위 사용량 데이터
  - CPU, 메모리, GPU 시간
  - 디스크 I/O
  - 네트워크 전송량
- **동작 근거**: 
  - 사용량 기반 과금

##### 5.2 특정 월 조회
- **입력값**: 
  - `email`: "user@example.com"
  - `month`: "2024-01"
- **기대 출력값**: 
  - 2024년 1월 사용량
  - 일별 집계 데이터
- **동작 근거**: 
  - 과거 사용량 확인

##### 5.3 사용량 없는 사용자
- **입력값**: 
  - 신규 사용자 또는 비활성 사용자
- **기대 출력값**: 
  - 빈 통계 또는 0 값
- **동작 근거**: 
  - 초기 사용자 처리

##### 5.4 프로젝트별 분류
- **입력값**: 
  - `group_by`: "project"
- **기대 출력값**: 
  - 프로젝트별 사용량 분리
  - 각 프로젝트 소계
- **동작 근거**: 
  - 프로젝트 비용 할당

### 6. Admin Month Stats

#### 기능 설명
시스템 전체의 월간 사용량 통계를 조회합니다.

#### 테스트 케이스

##### 6.1 전체 시스템 통계
- **입력값**: 
  - `month`: null (현재 월)
- **기대 출력값**: 
  - 모든 사용자 통계 집계
  - 도메인별 분류
  - 총 리소스 사용량
- **동작 근거**: 
  - 시스템 용량 계획

##### 6.2 도메인별 필터링
- **입력값**: 
  - `domain`: "research"
- **기대 출력값**: 
  - 특정 도메인 사용량만
  - 도메인 내 사용자 순위
- **동작 근거**: 
  - 도메인 관리

##### 6.3 리소스 타입별 집계
- **입력값**: 
  - `resource_type`: "gpu"
- **기대 출력값**: 
  - GPU 사용량만 표시
  - GPU 타입별 분류
- **동작 근거**: 
  - 고가 리소스 추적

##### 6.4 피크 사용량 분석
- **입력값**: 
  - `include_peaks`: true
- **기대 출력값**: 
  - 일별 피크 시간대
  - 최대 동시 사용량
- **동작 근거**: 
  - 용량 최적화


## 공통 에러 케이스

### 권한 부족
- **상황**: 일반 사용자가 타인 정보 수정
- **기대 동작**: 
  - PermissionDenied 예외
  - 감사 로그 기록

### 리소스 정리 실패
- **상황**: VFolder 삭제 중 스토리지 오류
- **기대 동작**: 
  - 부분 실패 처리
  - 재시도 큐 등록

### 순환 참조
- **상황**: 사용자 간 상호 의존성
- **기대 동작**: 
  - 의존성 해결
  - 강제 정리 옵션

