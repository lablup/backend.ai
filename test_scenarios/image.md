# Image Service Test Scenarios

## 서비스 개요
Image 서비스는 Backend.AI에서 컨테이너 이미지를 관리하는 핵심 서비스입니다.
이미지의 생명주기 관리, 메타데이터 수정, 별칭 관리, 에이전트 상의 이미지 관리 등의 기능을 제공합니다.

## 주요 기능 목록
1. Forget Image - 이미지 소프트 삭제
   - Action: `ForgetImageAction`
   - Result: `ForgetImageActionResult`
2. Forget Image by ID - UUID로 이미지 소프트 삭제
   - Action: `ForgetImageByIdAction`
   - Result: `ForgetImageByIdActionResult`
3. Purge Image by ID - 이미지 하드 삭제
   - Action: `PurgeImageByIdAction`
   - Result: `PurgeImageByIdActionResult`
4. Purge Images - 에이전트에서 이미지 제거
   - Action: `PurgeImagesAction`
   - Result: `PurgeImagesActionResult`
5. Scan Image - 이미지 메타데이터 스캔 및 업데이트
   - Action: `ScanImageAction`
   - Result: `ScanImageActionResult`
6. Modify Image - 이미지 속성 수정
   - Action: `ModifyImageAction`
   - Result: `ModifyImageActionResult`
7. Clear Image Custom Resource Limit - 커스텀 리소스 제한 초기화
   - Action: `ClearImageCustomResourceLimitAction`
   - Result: `ClearImageCustomResourceLimitActionResult`
8. Alias Image - 이미지 별칭 생성
   - Action: `AliasImageAction`
   - Result: `AliasImageActionResult`
9. Dealias Image - 이미지 별칭 제거
   - Action: `DealiasImageAction`
   - Result: `DealiasImageActionResult`
10. Untag Image from Registry - 레지스트리에서 이미지 태그 제거
    - Action: `UntagImageFromRegistryAction`
    - Result: `UntagImageFromRegistryActionResult`

## 테스트 시나리오

### 1. Forget Image

#### 기능 설명
이미지를 소프트 삭제하여 is_active를 false로 설정합니다.

#### 테스트 케이스

##### 1.1 정상적인 이미지 소프트 삭제
- **입력값**: 
  - `image_name`: "ubuntu:20.04"
  - `architecture`: "x86_64"
- **기대 출력값**: 
  - 성공 메시지
  - 이미지의 is_active = false
- **동작 근거**: 
  - 이미지를 논리적으로 삭제

##### 1.2 별칭으로 이미지 삭제
- **입력값**: 
  - `image_name`: "my-ubuntu" (별칭)
  - `architecture`: null
- **기대 출력값**: 
  - 원본 이미지가 소프트 삭제됨
- **동작 근거**: 
  - 별칭을 통한 이미지 식별 지원

##### 1.3 존재하지 않는 이미지
- **입력값**: 
  - `image_name`: "non-existent:latest"
  - `architecture`: "x86_64"
- **기대 출력값**: 
  - `ImageNotFound` 예외
- **동작 근거**: 
  - 없는 이미지는 삭제 불가

##### 1.4 이미 삭제된 이미지
- **입력값**: 
  - `image_name`: "deleted-image:latest"
  - `architecture`: "x86_64"
- **기대 출력값**: 
  - 성공 (멱등성) 또는 `ImageNotFound`
- **동작 근거**: 
  - 중복 삭제 요청 처리

##### 1.5 권한 없는 사용자
- **입력값**: 
  - 일반 사용자가 타인의 이미지 삭제 시도
- **기대 출력값**: 
  - `PermissionDenied` 예외
- **동작 근거**: 
  - 소유자만 삭제 가능

### 2. Forget Image by ID

#### 기능 설명
UUID를 사용하여 이미지를 소프트 삭제합니다.

#### 테스트 케이스

##### 2.1 UUID로 정상 삭제
- **입력값**: 
  - `image_id`: UUID("valid-image-id")
- **기대 출력값**: 
  - 성공 메시지
  - 해당 이미지 소프트 삭제
- **동작 근거**: 
  - UUID는 고유 식별자

##### 2.2 잘못된 UUID 형식
- **입력값**: 
  - `image_id`: "invalid-uuid-format"
- **기대 출력값**: 
  - UUID 형식 에러
- **동작 근거**: 
  - UUID 형식 검증

### 3. Purge Image by ID

#### 기능 설명
이미지를 데이터베이스에서 완전히 삭제합니다.

#### 테스트 케이스

##### 3.1 정상적인 이미지 퍼지
- **입력값**: 
  - `image_id`: UUID("valid-image-id")
- **기대 출력값**: 
  - 이미지와 관련 별칭 모두 삭제
- **동작 근거**: 
  - 하드 삭제로 데이터 완전 제거

##### 3.2 별칭이 있는 이미지 퍼지
- **입력값**: 
  - `image_id`: 별칭이 연결된 이미지 ID
- **기대 출력값**: 
  - 이미지와 모든 별칭 삭제
- **동작 근거**: 
  - 캐스케이드 삭제

##### 3.3 사용 중인 이미지 퍼지
- **입력값**: 
  - `image_id`: 실행 중인 세션이 사용하는 이미지
- **기대 출력값**: 
  - `ImageInUse` 예외 또는 강제 삭제
- **동작 근거**: 
  - 사용 중인 이미지 보호

### 4. Purge Images

#### 기능 설명
에이전트에서 이미지를 물리적으로 제거합니다.

#### 테스트 케이스

##### 4.1 단일 에이전트에서 이미지 제거
- **입력값**: 
  - `image_names`: ["ubuntu:20.04", "python:3.9"]
  - `agent_ids`: ["agent-1"]
- **기대 출력값**: 
  - 각 이미지별 삭제 결과
  - 성공/실패 상태
- **동작 근거**: 
  - 에이전트별 이미지 정리

##### 4.2 여러 에이전트에서 이미지 제거
- **입력값**: 
  - `image_names`: ["tensorflow:latest"]
  - `agent_ids`: ["agent-1", "agent-2", "agent-3"]
- **기대 출력값**: 
  - 에이전트별 결과 집계
- **동작 근거**: 
  - 분산 이미지 정리

##### 4.3 일부 에이전트 실패
- **입력값**: 
  - `image_names`: ["pytorch:latest"]
  - `agent_ids`: ["agent-1", "offline-agent"]
- **기대 출력값**: 
  - 성공한 에이전트와 실패한 에이전트 구분
  - 에러 메시지 포함
- **동작 근거**: 
  - 부분 실패 처리

##### 4.4 이미지 이름 패턴
- **입력값**: 
  - `image_names`: ["*:old-*"] (패턴)
  - `agent_ids`: ["agent-1"]
- **기대 출력값**: 
  - 패턴 매칭 지원 여부에 따른 결과
- **동작 근거**: 
  - 와일드카드 지원 확인

### 5. Scan Image

#### 기능 설명
레지스트리에서 이미지 정보를 스캔하여 메타데이터를 업데이트합니다.

#### 테스트 케이스

##### 5.1 새 이미지 스캔
- **입력값**: 
  - `image_name`: "nvidia/cuda:11.8.0-base-ubuntu22.04"
  - `architecture`: "x86_64"
- **기대 출력값**: 
  - 이미지 메타데이터 업데이트
  - 레이어 정보, 크기 등
- **동작 근거**: 
  - 레지스트리에서 최신 정보 가져오기

##### 5.2 멀티 아키텍처 이미지
- **입력값**: 
  - `image_name`: "alpine:latest"
  - `architecture`: "arm64"
- **기대 출력값**: 
  - arm64 아키텍처 정보만 업데이트
- **동작 근거**: 
  - 아키텍처별 이미지 관리

##### 5.3 레지스트리 연결 실패
- **입력값**: 
  - `image_name`: "private-registry/image:tag"
  - 레지스트리 오프라인
- **기대 출력값**: 
  - `RegistryConnectionError` 예외
- **동작 근거**: 
  - 네트워크 장애 처리

##### 5.4 인증 필요한 이미지
- **입력값**: 
  - `image_name`: "private/secure-image:latest"
  - 인증 정보 없음
- **기대 출력값**: 
  - `AuthenticationRequired` 예외
- **동작 근거**: 
  - 프라이빗 이미지 접근 제한

### 6. Modify Image

#### 기능 설명
이미지의 속성을 수정합니다.

#### 테스트 케이스

##### 6.1 이미지 이름 변경
- **입력값**: 
  - `image_id`: UUID("valid-image-id")
  - `props`: {"name": "new-name:latest"}
- **기대 출력값**: 
  - 이미지 이름 업데이트
- **동작 근거**: 
  - 이미지 재명명 지원

##### 6.2 리소스 제한 설정
- **입력값**: 
  - `image_id`: UUID("valid-image-id")
  - `props`: {"resource_limits": {"cpu": "4", "memory": "8G"}}
- **기대 출력값**: 
  - 커스텀 리소스 제한 설정
- **동작 근거**: 
  - 이미지별 리소스 관리

##### 6.3 태그 업데이트
- **입력값**: 
  - `image_id`: UUID("valid-image-id")
  - `props`: {"tags": ["gpu", "ml", "tensorflow"]}
- **기대 출력값**: 
  - 태그 목록 업데이트
- **동작 근거**: 
  - 이미지 분류 및 검색

##### 6.4 여러 속성 동시 수정
- **입력값**: 
  - `props`: {"name": "renamed", "size": 1024000000, "labels": {"version": "2.0"}}
- **기대 출력값**: 
  - 모든 속성 업데이트
- **동작 근거**: 
  - 배치 업데이트 지원

### 7. Clear Image Custom Resource Limit

#### 기능 설명
이미지의 커스텀 리소스 제한을 초기화합니다.

#### 테스트 케이스

##### 7.1 리소스 제한 초기화
- **입력값**: 
  - `image_id`: 커스텀 제한이 설정된 이미지 ID
- **기대 출력값**: 
  - 커스텀 리소스 제한 제거
  - 기본값으로 복원
- **동작 근거**: 
  - 설정 초기화

##### 7.2 이미 초기화된 이미지
- **입력값**: 
  - `image_id`: 커스텀 제한이 없는 이미지
- **기대 출력값**: 
  - 성공 (멱등성)
- **동작 근거**: 
  - 중복 초기화 허용

### 8. Alias Image

#### 기능 설명
기존 이미지에 별칭을 생성합니다.

#### 테스트 케이스

##### 8.1 새 별칭 생성
- **입력값**: 
  - `alias`: "my-tensorflow"
  - `target`: "tensorflow/tensorflow:2.10.0-gpu"
  - `architecture`: "x86_64"
- **기대 출력값**: 
  - 별칭 생성 성공
- **동작 근거**: 
  - 사용자 친화적 이름 제공

##### 8.2 중복 별칭
- **입력값**: 
  - `alias`: "existing-alias"
  - `target`: "new-image:latest"
- **기대 출력값**: 
  - `AliasAlreadyExists` 예외
- **동작 근거**: 
  - 별칭은 고유해야 함

##### 8.3 순환 별칭
- **입력값**: 
  - `alias`: "alias-a"
  - `target`: "alias-b" (alias-b → alias-a)
- **기대 출력값**: 
  - `CircularAlias` 예외
- **동작 근거**: 
  - 순환 참조 방지

##### 8.4 존재하지 않는 대상
- **입력값**: 
  - `alias`: "new-alias"
  - `target`: "non-existent:latest"
- **기대 출력값**: 
  - `TargetImageNotFound` 예외
- **동작 근거**: 
  - 유효한 대상만 별칭 가능

### 9. Dealias Image

#### 기능 설명
이미지 별칭을 제거합니다.

#### 테스트 케이스

##### 9.1 별칭 제거
- **입력값**: 
  - `alias`: "my-tensorflow"
- **기대 출력값**: 
  - 별칭 삭제 성공
- **동작 근거**: 
  - 더 이상 필요 없는 별칭 정리

##### 9.2 존재하지 않는 별칭
- **입력값**: 
  - `alias`: "non-existent-alias"
- **기대 출력값**: 
  - `AliasNotFound` 예외
- **동작 근거**: 
  - 없는 별칭은 제거 불가

##### 9.3 여러 별칭 중 하나 제거
- **입력값**: 
  - 같은 대상을 가리키는 여러 별칭 중 하나
- **기대 출력값**: 
  - 해당 별칭만 제거
  - 다른 별칭은 유지
- **동작 근거**: 
  - 독립적인 별칭 관리

### 10. Untag Image from Registry

#### 기능 설명
컨테이너 레지스트리에서 이미지 태그를 제거합니다.

#### 테스트 케이스

##### 10.1 태그 제거
- **입력값**: 
  - `image_id`: UUID("valid-image-id")
  - `registry`: "docker.io"
- **기대 출력값**: 
  - 레지스트리에서 태그 제거
- **동작 근거**: 
  - 레지스트리 정리

##### 10.2 권한 없는 레지스트리
- **입력값**: 
  - `image_id`: UUID("valid-image-id")
  - `registry`: "unauthorized-registry"
- **기대 출력값**: 
  - `RegistryAuthorizationError` 예외
- **동작 근거**: 
  - 레지스트리 쓰기 권한 필요

##### 10.3 레지스트리 API 오류
- **입력값**: 
  - 유효한 이미지 ID
  - 레지스트리 API 장애
- **기대 출력값**: 
  - `RegistryAPIError` 예외
- **동작 근거**: 
  - 외부 서비스 장애 처리

## 공통 에러 케이스

### 데이터베이스 연결 실패
- **상황**: 데이터베이스 연결 불가
- **기대 동작**: 
  - 데이터베이스 연결 에러
  - 모든 작업 실패

### 에이전트 통신 실패
- **상황**: 에이전트와 통신 불가
- **기대 동작**: 
  - 에이전트 연결 에러
  - purge 작업 실패

### 권한 검증 실패
- **상황**: 사용자 권한 부족
- **기대 동작**: 
  - PermissionDenied 예외
  - 작업 차단

