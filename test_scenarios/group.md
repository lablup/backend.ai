# Group Service Test Scenarios

## 서비스 개요
Group 서비스는 Backend.AI에서 그룹(프로젝트)을 관리하는 핵심 서비스입니다.
그룹은 사용자들이 리소스를 공유하고 협업하는 단위로, 생성, 수정, 삭제 및 사용량 추적 기능을 제공합니다.

## 주요 기능 목록
1. Create Group - 새로운 그룹 생성
   - Action: `CreateGroupAction`
   - Result: `CreateGroupActionResult`
2. Modify Group - 그룹 속성 및 멤버십 수정
   - Action: `ModifyGroupAction`
   - Result: `ModifyGroupActionResult`
3. Delete Group - 그룹 비활성화 (소프트 삭제)
   - Action: `DeleteGroupAction`
   - Result: `DeleteGroupActionResult`
4. Purge Group - 그룹 영구 삭제
   - Action: `PurgeGroupAction`
   - Result: `PurgeGroupActionResult`
5. Usage Per Month - 월별 사용량 조회
   - Action: `UsagePerMonthAction`
   - Result: `UsagePerMonthActionResult`
6. Usage Per Period - 기간별 사용량 조회
   - Action: `UsagePerPeriodAction`
   - Result: `UsagePerPeriodActionResult`

## 테스트 시나리오

### 1. Create Group

#### 기능 설명
새로운 그룹을 생성하고 리소스 정책을 설정합니다.

#### 테스트 케이스

##### 1.1 정상적인 그룹 생성
- **입력값**: 
  - `name`: "research-team"
  - `domain_name`: "default"
  - `type`: ProjectType.GENERAL
  - `description`: "Research Team Group"
  - `is_active`: true
  - `total_resource_slots`: {"cpu": "50", "memory": "256G", "gpu": "4"}
  - `allowed_vfolder_hosts`: ["storage1", "storage2"]
  - `resource_policy`: "default-policy"
- **기대 출력값**: 
  - 생성된 그룹 데이터 (ID, 타임스탬프 포함)
- **동작 근거**: 
  - 모든 필수 정보 제공
  - 도메인 내에서 고유한 그룹 이름

##### 1.2 중복된 그룹 이름
- **입력값**: 
  - `name`: "existing-group"
  - `domain_name`: "default"
  - 기타 유효한 정보
- **기대 출력값**: 
  - `DuplicatedGroup` 예외 또는 데이터베이스 무결성 에러
- **동작 근거**: 
  - 도메인 내에서 그룹 이름은 고유해야 함

##### 1.3 MODEL_STORE 타입 그룹 생성
- **입력값**: 
  - `name`: "model-repository"
  - `type`: ProjectType.MODEL_STORE
  - 기타 유효한 정보
- **기대 출력값**: 
  - MODEL_STORE 타입의 그룹 생성
- **동작 근거**: 
  - 특수 목적 그룹 타입 지원

##### 1.4 존재하지 않는 도메인
- **입력값**: 
  - `domain_name`: "non-existent-domain"
  - 기타 유효한 정보
- **기대 출력값**: 
  - `DomainNotFound` 예외
- **동작 근거**: 
  - 유효한 도메인에만 그룹 생성 가능

##### 1.5 잘못된 리소스 정책
- **입력값**: 
  - `resource_policy`: "invalid-policy"
  - 기타 유효한 정보
- **기대 출력값**: 
  - `ResourcePolicyNotFound` 예외
- **동작 근거**: 
  - 존재하는 리소스 정책만 사용 가능

### 2. Modify Group

#### 기능 설명
그룹의 속성을 수정하고 사용자 멤버십을 관리합니다.

#### 테스트 케이스

##### 2.1 그룹 이름 및 설명 변경
- **입력값**: 
  - `gid`: UUID("valid-group-id")
  - `modifier`: {"name": "renamed-group", "description": "Updated description"}
- **기대 출력값**: 
  - 업데이트된 그룹 정보
- **동작 근거**: 
  - 기본 속성 변경 허용

##### 2.2 사용자 추가
- **입력값**: 
  - `gid`: UUID("valid-group-id")
  - `add_user_uuids`: [UUID("user1"), UUID("user2")]
- **기대 출력값**: 
  - 사용자들이 그룹에 추가됨
  - association_groups_users 테이블 업데이트
- **동작 근거**: 
  - 그룹 멤버십 확장

##### 2.3 사용자 제거
- **입력값**: 
  - `gid`: UUID("valid-group-id")
  - `remove_user_uuids`: [UUID("user3")]
- **기대 출력값**: 
  - 사용자가 그룹에서 제거됨
- **동작 근거**: 
  - 그룹 멤버십 축소

##### 2.4 동시에 추가와 제거
- **입력값**: 
  - `gid`: UUID("valid-group-id")
  - `add_user_uuids`: [UUID("user1")]
  - `remove_user_uuids`: [UUID("user2")]
- **기대 출력값**: 
  - user1 추가, user2 제거
- **동작 근거**: 
  - 복합 멤버십 변경

##### 2.5 존재하지 않는 사용자 추가
- **입력값**: 
  - `add_user_uuids`: [UUID("non-existent-user")]
- **기대 출력값**: 
  - `UserNotFound` 예외 또는 외래 키 제약 에러
- **동작 근거**: 
  - 유효한 사용자만 추가 가능

##### 2.6 리소스 슬롯 업데이트
- **입력값**: 
  - `modifier`: {"total_resource_slots": {"cpu": "100", "memory": "512G"}}
- **기대 출력값**: 
  - 리소스 제한 업데이트
- **동작 근거**: 
  - 그룹 리소스 할당 조정

### 3. Delete Group

#### 기능 설명
그룹을 비활성화합니다 (소프트 삭제).

#### 테스트 케이스

##### 3.1 정상적인 그룹 삭제
- **입력값**: 
  - `gid`: UUID("valid-group-id")
- **기대 출력값**: 
  - `is_active`: false
  - `integration_id`: null
- **동작 근거**: 
  - 소프트 삭제로 데이터 보존

##### 3.2 이미 삭제된 그룹
- **입력값**: 
  - `gid`: UUID("already-deleted-group")
- **기대 출력값**: 
  - 성공 (멱등성) 또는 경고
- **동작 근거**: 
  - 중복 삭제 요청 처리

##### 3.3 활성 리소스가 있는 그룹
- **입력값**: 
  - `gid`: UUID("group-with-active-resources")
- **기대 출력값**: 
  - 성공 (소프트 삭제는 리소스 체크 없음)
- **동작 근거**: 
  - 소프트 삭제는 활성 리소스 허용

### 4. Purge Group

#### 기능 설명
그룹과 관련된 모든 리소스를 영구적으로 삭제합니다.

#### 테스트 케이스

##### 4.1 정상적인 그룹 퍼지
- **입력값**: 
  - `gid`: UUID("inactive-group-id")
  - 활성 커널, 마운트된 vfolder, 엔드포인트 없음
- **기대 출력값**: 
  - 그룹과 모든 관련 리소스 삭제
- **동작 근거**: 
  - 모든 전제조건 충족

##### 4.2 활성 커널이 있는 그룹
- **입력값**: 
  - `gid`: UUID("group-with-active-kernels")
- **기대 출력값**: 
  - `GroupStillHasActiveKernels` 예외
- **동작 근거**: 
  - 실행 중인 커널이 있으면 퍼지 불가

##### 4.3 마운트된 vfolder가 있는 그룹
- **입력값**: 
  - `gid`: UUID("group-with-mounted-vfolders")
- **기대 출력값**: 
  - `GroupFolderStillMounted` 예외
- **동작 근거**: 
  - 사용 중인 스토리지가 있으면 퍼지 불가

##### 4.4 활성 엔드포인트가 있는 그룹
- **입력값**: 
  - `gid`: UUID("group-with-active-endpoints")
- **기대 출력값**: 
  - `GroupStillHasActiveEndpoints` 예외
- **동작 근거**: 
  - 서비스 중인 엔드포인트가 있으면 퍼지 불가

##### 4.5 캐스케이드 삭제 확인
- **입력값**: 
  - `gid`: UUID("group-for-cascade-delete")
  - 비활성 커널, vfolder, 세션 존재
- **기대 출력값**: 
  - 그룹과 모든 관련 리소스 삭제
  - 엔드포인트, vfolder, 커널, 세션 순서로 삭제
- **동작 근거**: 
  - 의존성 순서에 따른 캐스케이드 삭제

### 5. Usage Per Month

#### 기능 설명
특정 월의 컨테이너 사용량 통계를 조회합니다.

#### 테스트 케이스

##### 5.1 특정 월 사용량 조회
- **입력값**: 
  - `month`: "202401"
  - `group_ids`: null (모든 그룹)
- **기대 출력값**: 
  - 2024년 1월의 모든 그룹 사용량 통계
  - CPU, 메모리, GPU, I/O 메트릭 포함
- **동작 근거**: 
  - Redis에서 월별 통계 조회

##### 5.2 특정 그룹들의 사용량
- **입력값**: 
  - `month`: "202401"
  - `group_ids`: ["group1", "group2"]
- **기대 출력값**: 
  - 지정된 그룹들의 사용량만 반환
- **동작 근거**: 
  - 그룹 필터링 적용

##### 5.3 잘못된 월 형식
- **입력값**: 
  - `month`: "2024-01" (잘못된 형식)
- **기대 출력값**: 
  - 형식 검증 에러
- **동작 근거**: 
  - YYYYMM 형식만 허용

##### 5.4 미래 월 조회
- **입력값**: 
  - `month`: "209901"
- **기대 출력값**: 
  - 빈 결과 또는 에러
- **동작 근거**: 
  - 아직 발생하지 않은 데이터

##### 5.5 데이터가 없는 월
- **입력값**: 
  - `month`: "202201" (데이터 없음)
- **기대 출력값**: 
  - 빈 통계 결과
- **동작 근거**: 
  - 해당 기간 사용량 없음

### 6. Usage Per Period

#### 기능 설명
특정 기간의 프로젝트 리소스 사용량을 조회합니다.

#### 테스트 케이스

##### 6.1 정상적인 기간 조회
- **입력값**: 
  - `start_date`: "20240101"
  - `end_date`: "20240131"
  - `project_id`: null
- **기대 출력값**: 
  - 2024년 1월 전체 사용량
  - 집계된 리소스 사용 데이터
- **동작 근거**: 
  - 유효한 날짜 범위

##### 6.2 특정 프로젝트 사용량
- **입력값**: 
  - `start_date`: "20240101"
  - `end_date`: "20240131"
  - `project_id`: "project-123"
- **기대 출력값**: 
  - 해당 프로젝트의 사용량만 반환
- **동작 근거**: 
  - 프로젝트 필터 적용

##### 6.3 100일 초과 기간
- **입력값**: 
  - `start_date`: "20240101"
  - `end_date`: "20240501"
- **기대 출력값**: 
  - `PeriodTooLong` 예외
- **동작 근거**: 
  - 최대 100일 제한

##### 6.4 잘못된 날짜 순서
- **입력값**: 
  - `start_date`: "20240131"
  - `end_date`: "20240101"
- **기대 출력값**: 
  - `InvalidDateRange` 예외
- **동작 근거**: 
  - 시작일이 종료일보다 늦을 수 없음

##### 6.5 잘못된 날짜 형식
- **입력값**: 
  - `start_date`: "2024-01-01"
  - `end_date`: "2024-01-31"
- **기대 출력값**: 
  - 형식 검증 에러
- **동작 근거**: 
  - YYYYMMDD 형식만 허용

## 공통 에러 케이스

### 데이터베이스 연결 실패
- **상황**: 데이터베이스 연결 불가
- **기대 동작**: 
  - 데이터베이스 연결 에러
  - 모든 작업 실패

### Redis 연결 실패
- **상황**: Redis 서버 연결 불가
- **기대 동작**: 
  - 사용량 통계 조회 실패
  - 다른 작업은 정상 동작

### 트랜잭션 충돌
- **상황**: 동일 그룹에 대한 동시 수정
- **기대 동작**: 
  - 재시도 로직 실행
  - 충돌 해결 또는 에러 반환

### 스토리지 매니저 오류
- **상황**: vfolder 작업 중 스토리지 오류
- **기대 동작**: 
  - 적절한 에러 메시지
  - 트랜잭션 롤백

