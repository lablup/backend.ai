# Container Registry Service Test Scenarios

## 서비스 개요
Container Registry 서비스는 Backend.AI에서 컨테이너 레지스트리를 관리하는 서비스입니다.
다양한 유형의 컨테이너 레지스트리와 연동하여 이미지를 스캔하고, 메타데이터를 관리하며, 
레지스트리 설정을 조회하는 기능을 제공합니다.

## 주요 기능 목록
1. Rescan Images - 컨테이너 레지스트리의 이미지 스캔 및 업데이트
   - Action: `RescanImagesAction`
   - Result: `RescanImagesActionResult`
2. Clear Images - 특정 레지스트리의 모든 이미지를 삭제 상태로 변경
   - Action: `ClearImagesAction`
   - Result: `ClearImagesActionResult`
3. Load Container Registries - 특정 컨테이너 레지스트리 설정 조회
   - Action: `LoadContainerRegistriesAction`
   - Result: `LoadContainerRegistriesActionResult`
4. Load All Container Registries - 모든 컨테이너 레지스트리 설정 조회
   - Action: `LoadAllContainerRegistriesAction`
   - Result: `LoadAllContainerRegistriesActionResult`
5. Get Container Registries - 알려진 컨테이너 레지스트리 목록 조회
   - Action: `GetContainerRegistriesAction`
   - Result: `GetContainerRegistriesActionResult`

## 테스트 시나리오

### 1. Rescan Images

#### 기능 설명
특정 컨테이너 레지스트리를 스캔하여 이미지 정보를 발견하고 데이터베이스를 업데이트합니다.

#### 테스트 케이스

##### 1.1 정상적인 이미지 스캔
- **입력값**: 
  - `registry_name`: "docker.io"
  - `project`: null (모든 프로젝트)
  - `reporter`: null
- **기대 출력값**: 
  - `images`: 발견된 이미지 목록
  - `errors`: 빈 목록
  - `registry`: 레지스트리 정보
- **동작 근거**: 
  - 레지스트리가 정상적으로 응답
  - 새로운 이미지들이 발견되고 기록됨

##### 1.2 프로젝트별 필터링 스캔
- **입력값**: 
  - `registry_name`: "private-registry"
  - `project`: "project-a"
  - `reporter`: null
- **기대 출력값**: 
  - `images`: project-a에 속한 이미지만 포함
  - `errors`: 빈 목록
  - `registry`: 레지스트리 정보
- **동작 근거**: 
  - 프로젝트 필터가 적용되어 해당 프로젝트 이미지만 스캔

##### 1.3 레지스트리 연결 실패
- **입력값**: 
  - `registry_name`: "offline-registry"
  - `project`: null
  - `reporter`: null
- **기대 출력값**: 
  - `images`: 빈 목록
  - `errors`: 연결 에러 메시지 포함
  - `registry`: 레지스트리 정보
- **동작 근거**: 
  - 네트워크 문제나 레지스트리 다운으로 연결 실패

##### 1.4 존재하지 않는 레지스트리
- **입력값**: 
  - `registry_name`: "non-existent-registry"
  - `project`: null
  - `reporter`: null
- **기대 출력값**: 
  - `RegistryNotFound` 예외 또는 null 결과
- **동작 근거**: 
  - 데이터베이스에 해당 레지스트리 설정이 없음

##### 1.5 진행 상황 리포팅
- **입력값**: 
  - `registry_name`: "large-registry"
  - `project`: null
  - `reporter`: ProgressReporter 인스턴스
- **기대 출력값**: 
  - `images`: 발견된 이미지 목록
  - `errors`: 처리 중 발생한 에러
  - `registry`: 레지스트리 정보
  - reporter에 진행 상황 업데이트
- **동작 근거**: 
  - 대량의 이미지 스캔 시 진행 상황 추적 필요

##### 1.6 인증 실패
- **입력값**: 
  - `registry_name`: "private-registry"
  - 잘못된 인증 정보가 설정된 레지스트리
- **기대 출력값**: 
  - `images`: 빈 목록
  - `errors`: 인증 에러 메시지
  - `registry`: 레지스트리 정보
- **동작 근거**: 
  - 레지스트리 접근 권한이 없음

### 2. Clear Images

#### 기능 설명
특정 레지스트리의 모든 이미지를 삭제 상태로 표시합니다 (소프트 삭제).

#### 테스트 케이스

##### 2.1 전체 이미지 삭제
- **입력값**: 
  - `registry_name`: "docker.io"
  - `project`: null
- **기대 출력값**: 
  - 성공 (빈 응답)
  - 모든 이미지 상태가 DELETED로 변경
- **동작 근거**: 
  - 레지스트리의 모든 활성 이미지를 삭제 상태로 변경

##### 2.2 프로젝트별 이미지 삭제
- **입력값**: 
  - `registry_name`: "private-registry"
  - `project`: "project-a"
- **기대 출력값**: 
  - 성공 (빈 응답)
  - project-a의 이미지만 DELETED로 변경
- **동작 근거**: 
  - 프로젝트 필터가 적용되어 특정 프로젝트 이미지만 삭제

##### 2.3 이미 삭제된 이미지들
- **입력값**: 
  - `registry_name`: "docker.io"
  - 이미 모든 이미지가 DELETED 상태
- **기대 출력값**: 
  - 성공 (빈 응답)
  - 변경사항 없음 (멱등성)
- **동작 근거**: 
  - 이미 삭제된 이미지는 무시

##### 2.4 존재하지 않는 레지스트리
- **입력값**: 
  - `registry_name`: "non-existent-registry"
  - `project`: null
- **기대 출력값**: 
  - 성공 (빈 응답) 또는 경고
  - 실제 변경사항 없음
- **동작 근거**: 
  - 해당 레지스트리의 이미지가 없으므로 영향 없음

### 3. Load Container Registries

#### 기능 설명
특정 컨테이너 레지스트리의 설정 정보를 조회합니다.

#### 테스트 케이스

##### 3.1 단일 레지스트리 조회
- **입력값**: 
  - `registry_name`: "docker.io"
  - `project`: null
- **기대 출력값**: 
  - ContainerRegistryRow 객체 목록
  - docker.io 설정 정보 포함
- **동작 근거**: 
  - 데이터베이스에서 해당 레지스트리 정보 조회

##### 3.2 프로젝트별 레지스트리 조회
- **입력값**: 
  - `registry_name`: "private-registry"
  - `project`: "project-a"
- **기대 출력값**: 
  - project-a에 속한 레지스트리 설정만 반환
- **동작 근거**: 
  - 프로젝트 필터 적용

##### 3.3 존재하지 않는 레지스트리
- **입력값**: 
  - `registry_name`: "non-existent"
  - `project`: null
- **기대 출력값**: 
  - 빈 목록
- **동작 근거**: 
  - 일치하는 레지스트리가 없음

##### 3.4 와일드카드 매칭
- **입력값**: 
  - `registry_name`: "docker*"
  - `project`: null
- **기대 출력값**: 
  - "docker"로 시작하는 모든 레지스트리
- **동작 근거**: 
  - 패턴 매칭 지원 (구현에 따라 다름)

### 4. Load All Container Registries

#### 기능 설명
시스템의 모든 컨테이너 레지스트리 설정을 조회합니다.

#### 테스트 케이스

##### 4.1 전체 레지스트리 조회
- **입력값**: 없음
- **기대 출력값**: 
  - 모든 ContainerRegistryRow 객체 목록
  - 각 레지스트리의 전체 설정 정보
- **동작 근거**: 
  - 필터 없이 모든 레지스트리 반환

##### 4.2 레지스트리가 없는 경우
- **입력값**: 없음 (레지스트리가 설정되지 않은 시스템)
- **기대 출력값**: 
  - 빈 목록
- **동작 근거**: 
  - 설정된 레지스트리가 없음

##### 4.3 다양한 타입의 레지스트리
- **입력값**: 없음
- **기대 출력값**: 
  - Docker Hub, ECR, GCR 등 다양한 타입의 레지스트리 포함
- **동작 근거**: 
  - 모든 지원되는 레지스트리 타입 조회

### 5. Get Container Registries

#### 기능 설명
알려진 컨테이너 레지스트리의 포맷된 목록을 조회합니다.

#### 테스트 케이스

##### 5.1 정상적인 레지스트리 목록
- **입력값**: 없음
- **기대 출력값**: 
  - `{"project/registry_name": "url"}` 형식의 딕셔너리
  - 예: `{"default/docker.io": "https://registry.docker.io"}`
- **동작 근거**: 
  - 레지스트리 정보를 사용자 친화적 형식으로 반환

##### 5.2 프로젝트별 레지스트리 구분
- **입력값**: 없음
- **기대 출력값**: 
  - 프로젝트별로 구분된 레지스트리 목록
  - 예: `{"project-a/private": "url1", "project-b/private": "url2"}`
- **동작 근거**: 
  - 동일한 이름의 레지스트리도 프로젝트로 구분

##### 5.3 빈 레지스트리
- **입력값**: 없음 (설정된 레지스트리 없음)
- **기대 출력값**: 
  - 빈 딕셔너리 `{}`
- **동작 근거**: 
  - 알려진 레지스트리가 없음

## 공통 에러 케이스

### 데이터베이스 연결 실패
- **상황**: 데이터베이스 연결 불가
- **기대 동작**: 
  - 데이터베이스 연결 에러
  - 모든 작업 실패

### 트랜잭션 롤백
- **상황**: 이미지 업데이트 중 에러 발생
- **기대 동작**: 
  - 트랜잭션 롤백
  - 부분적 업데이트 방지

### 동시성 문제
- **상황**: 동일 레지스트리에 대한 동시 스캔
- **기대 동작**: 
  - 적절한 락킹 또는 충돌 해결
  - 데이터 일관성 유지

