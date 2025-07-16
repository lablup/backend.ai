# Domain Service Test Scenarios

## 서비스 개요
Domain 서비스는 Backend.AI의 다중 테넌시를 위한 핵심 서비스로, 도메인(조직 단위)을 관리합니다.
각 도메인은 사용자, 그룹, 리소스를 격리하여 관리하며, 도메인 생성, 수정, 삭제 등의 기능을 제공합니다.

## 주요 기능 목록
1. Create Domain - 새로운 도메인 생성
   - Action: `CreateDomainAction`
   - Result: `CreateDomainActionResult`
2. Create Domain Node - 노드별 설정이 포함된 도메인 생성
   - Action: `CreateDomainNodeAction`
   - Result: `CreateDomainNodeActionResult`
3. Modify Domain - 도메인 속성 수정
   - Action: `ModifyDomainAction`
   - Result: `ModifyDomainActionResult`
4. Modify Domain Node - 노드별 도메인 설정 수정
   - Action: `ModifyDomainNodeAction`
   - Result: `ModifyDomainNodeActionResult`
5. Delete Domain - 도메인 비활성화 (소프트 삭제)
   - Action: `DeleteDomainAction`
   - Result: `DeleteDomainActionResult`
6. Purge Domain - 도메인 영구 삭제
   - Action: `PurgeDomainAction`
   - Result: `PurgeDomainActionResult`

## 테스트 시나리오

### 1. Create Domain

#### 기능 설명
새로운 도메인을 생성하고 자동으로 model-store 그룹을 생성합니다.

#### 테스트 케이스

##### 1.1 정상적인 도메인 생성
- **입력값**: 
  - `name`: "new-domain"
  - `description`: "New Domain for Testing"
  - `is_active`: true
  - `total_resource_slots`: {"cpu": "10", "memory": "64G"}
  - `allowed_vfolder_hosts`: ["host1", "host2"]
  - `allowed_docker_registries`: ["docker.io"]
- **기대 출력값**: 
  - 생성된 도메인 정보
  - model-store 그룹 자동 생성
- **동작 근거**: 
  - 모든 필수 정보 제공
  - 중복되지 않는 도메인 이름

##### 1.2 중복된 도메인 이름
- **입력값**: 
  - `name`: "existing-domain" (이미 존재하는 도메인)
  - 기타 유효한 정보
- **기대 출력값**: 
  - `DuplicatedDomain` 예외 또는 데이터베이스 무결성 에러
- **동작 근거**: 
  - 도메인 이름은 고유해야 함

##### 1.3 잘못된 리소스 슬롯 형식
- **입력값**: 
  - `name`: "test-domain"
  - `total_resource_slots`: {"invalid": "format"}
- **기대 출력값**: 
  - 검증 에러
- **동작 근거**: 
  - 리소스 슬롯은 특정 형식을 따라야 함

##### 1.4 빈 도메인 이름
- **입력값**: 
  - `name`: ""
  - 기타 유효한 정보
- **기대 출력값**: 
  - 검증 에러
- **동작 근거**: 
  - 도메인 이름은 필수 항목

##### 1.5 트랜잭션 롤백 시나리오
- **입력값**: 
  - 유효한 도메인 정보
  - model-store 그룹 생성 중 에러 발생
- **기대 출력값**: 
  - 트랜잭션 롤백
  - 도메인과 그룹 모두 생성되지 않음
- **동작 근거**: 
  - 원자성 보장

### 2. Create Domain Node

#### 기능 설명
스케일링 그룹 연결이 포함된 도메인을 생성합니다.

#### 테스트 케이스

##### 2.1 스케일링 그룹과 함께 도메인 생성
- **입력값**: 
  - `domain`: 유효한 도메인 정보
  - `scaling_groups`: ["sg1", "sg2"]
  - `user`: 권한이 있는 사용자 정보
- **기대 출력값**: 
  - 도메인 생성
  - 스케일링 그룹 연결 완료
- **동작 근거**: 
  - 사용자가 스케일링 그룹 연결 권한 보유

##### 2.2 권한 없는 스케일링 그룹 연결
- **입력값**: 
  - `domain`: 유효한 도메인 정보
  - `scaling_groups`: ["unauthorized-sg"]
  - `user`: 권한이 없는 사용자
- **기대 출력값**: 
  - `PermissionDenied` 예외
- **동작 근거**: 
  - ScalingGroupPermission.ASSOCIATE_WITH_SCOPES 권한 필요

##### 2.3 존재하지 않는 스케일링 그룹
- **입력값**: 
  - `scaling_groups`: ["non-existent-sg"]
- **기대 출력값**: 
  - `ScalingGroupNotFound` 예외
- **동작 근거**: 
  - 유효한 스케일링 그룹만 연결 가능

### 3. Modify Domain

#### 기능 설명
기존 도메인의 속성을 수정합니다.

#### 테스트 케이스

##### 3.1 도메인 이름 변경
- **입력값**: 
  - `name`: "existing-domain"
  - `modifier`: {"name": "renamed-domain"}
- **기대 출력값**: 
  - 성공적인 업데이트
  - 변경된 도메인 정보
- **동작 근거**: 
  - 도메인 이름 변경 허용

##### 3.2 리소스 슬롯 업데이트
- **입력값**: 
  - `name`: "test-domain"
  - `modifier`: {"total_resource_slots": {"cpu": "20", "memory": "128G"}}
- **기대 출력값**: 
  - 리소스 제한 업데이트
- **동작 근거**: 
  - 도메인 리소스 할당 조정

##### 3.3 도메인 비활성화
- **입력값**: 
  - `name`: "active-domain"
  - `modifier`: {"is_active": false}
- **기대 출력값**: 
  - 도메인 비활성화 상태
- **동작 근거**: 
  - 도메인 일시 중지 기능

##### 3.4 존재하지 않는 도메인 수정
- **입력값**: 
  - `name`: "non-existent-domain"
  - `modifier`: 임의의 수정 사항
- **기대 출력값**: 
  - `DomainNotFound` 예외
- **동작 근거**: 
  - 존재하는 도메인만 수정 가능

##### 3.5 null 값으로 필드 제거
- **입력값**: 
  - `modifier`: {"description": null, "integration_id": null}
- **기대 출력값**: 
  - 해당 필드들이 null로 설정
- **동작 근거**: 
  - TriState를 통한 null 설정 지원

### 4. Modify Domain Node

#### 기능 설명
도메인의 노드별 설정, 특히 스케일링 그룹 연결을 수정합니다.

#### 테스트 케이스

##### 4.1 스케일링 그룹 추가
- **입력값**: 
  - `name`: "test-domain"
  - `scaling_groups_to_add`: ["new-sg1", "new-sg2"]
  - `user`: 권한이 있는 사용자
- **기대 출력값**: 
  - 새 스케일링 그룹 연결 추가
- **동작 근거**: 
  - 권한 검증 후 연결 추가

##### 4.2 스케일링 그룹 제거
- **입력값**: 
  - `name`: "test-domain"
  - `scaling_groups_to_remove`: ["old-sg1"]
  - `user`: 권한이 있는 사용자
- **기대 출력값**: 
  - 기존 스케일링 그룹 연결 제거
- **동작 근거**: 
  - 연결된 스케일링 그룹 제거

##### 4.3 추가와 제거 그룹 중복
- **입력값**: 
  - `scaling_groups_to_add`: ["sg1"]
  - `scaling_groups_to_remove`: ["sg1"]
- **기대 출력값**: 
  - `InvalidOperation` 예외
- **동작 근거**: 
  - 동일 그룹을 추가하면서 제거할 수 없음

##### 4.4 dotfiles 업데이트
- **입력값**: 
  - `name`: "test-domain"
  - `dotfiles`: ".bashrc contents..."
- **기대 출력값**: 
  - dotfiles 설정 업데이트
- **동작 근거**: 
  - 도메인별 설정 파일 관리

### 5. Delete Domain

#### 기능 설명
도메인을 비활성화합니다 (소프트 삭제).

#### 테스트 케이스

##### 5.1 정상적인 도메인 삭제
- **입력값**: 
  - `name`: "test-domain"
- **기대 출력값**: 
  - `is_active`: false로 설정
  - 도메인은 데이터베이스에 유지
- **동작 근거**: 
  - 소프트 삭제로 데이터 보존

##### 5.2 이미 삭제된 도메인
- **입력값**: 
  - `name`: "deleted-domain" (이미 is_active=false)
- **기대 출력값**: 
  - 성공 (멱등성) 또는 경고
- **동작 근거**: 
  - 중복 삭제 요청 처리

##### 5.3 활성 리소스가 있는 도메인
- **입력값**: 
  - `name`: "active-domain-with-resources"
- **기대 출력값**: 
  - 성공 (소프트 삭제는 활성 리소스 허용)
- **동작 근거**: 
  - 소프트 삭제는 리소스 체크 없음

### 6. Purge Domain

#### 기능 설명
도메인과 관련된 모든 데이터를 영구적으로 삭제합니다.

#### 테스트 케이스

##### 6.1 정상적인 도메인 퍼지
- **입력값**: 
  - `name`: "inactive-domain"
  - 활성 커널, 사용자, 그룹 없음
- **기대 출력값**: 
  - 도메인 완전 삭제
  - 종료된 커널들도 삭제
- **동작 근거**: 
  - 모든 전제조건 충족

##### 6.2 활성 커널이 있는 도메인
- **입력값**: 
  - `name`: "domain-with-active-kernels"
  - 실행 중인 커널 존재
- **기대 출력값**: 
  - `DomainHasActiveKernels` 예외
- **동작 근거**: 
  - 활성 리소스가 있으면 퍼지 불가

##### 6.3 사용자가 있는 도메인
- **입력값**: 
  - `name`: "domain-with-users"
  - 도메인에 속한 사용자 존재
- **기대 출력값**: 
  - `DomainHasUsers` 예외
- **동작 근거**: 
  - 사용자가 있으면 퍼지 불가

##### 6.4 그룹이 있는 도메인
- **입력값**: 
  - `name`: "domain-with-groups"
  - 도메인에 속한 그룹 존재
- **기대 출력값**: 
  - `DomainHasGroups` 예외
- **동작 근거**: 
  - 그룹이 있으면 퍼지 불가

##### 6.5 종료된 커널 정리
- **입력값**: 
  - `name`: "domain-with-terminated-kernels"
  - 종료된 커널들만 존재
- **기대 출력값**: 
  - 도메인과 종료된 커널 모두 삭제
- **동작 근거**: 
  - 종료된 커널은 함께 정리

## 공통 에러 케이스

### 데이터베이스 연결 실패
- **상황**: 데이터베이스 연결 불가
- **기대 동작**: 
  - 데이터베이스 연결 에러
  - 모든 작업 실패

### 트랜잭션 충돌
- **상황**: 동일 도메인에 대한 동시 수정
- **기대 동작**: 
  - 재시도 로직 실행
  - 충돌 해결 또는 에러 반환

### 권한 부족
- **상황**: 필요한 권한이 없는 사용자의 요청
- **기대 동작**: 
  - PermissionDenied 예외
  - 작업 차단

