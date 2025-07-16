# VFolder Service Test Scenarios

## 서비스 개요
VFolder 서비스는 Backend.AI의 가상 폴더(스토리지 볼륨)를 관리하는 핵심 서비스입니다.
파일 저장소 생성, 파일 작업, 공유 및 권한 관리 등의 기능을 제공합니다.

## 주요 기능 목록

### VFolder 관리
1. Create - 새로운 가상 폴더 생성
   - Action: `CreateVFolderAction`
   - Result: `CreateVFolderActionResult`
2. Update Attribute - VFolder 속성 수정
   - Action: `UpdateVFolderAttributeAction`
   - Result: `UpdateVFolderAttributeActionResult`
3. Get - VFolder 정보 및 사용량 조회
   - Action: `GetVFolderAction`
   - Result: `GetVFolderActionResult`
4. List - 접근 가능한 VFolder 목록
   - Action: `ListVFolderAction`
   - Result: `ListVFolderActionResult`
5. Move to Trash - 휴지통으로 이동
   - Action: `MoveToTrashVFolderAction`
   - Result: `MoveToTrashVFolderActionResult`
6. Restore - 휴지통에서 복원
   - Action: `RestoreVFolderFromTrashAction`
   - Result: `RestoreVFolderFromTrashActionResult`
7. Delete Forever - 영구 삭제
   - Action: `DeleteForeverVFolderAction`
   - Result: `DeleteForeverVFolderActionResult`
8. Force Delete - 강제 삭제
   - Action: `ForceDeleteVFolderAction`
   - Result: `ForceDeleteVFolderActionResult`
9. Clone - VFolder 복제
   - Action: `CloneVFolderAction`
   - Result: `CloneVFolderActionResult`
10. Get Task Logs - 백그라운드 작업 로그
   - Action: `GetTaskLogsAction`
   - Result: `GetTaskLogsActionResult`

### 파일 작업
11. Upload File - 파일 업로드
   - Action: `CreateUploadSessionAction`
   - Result: `CreateUploadSessionActionResult`
12. Download File - 파일 다운로드
   - Action: `CreateDownloadSessionAction`
   - Result: `CreateDownloadSessionActionResult`
13. List Files - 파일 목록 조회
   - Action: `ListFilesAction`
   - Result: `ListFilesActionResult`
14. Rename File - 파일/디렉토리 이름 변경
   - Action: `RenameFileAction`
   - Result: `RenameFileActionResult`
15. Delete Files - 파일/디렉토리 삭제
   - Action: `DeleteFilesAction`
   - Result: `DeleteFilesActionResult`
16. Mkdir - 디렉토리 생성
   - Action: `MkdirAction`
   - Result: `MkdirActionResult`

### 공유 및 권한
17. Invite - VFolder 공유 초대
   - Action: `InviteVFolderAction`
   - Result: `InviteVFolderActionResult`
18. Accept Invitation - 초대 수락
   - Action: `AcceptInvitationAction`
   - Result: `AcceptInvitationActionResult`
19. Reject Invitation - 초대 거절
   - Action: `RejectInvitationAction`
   - Result: `RejectInvitationActionResult`
20. Update Invitation - 공유 권한 수정
   - Action: `UpdateInvitationAction`
   - Result: `UpdateInvitationActionResult`
21. List Invitation - 초대 목록 조회
   - Action: `ListInvitationAction`
   - Result: `ListInvitationActionResult`
22. Leave Invited VFolder - 공유 폴더 나가기
   - Action: `LeaveInvitedVFolderAction`
   - Result: `LeaveInvitedVFolderActionResult`

## 테스트 시나리오

### 1. Create VFolder

#### 기능 설명
새로운 가상 폴더를 생성합니다.

#### 테스트 케이스

##### 1.1 개인 VFolder 생성
- **입력값**: 
  - `name`: "my-workspace"
  - `host`: "storage1"
  - `quota`: 10737418240 (10GB)
  - `usage_mode`: "general"
  - `permission`: "rw"
- **기대 출력값**: 
  - 생성된 VFolder ID
  - 실제 경로
  - 초기 사용량: 0
- **동작 근거**: 
  - 개인 작업 공간 생성

##### 1.2 프로젝트 VFolder 생성
- **입력값**: 
  - `name`: "team-data"
  - `group_id`: UUID("project-id")
  - `quota`: 107374182400 (100GB)
  - `usage_mode`: "data"
  - `cloneable`: true
- **기대 출력값**: 
  - 프로젝트 소유 VFolder
  - 팀원 자동 접근 권한
- **동작 근거**: 
  - 팀 공유 스토리지

##### 1.3 모델 저장소 생성
- **입력값**: 
  - `name`: "ml-models"
  - `usage_mode`: "model"
  - `permission`: "ro"
- **기대 출력값**: 
  - 읽기 전용 모델 저장소
  - 모델 서빙 가능
- **동작 근거**: 
  - 모델 배포용 스토리지

##### 1.4 중복 이름
- **입력값**: 
  - `name`: "existing-folder"
  - 동일 소유자
- **기대 출력값**: 
  - `VFolderAlreadyExists` 예외
- **동작 근거**: 
  - 소유자별 고유 이름

##### 1.5 할당량 초과
- **입력값**: 
  - `quota`: 10995116277760 (10TB)
  - 사용자 할당량: 1TB
- **기대 출력값**: 
  - `QuotaExceeded` 예외
- **동작 근거**: 
  - 리소스 정책 준수

##### 1.6 Unmanaged VFolder
- **입력값**: 
  - `unmanaged_path`: "/mnt/external/data"
  - `name`: "external-data"
- **기대 출력값**: 
  - 외부 경로 마운트
  - 할당량 관리 없음
- **동작 근거**: 
  - 기존 데이터 접근

### 2. Upload File

#### 기능 설명
VFolder에 파일을 업로드합니다.

#### 테스트 케이스

##### 2.1 단일 파일 업로드
- **입력값**: 
  - `vfolder_id`: UUID("valid-vfolder")
  - `file`: "data.csv" (1MB)
  - `path`: "/datasets/"
- **기대 출력값**: 
  - 업로드 세션 토큰
  - 청크 업로드 지원
- **동작 근거**: 
  - 표준 파일 업로드

##### 2.2 대용량 파일 업로드
- **입력값**: 
  - `file`: "model.h5" (5GB)
  - `chunk_size`: 10485760 (10MB)
- **기대 출력값**: 
  - 멀티파트 업로드
  - 진행률 추적 가능
- **동작 근거**: 
  - 대용량 파일 지원

##### 2.3 디렉토리 업로드
- **입력값**: 
  - `directory`: "project/" (여러 파일)
  - `preserve_structure`: true
- **기대 출력값**: 
  - 디렉토리 구조 유지
  - 모든 파일 업로드
- **동작 근거**: 
  - 프로젝트 전체 업로드

##### 2.4 권한 없는 업로드
- **입력값**: 
  - VFolder with "ro" permission
- **기대 출력값**: 
  - `PermissionDenied` 예외
- **동작 근거**: 
  - 읽기 전용 보호

##### 2.5 할당량 초과
- **입력값**: 
  - 남은 용량: 100MB
  - 파일 크기: 200MB
- **기대 출력값**: 
  - `QuotaExceeded` 예외
- **동작 근거**: 
  - 스토리지 제한 강제

### 3. List Files

#### 기능 설명
VFolder 내의 파일과 디렉토리를 조회합니다.

#### 테스트 케이스

##### 3.1 루트 디렉토리 조회
- **입력값**: 
  - `vfolder_id`: UUID("valid-vfolder")
  - `path`: "/"
- **기대 출력값**: 
  - 파일/디렉토리 목록
  - 각 항목의 크기, 수정일
- **동작 근거**: 
  - 기본 파일 탐색

##### 3.2 재귀적 조회
- **입력값**: 
  - `path`: "/data"
  - `recursive`: true
- **기대 출력값**: 
  - 하위 모든 파일
  - 트리 구조 정보
- **동작 근거**: 
  - 전체 구조 파악

##### 3.3 필터링 및 정렬
- **입력값**: 
  - `pattern`: "*.csv"
  - `sort_by`: "size"
  - `order`: "desc"
- **기대 출력값**: 
  - CSV 파일만
  - 크기 역순 정렬
- **동작 근거**: 
  - 효율적인 파일 검색

##### 3.4 숨김 파일 표시
- **입력값**: 
  - `show_hidden`: true
- **기대 출력값**: 
  - 점(.)으로 시작하는 파일 포함
- **동작 근거**: 
  - 설정 파일 접근

### 4. Clone VFolder

#### 기능 설명
기존 VFolder를 복제합니다.

#### 테스트 케이스

##### 4.1 전체 복제
- **입력값**: 
  - `source_vfolder_id`: UUID("cloneable-vfolder")
  - `target_name`: "cloned-folder"
  - `target_host`: "storage1"
- **기대 출력값**: 
  - 새 VFolder 생성
  - 모든 파일 복사
  - 메타데이터 유지
- **동작 근거**: 
  - 백업 또는 실험

##### 4.2 선택적 복제
- **입력값**: 
  - `include_patterns`: ["*.py", "*.ipynb"]
  - `exclude_patterns`: ["__pycache__"]
- **기대 출력값**: 
  - 특정 파일만 복제
- **동작 근거**: 
  - 필요한 파일만 복사

##### 4.3 권한 없는 복제
- **입력값**: 
  - Non-cloneable VFolder
- **기대 출력값**: 
  - `NotCloneable` 예외
- **동작 근거**: 
  - 복제 권한 제어

##### 4.4 크로스 호스트 복제
- **입력값**: 
  - `source_host`: "storage1"
  - `target_host`: "storage2"
- **기대 출력값**: 
  - 다른 스토리지로 복사
  - 네트워크 전송
- **동작 근거**: 
  - 스토리지 마이그레이션

### 5. Invite to VFolder

#### 기능 설명
다른 사용자에게 VFolder 접근 권한을 부여합니다.

#### 테스트 케이스

##### 5.1 읽기 권한 초대
- **입력값**: 
  - `vfolder_id`: UUID("my-vfolder")
  - `invitee_emails`: ["colleague@example.com"]
  - `permission`: "ro"
- **기대 출력값**: 
  - 초대 생성
  - 이메일 알림 (선택적)
- **동작 근거**: 
  - 데이터 공유

##### 5.2 쓰기 권한 초대
- **입력값**: 
  - `permission`: "rw"
  - `invitee_emails`: ["team@example.com"]
- **기대 출력값**: 
  - 읽기/쓰기 권한 부여
- **동작 근거**: 
  - 협업 지원

##### 5.3 삭제 권한 포함
- **입력값**: 
  - `permission`: "rwd"
- **기대 출력값**: 
  - 전체 권한 부여
  - 파일 삭제 가능
- **동작 근거**: 
  - 완전한 제어권

##### 5.4 대량 초대
- **입력값**: 
  - `invitee_emails`: ["user1@example.com", "user2@example.com", ...]
- **기대 출력값**: 
  - 배치 초대 처리
- **동작 근거**: 
  - 팀 전체 공유

##### 5.5 중복 초대
- **입력값**: 
  - 이미 초대된 사용자
- **기대 출력값**: 
  - 권한 업데이트 또는 에러
- **동작 근거**: 
  - 권한 변경 처리

### 6. Move to Trash

#### 기능 설명
VFolder를 휴지통으로 이동합니다.

#### 테스트 케이스

##### 6.1 정상적인 삭제
- **입력값**: 
  - `vfolder_id`: UUID("unused-vfolder")
- **기대 출력값**: 
  - 상태: "trash"
  - 30일 후 자동 삭제 예정
- **동작 근거**: 
  - 실수 방지

##### 6.2 마운트된 VFolder
- **입력값**: 
  - 세션에 마운트된 VFolder
- **기대 출력값**: 
  - `VFolderInUse` 예외
- **동작 근거**: 
  - 사용 중 보호

##### 6.3 공유 VFolder 삭제
- **입력값**: 
  - 다른 사용자와 공유 중
- **기대 출력값**: 
  - 소유자만 삭제 가능
  - 공유 해제 알림
- **동작 근거**: 
  - 소유권 존중

### 7. Get Task Logs

#### 기능 설명
VFolder 관련 백그라운드 작업의 로그를 조회합니다.

#### 테스트 케이스

##### 7.1 복제 작업 로그
- **입력값**: 
  - `task_id`: UUID("clone-task-id")
- **기대 출력값**: 
  - 복제 진행률
  - 완료/실패 상태
  - 상세 로그
- **동작 근거**: 
  - 장시간 작업 추적

##### 7.2 삭제 작업 로그
- **입력값**: 
  - `task_id`: UUID("delete-task-id")
- **기대 출력값**: 
  - 삭제된 파일 수
  - 해제된 용량
- **동작 근거**: 
  - 작업 확인


## 공통 에러 케이스

### 스토리지 장애
- **상황**: 스토리지 호스트 다운
- **기대 동작**: 
  - 명확한 에러 메시지
  - 다른 호스트 제안

### 동시성 충돌
- **상황**: 동시 파일 수정
- **기대 동작**: 
  - 락 메커니즘
  - 충돌 해결 옵션

### 권한 에스컬레이션
- **상황**: 낮은 권한으로 높은 권한 작업 시도
- **기대 동작**: 
  - 권한 검증
  - 감사 로그

