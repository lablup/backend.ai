# Auth Service Test Scenarios

## 서비스 개요
Auth 서비스는 Backend.AI의 사용자 인증 및 권한 관리를 담당하는 핵심 서비스입니다.
사용자 로그인, 회원가입, 비밀번호 관리, SSH 키 관리, 역할 조회 등의 기능을 제공합니다.

## 주요 기능 목록
1. Authorize - 사용자 인증 및 액세스 토큰 발급
   - Action: `AuthorizeAction`
   - Result: `AuthorizeActionResult`
2. Signup - 신규 사용자 등록
   - Action: `SignupAction`
   - Result: `SignupActionResult`
3. Signout - 사용자 계정 비활성화
   - Action: `SignoutAction`
   - Result: `SignoutActionResult`
4. Update Full Name - 사용자 이름 변경
   - Action: `UpdateFullNameAction`
   - Result: `UpdateFullNameActionResult`
5. Update Password - 비밀번호 변경
   - Action: `UpdatePasswordAction`
   - Result: `UpdatePasswordActionResult`
6. Update Password No Auth - 만료된 비밀번호 변경
   - Action: `UpdatePasswordNoAuthAction`
   - Result: `UpdatePasswordNoAuthActionResult`
7. Get Role - 사용자 역할 조회
   - Action: `GetRoleAction`
   - Result: `GetRoleActionResult`
8. Get SSH Keypair - SSH 공개키 조회
   - Action: `GetSSHKeypairAction`
   - Result: `GetSSHKeypairActionResult`
9. Generate SSH Keypair - SSH 키 쌍 생성
   - Action: `GenerateSSHKeypairAction`
   - Result: `GenerateSSHKeypairActionResult`
10. Upload SSH Keypair - SSH 키 쌍 업로드
    - Action: `UploadSSHKeypairAction`
    - Result: `UploadSSHKeypairActionResult`

## 테스트 시나리오

### 1. Authorize

#### 기능 설명
사용자 인증을 수행하고 API 접근을 위한 액세스 토큰(access_key/secret_key)을 발급합니다.

#### 테스트 케이스

##### 1.1 정상적인 로그인
- **입력값**: 
  - `auth_type`: "keypair"
  - `domain`: "default"
  - `email`: "user@example.com"
  - `password`: "valid_password"
- **기대 출력값**: 
  - `type`: "authorize"
  - `access_key`: 생성된 액세스 키
  - `secret_key`: 생성된 시크릿 키
  - `role`: 사용자 역할
  - `need_password_change`: false
- **동작 근거**: 
  - 유효한 자격증명으로 인증 성공
  - 새로운 keypair 생성 및 반환

##### 1.2 잘못된 비밀번호
- **입력값**: 
  - `auth_type`: "keypair"
  - `domain`: "default"
  - `email`: "user@example.com"
  - `password`: "wrong_password"
- **기대 출력값**: 
  - `AuthorizationFailed` 예외
- **동작 근거**: 
  - 비밀번호 검증 실패
  - 보안상 구체적인 실패 이유 숨김

##### 1.3 존재하지 않는 사용자
- **입력값**: 
  - `auth_type`: "keypair"
  - `domain`: "default"
  - `email`: "nonexistent@example.com"
  - `password`: "any_password"
- **기대 출력값**: 
  - `UserNotFound` 예외
- **동작 근거**: 
  - 데이터베이스에 해당 이메일의 사용자 없음

##### 1.4 비활성화된 사용자
- **입력값**: 
  - `auth_type`: "keypair"
  - `domain`: "default"
  - `email`: "inactive@example.com"
  - `password`: "valid_password"
- **기대 출력값**: 
  - `AuthorizationFailed` 예외 (status=INACTIVE)
- **동작 근거**: 
  - 사용자 상태가 INACTIVE인 경우 로그인 불가

##### 1.5 비밀번호 만료
- **입력값**: 
  - `auth_type`: "keypair"
  - `domain`: "default"
  - `email`: "user@example.com"
  - `password`: "old_password"
  - 비밀번호 변경일이 만료 기간 초과
- **기대 출력값**: 
  - `type`: "authorize"
  - `need_password_change`: true
  - `access_key`, `secret_key` 포함
- **동작 근거**: 
  - 비밀번호 만료 정책이 설정된 경우
  - 로그인은 허용하되 비밀번호 변경 필요 표시

##### 1.6 플러그인 훅에 의한 거부
- **입력값**: 
  - 유효한 자격증명
  - AUTHORIZE 훅이 거부 응답 반환
- **기대 출력값**: 
  - `RejectedByHook` 예외
- **동작 근거**: 
  - 외부 인증 시스템이나 정책에 의한 거부

### 2. Signup

#### 기능 설명
새로운 사용자를 등록하고 초기 API 키페어를 생성합니다.

#### 테스트 케이스

##### 2.1 정상적인 회원가입
- **입력값**: 
  - `domain`: "default"
  - `email`: "newuser@example.com"
  - `password`: "SecurePass123!"
  - `username`: "newuser"
  - `full_name`: "New User"
  - `group_id`: null (기본 그룹 사용)
- **기대 출력값**: 
  - `user_id`: 생성된 사용자 UUID
  - `access_key`: 초기 액세스 키
  - `secret_key`: 초기 시크릿 키
- **동작 근거**: 
  - 모든 필수 정보 제공
  - 이메일 중복 없음
  - 비밀번호 정책 만족

##### 2.2 중복 이메일
- **입력값**: 
  - `email`: "existing@example.com" (이미 존재하는 이메일)
  - 기타 유효한 정보
- **기대 출력값**: 
  - `DuplicatedEmail` 예외 또는 데이터베이스 무결성 에러
- **동작 근거**: 
  - 이메일은 고유해야 함

##### 2.3 약한 비밀번호
- **입력값**: 
  - `password`: "123" (정책 위반)
  - 기타 유효한 정보
- **기대 출력값**: 
  - `PasswordFormatViolation` 예외
- **동작 근거**: 
  - VERIFY_PASSWORD_FORMAT 훅에 의한 검증 실패

##### 2.4 잘못된 그룹 ID
- **입력값**: 
  - `group_id`: "invalid-group-id"
  - 기타 유효한 정보
- **기대 출력값**: 
  - `GroupNotFound` 예외
- **동작 근거**: 
  - 존재하지 않는 그룹에 사용자 할당 불가

##### 2.5 도메인 제한
- **입력값**: 
  - `domain`: "restricted" (회원가입 제한된 도메인)
  - 기타 유효한 정보
- **기대 출력값**: 
  - `DomainNotAllowed` 예외
- **동작 근거**: 
  - 도메인별 회원가입 정책

### 3. Signout

#### 기능 설명
사용자 계정을 비활성화하고 모든 API 키를 무효화합니다.

#### 테스트 케이스

##### 3.1 정상적인 계정 비활성화
- **입력값**: 
  - `email`: "user@example.com"
  - `password`: "correct_password"
- **기대 출력값**: 
  - 성공 (빈 응답)
  - 사용자 상태: INACTIVE
  - 모든 키페어 비활성화
- **동작 근거**: 
  - 비밀번호 확인 후 계정 비활성화

##### 3.2 잘못된 비밀번호
- **입력값**: 
  - `email`: "user@example.com"
  - `password`: "wrong_password"
- **기대 출력값**: 
  - `AuthorizationFailed` 예외
- **동작 근거**: 
  - 보안을 위해 비밀번호 검증 필수

##### 3.3 이미 비활성화된 계정
- **입력값**: 
  - 이미 INACTIVE 상태인 사용자 정보
- **기대 출력값**: 
  - `UserNotFound` 또는 성공 (멱등성)
- **동작 근거**: 
  - 이미 비활성화된 계정 처리

### 4. Update Full Name

#### 기능 설명
사용자의 전체 이름을 변경합니다.

#### 테스트 케이스

##### 4.1 정상적인 이름 변경
- **입력값**: 
  - `email`: "user@example.com"
  - `full_name`: "Updated Name"
- **기대 출력값**: 
  - 성공 (빈 응답)
- **동작 근거**: 
  - 단순 프로필 업데이트

##### 4.2 너무 긴 이름
- **입력값**: 
  - `email`: "user@example.com"
  - `full_name`: 256자 이상의 문자열
- **기대 출력값**: 
  - 데이터베이스 제약조건 에러
- **동작 근거**: 
  - 컬럼 크기 제한

### 5. Update Password

#### 기능 설명
현재 비밀번호를 확인한 후 새 비밀번호로 변경합니다.

#### 테스트 케이스

##### 5.1 정상적인 비밀번호 변경
- **입력값**: 
  - `email`: "user@example.com"
  - `old_password`: "current_password"
  - `new_password`: "NewSecurePass123!"
- **기대 출력값**: 
  - 성공 (빈 응답)
  - `password_changed_at` 업데이트
- **동작 근거**: 
  - 현재 비밀번호 확인 후 변경

##### 5.2 현재 비밀번호 불일치
- **입력값**: 
  - `email`: "user@example.com"
  - `old_password`: "wrong_current"
  - `new_password`: "NewSecurePass123!"
- **기대 출력값**: 
  - `AuthorizationFailed` 예외
- **동작 근거**: 
  - 보안을 위한 현재 비밀번호 검증

##### 5.3 동일한 비밀번호로 변경
- **입력값**: 
  - `old_password`와 `new_password`가 동일
- **기대 출력값**: 
  - `SamePasswordError` 예외 또는 정책 위반
- **동작 근거**: 
  - 비밀번호 재사용 방지 정책

##### 5.4 비밀번호 형식 위반
- **입력값**: 
  - `new_password`: "weak"
- **기대 출력값**: 
  - `PasswordFormatViolation` 예외
- **동작 근거**: 
  - VERIFY_PASSWORD_FORMAT 훅 검증

### 6. Update Password No Auth

#### 기능 설명
만료된 비밀번호를 변경할 때 사용하는 특수 엔드포인트입니다.

#### 테스트 케이스

##### 6.1 만료된 비밀번호 변경
- **입력값**: 
  - `email`: "user@example.com"
  - `old_password`: "expired_password"
  - `new_password`: "NewSecurePass123!"
  - 사용자의 비밀번호가 만료 상태
- **기대 출력값**: 
  - 성공 (빈 응답)
  - 새 비밀번호로 변경
- **동작 근거**: 
  - 만료 상태에서도 비밀번호 변경 허용

##### 6.2 만료되지 않은 비밀번호
- **입력값**: 
  - 비밀번호가 만료되지 않은 사용자 정보
- **기대 출력값**: 
  - `PasswordNotExpired` 예외 또는 거부
- **동작 근거**: 
  - 일반 비밀번호 변경 사용 강제

### 7. Get Role

#### 기능 설명
사용자의 글로벌, 도메인, 그룹 레벨 역할을 조회합니다.

#### 테스트 케이스

##### 7.1 일반 사용자 역할 조회
- **입력값**: 
  - `email`: "user@example.com"
- **기대 출력값**: 
  - `global_role`: "user"
  - `domain_role`: "user"
  - `group_role`: "user"
- **동작 근거**: 
  - 일반 사용자의 기본 역할

##### 7.2 도메인 관리자 역할 조회
- **입력값**: 
  - `email`: "domain_admin@example.com"
- **기대 출력값**: 
  - `global_role`: "user"
  - `domain_role`: "admin"
  - `group_role`: "user"
- **동작 근거**: 
  - 도메인 관리자 권한 반영

##### 7.3 슈퍼관리자 역할 조회
- **입력값**: 
  - `email`: "superadmin@example.com"
- **기대 출력값**: 
  - `global_role`: "superadmin"
  - `domain_role`: "admin"
  - `group_role`: "user"
- **동작 근거**: 
  - 최고 권한 사용자

### 8. Get SSH Keypair

#### 기능 설명
사용자의 SSH 공개키를 조회합니다.

#### 테스트 케이스

##### 8.1 SSH 키가 있는 경우
- **입력값**: 
  - `email`: "user@example.com"
  - 사용자가 SSH 키 보유
- **기대 출력값**: 
  - `ssh_public_key`: "ssh-rsa AAAA..."
- **동작 근거**: 
  - 저장된 SSH 공개키 반환

##### 8.2 SSH 키가 없는 경우
- **입력값**: 
  - `email`: "user@example.com"
  - SSH 키 미등록 상태
- **기대 출력값**: 
  - `ssh_public_key`: null 또는 빈 문자열
- **동작 근거**: 
  - SSH 키는 선택사항

### 9. Generate SSH Keypair

#### 기능 설명
새로운 SSH 키 쌍을 생성하고 저장합니다.

#### 테스트 케이스

##### 9.1 새 SSH 키 생성
- **입력값**: 
  - `email`: "user@example.com"
- **기대 출력값**: 
  - `ssh_public_key`: 생성된 공개키
  - `ssh_private_key`: 생성된 개인키
- **동작 근거**: 
  - RSA 2048비트 키 쌍 생성

##### 9.2 기존 SSH 키 덮어쓰기
- **입력값**: 
  - `email`: "user@example.com"
  - 이미 SSH 키가 있는 사용자
- **기대 출력값**: 
  - 새로 생성된 키 쌍
  - 기존 키 대체
- **동작 근거**: 
  - 키 재생성 허용

### 10. Upload SSH Keypair

#### 기능 설명
사용자가 제공한 SSH 키 쌍을 검증하고 저장합니다.

#### 테스트 케이스

##### 10.1 유효한 키 쌍 업로드
- **입력값**: 
  - `email`: "user@example.com"
  - `ssh_public_key`: "ssh-rsa AAAA... user@host"
  - `ssh_private_key`: "-----BEGIN RSA PRIVATE KEY-----..."
- **기대 출력값**: 
  - 성공 (빈 응답)
- **동작 근거**: 
  - 공개키와 개인키가 매칭됨

##### 10.2 매칭되지 않는 키 쌍
- **입력값**: 
  - `ssh_public_key`: 한 키 쌍의 공개키
  - `ssh_private_key`: 다른 키 쌍의 개인키
- **기대 출력값**: 
  - `InvalidSSHKeypair` 예외
- **동작 근거**: 
  - 키 쌍 호환성 검증 실패

##### 10.3 잘못된 키 형식
- **입력값**: 
  - `ssh_public_key`: "invalid key format"
  - `ssh_private_key`: "invalid private key"
- **기대 출력값**: 
  - `InvalidSSHKeypair` 예외
- **동작 근거**: 
  - SSH 키 형식 검증 실패

## 공통 에러 케이스

### 데이터베이스 연결 실패
- **상황**: 데이터베이스 서버 다운 또는 연결 문제
- **기대 동작**: 
  - 데이터베이스 연결 에러 발생
  - 모든 작업 실패

### 플러그인 시스템 오류
- **상황**: 훅 플러그인 실행 중 예외 발생
- **기대 동작**: 
  - 적절한 에러 처리
  - 기본 동작으로 폴백 또는 실패

### 동시성 문제
- **상황**: 동일 사용자에 대한 동시 요청
- **기대 동작**: 
  - 트랜잭션 격리로 데이터 일관성 유지
  - 필요시 재시도

