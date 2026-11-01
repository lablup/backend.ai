# 인증 서비스: 배경

## 그룹이 둘인 이유

`global` 그룹은 어떤 엔티티도 지정하지 않는 동작을 맡는다. 로그인과 만료 비밀번호 교체는
호출자가 아직 주체를 갖지 않은 채 들어온다. 관리자의 로그인 세션 회수와 로그인 차단 해제는
소유자를 읽지 않는다. `user` 그룹은 한 사용자의 row, 자격 증명, 로그인 기록에 대한 동작을
처리한다.

## gate 없는 세 연결

`authorize`, `signup`, `update_password_no_auth` 는 `anonymous_global` 로 연결된다.
셋 다 인증 미들웨어가 없는 라우트(`api/rest/auth/registry.py`)에 걸려 있어 확인할
호출자 맥락 자체가 없다. 대신 서비스가 호출자를 직접 확인한다. 비밀번호는 row 가
보관한 비밀과 대조한다. `signup` 은 대조할 row 가 아직 없고, 훅 플러그인이 가입 요청을
판정한다.

`logout` 은 여기 들지 않는다. 로그아웃하는 호출자는 이미 세션을 가지고 있으므로
라우트가 인증을 요구하고, action 은 그 사용자를 지정한다. 세션 토큰은 그대로
끝낼 세션을 고르는 값으로 남는다.

## 역할 조회와 access key 스코프 해석

`get_role` 은 요청자 자신을 지정하는 `single_entity` GET 이다.

`public_resolve_access_key_scope` 는 access key 로 keypair 소유자를 찾는 lookup 에 요청자의
기본 keypair 읽기와 위임 자격 검사가 섞여 있어 lookup 으로 연결하지 못한다. 다루는 엔티티가
user 이므로 user 그룹의 public 이다. 위임 대상을 지정하는 경우는 서비스가 요청자와 대상의
역할과 도메인을 비교해 판정한다.

## 로그인 세션과 SSH 키페어는 사용자로 기록된다

두 row 모두 자기 소속을 갖지 않고 own 하는 사용자를 통해서만 읽힌다. 그래서 사용자를
지정한 조작인 로그아웃, 세션 회수, SSH 키페어 발급과 업로드는 `single_entity` 로 그 사용자를
지정하고 `UPDATE` 를 선언한다. `DELETE` 를 선언하면 사용자 자체를 삭제한다는 의미가 되고,
권한도 그것으로 확인된다. 계정을 비활성화하는 `signout` 만 `DELETE` 다.

관리자 쪽 회수(`global_revoke_login_session`)는 소유자를 읽지 않으므로 사용자를 지정할
수 없고, SUPERADMIN gate 뒤의 global 이다.

## 사용자 도메인의 SSH 키페어 action 과의 관계

`services/user` 의 `admin_get_ssh_keypair`, `admin_register_ssh_keypair`,
`admin_delete_ssh_keypair` 는 관리자가 다른 사용자의 키페어를 지정하는 경로다. 여기의
`get_ssh_keypair`, `generate_ssh_keypair`, `upload_ssh_keypair` 는 로그인한 사용자가
자기 세션의 액세스 키에 대해 하는 조작이고, 키 생성은 이쪽에만 있다.

## 로그인 세션과 이력은 사용자의 field group 이다

두 row 모두 사용자가 own 하는 field row 이므로 조회는 `user_group.field_group(...)` 이
제공하는 하위 그룹에서 나온다. 소유자 lookup 은 그 그룹이 스스로 생성하고, 도메인은 조회
네 건만 연결한다. 네 건 다 서비스 메서드 없이 `LoginSessionSearcher`,
`LoginHistorySearcher` 스펙으로 ops 를 거친다.

스코프 조회가 `scope_search_ops` 가 아닌 이유는 그 결과의 데이터가
`EntityData` 여야 하기 때문이다. field row 는 엔티티가 아니라서 반환할 id 가 없고,
`ScopedFieldsOpsResult` 가 그 항목을 맡는다.

없는 사용자로 스코프 조회를 하면 ops 가 스코프의 존재 검사를 먼저 실행하므로 `UserNotFound`
가 그대로 난다.
