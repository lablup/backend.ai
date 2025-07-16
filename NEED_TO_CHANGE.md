# VFolder Service 호환성 문제 및 수정 필요 사항

## 개요
코드 레이어 분리 작업 후 VFolder 서비스의 현재 구현체와 레거시 구현체 간의 호환성 문제를 분석한 결과, 다음과 같은 주요 문제점들이 발견되었습니다.

## 1. File Service 호환성 문제

### 1.1 권한 검증 누락
**문제점**: 
- 현재 구현체에서 `ensure_host_permission_allowed` 검증이 TODO 주석으로 처리되어 있음
- 파일 업로드, 다운로드, 이름 변경 등의 작업에서 호스트 권한 검증이 누락됨

**영향도**: 높음 - 보안 취약점 발생 가능

**수정 필요 사항**:
```python
# services/vfolder/services/file.py
async def upload_file(self, action: CreateUploadSessionAction) -> CreateUploadSessionActionResult:
    # TODO: 권한 서비스 구현 후 아래 주석 해제
    # await self.permission_service.ensure_host_permission_allowed(
    #     vfolder_info["host"],
    #     action.keypair_resource_policy,
    # )
```

### 1.2 리포지토리 패턴 마이그레이션 불완전
**문제점**:
- 레거시: 직접 DB 접근 (`ExtendedAsyncSAEngine`)
- 현재: 리포지토리 패턴 사용하나 필수 기능 누락

**수정 필요 사항**:
- 리포지토리에 권한 검증 메서드 추가
- 리소스 정책 검증 로직 구현

## 2. Invite Service 호환성 문제

### 2.1 반환 타입 불일치
**문제점**:
- 레거시: `invite()` 메서드가 이메일 문자열 반환
- 현재: UUID 반환

**영향도**: 높음 - 기존 클라이언트 호환성 깨짐

**수정 필요 사항**:
```python
# 현재 구현
invitation_ids: list[uuid.UUID]

# 수정 필요
invitation_ids: list[str]  # 이메일 주소 반환하도록 변경
```

### 2.2 권한 검증 미구현
**문제점**: 초대 권한 검증이 TODO로 표시되어 있음

**수정 필요 사항**: 권한 서비스 구현 및 통합

## 3. VFolder Service 호환성 문제

### 3.1 Clone 기능 미구현
**문제점**: 
- `clone()` 메서드가 플레이스홀더 데이터만 반환
- 실제 복제 작업이 구현되지 않음

**영향도**: 높음 - 핵심 기능 작동 불가

**수정 필요 사항**:
```python
async def clone(self, action: CloneVFolderAction) -> CloneVFolderActionResult:
    # TODO: 실제 복제 로직 구현
    # 1. 소스 VFolder 검증
    # 2. 타겟 VFolder 생성
    # 3. 백그라운드 복사 작업 시작
    # 4. 작업 ID 반환
```

### 3.2 Task Logs 기능 미구현
**문제점**: `get_task_logs()` 메서드가 빈 응답 반환

**영향도**: 중간 - 모니터링 기능 제한

**수정 필요 사항**:
- 백그라운드 작업 추적 시스템 구현
- 로그 저장 및 조회 기능 구현

### 3.3 권한 검증 불완전
**문제점**:
- 삭제 작업에서 admin repository 직접 사용
- 적절한 권한 검증 없음

**수정 필요 사항**:
- 모든 작업에 대한 권한 검증 추가
- 소유권 및 공유 권한 확인

## 4. 공통 문제점

### 4.1 Permission Service 부재
**문제점**: 전체 서비스에서 참조하는 권한 서비스가 구현되지 않음

**수정 필요 사항**:
```python
# services/vfolder/services/permission.py (신규 생성 필요)
class PermissionService:
    async def ensure_host_permission_allowed(self, host: str, policy: Mapping[str, Any]):
        # 호스트 권한 검증 로직
        pass
    
    async def check_vfolder_permission(self, user_id: uuid.UUID, vfolder_id: uuid.UUID, required_perm: VFolderPermission):
        # VFolder 접근 권한 검증
        pass
```

### 4.2 에러 처리 일관성
**문제점**: 레거시 대비 에러 처리가 단순화되어 있음

**수정 필요 사항**:
- 구체적인 예외 타입 정의 및 사용
- 에러 메시지 상세화

## 우선순위 및 실행 계획

### 즉시 수정 필요 (P0)
1. **Invite Service 반환 타입 수정** - 기존 API 호환성
2. **File Service 권한 검증** - 보안 취약점
3. **Permission Service 구현** - 전체 서비스 의존성

### 단기 수정 필요 (P1)
1. **Clone 기능 구현** - 핵심 기능
2. **VFolder 삭제 권한 검증** - 데이터 보호

### 중기 수정 필요 (P2)
1. **Task Logs 구현** - 운영 편의성
2. **에러 처리 개선** - 사용자 경험

## 테스트 전략

1. **기존 API 호환성 테스트**
   - 레거시 클라이언트로 신규 서비스 테스트
   - 반환값 형식 검증

2. **권한 검증 테스트**
   - 비인가 접근 시도
   - 권한 에스컬레이션 방지

3. **기능 완전성 테스트**
   - Clone 작업 end-to-end 테스트
   - 대용량 파일 처리 테스트

## 마이그레이션 가이드

1. **단계적 배포**
   - Permission Service 먼저 배포
   - 각 서비스별 순차 업데이트

2. **호환성 레이어**
   - 임시로 이전 API 형식 지원
   - Deprecation 경고 후 제거

3. **모니터링**
   - 권한 검증 실패 로깅
   - API 호출 패턴 분석