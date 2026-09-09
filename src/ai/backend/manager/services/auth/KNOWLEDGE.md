---
name: auth-service-composition
type: decision-table
description: 인증 도메인의 모든 액션이 왜 user 하나로 답하는지, 게이트 없는 세 배선이 무엇으로 호출자를 확인하는지, 스코프 해석이 왜 lookup 인지, 로그인 세션과 SSH 키페어 조작이 왜 사용자 단위로 기록되는지
scope: src/ai/backend/manager/services/auth
keywords:
  - AuthProcessors
  - UserGlobalAction
  - anonymous_global
  - public_lookup
  - PublicResolveUserScopeAction
  - RevokeLoginSessionAction
sources:
  - src/ai/backend/manager/services/auth/processors.py
  - src/ai/backend/manager/api/rest/auth/registry.py
generated:
  by: claude-code/opus-5
  at: 2026-09-09
status: draft
---

# 인증 서비스

## 그룹이 하나인 이유

- 이 도메인의 액션은 전부 사용자 행이나 사용자가 소유한 행을 다루므로 `user` 하나로 답한다.
- 로그인·인증 없는 비밀번호 변경은 실행 전에 대상 id 가 없지만, 전역 동작은 원래 식별자를
  답하지 않으므로 종류만 user 로 선언한다. 회원가입이 같은 형태다.
- 관리자용 세션 강제 만료와 로그인 차단 해제도 소유자를 읽지 않아 id 가 없다. SUPERADMIN
  게이트 뒤의 전역 동작으로 두고, 무엇을 대상으로 했는지만 user 로 기록한다.

## 게이트 없는 세 배선

`authorize`, `signup`, `update_password_no_auth` 는 `anonymous_global` 로 배선된다.
셋 다 인증 미들웨어가 없는 라우트(`api/rest/auth/registry.py`)에 걸려 있어 확인할
호출자 맥락 자체가 없다. 대신 서비스가 호출자를 직접 확인한다 — 비밀번호, 즉 행이
보관한 비밀과 대조한다. `signup` 은 대조할 행이 아직 없고, 훅 플러그인이 가입 요청을
판정한다.

`logout` 은 여기 들지 않는다. 로그아웃하는 호출자는 이미 세션을 들고 있으므로
라우트가 인증을 요구하고, 액션은 그 사용자를 지목한다. 세션 토큰은 그대로 어느 세션을
끝낼지 고르는 값으로 남는다.

## 인증만 요구하는 세 읽기

- `public_get_role`, `public_resolve_access_key_scope`, `public_resolve_user_scope` 는
  호출자 맥락에서 대상이 정해진다. 지목할 수 있는 대상이 자기 자신뿐이라 권한 확인이
  더할 것이 없고, 인증만 확인한다.
- 위임 대상을 지목하는 경우는 서비스가 요청자와 대상의 역할·도메인을 비교해 판정한다.
  RBAC 이 대신할 수 없어서 `public_lookup` 으로 배선한다 — post-validator 가 붙으면
  이 판정과 이중으로 걸린다.

## 스코프 해석 두 건은 lookup 이다

- 둘 다 요청이 이름 지은 것 — 이메일, 액세스 키, 또는 아무것도 아닌 것 — 을 그 요청이
  대행하는 user 로 바꾼다. 외부 키를 내부 id 로 바꾸는 일이므로 lookup 이다.
- 아무것도 지목하지 않은 요청은 호출자 자신을 뜻하므로 키의 shape 이 다르다.
  `ActingUserKey` · `ActingKeypairKey` 가 그 경우를 맡고, 값을 담는 키와 `kind()` 가
  갈린다.
- 액세스 키 쪽 결과는 키페어의 소유자인 user 를 답한다. 키페어는 field row 라 감사 기록이
  지목할 엔티티가 되지 못한다.

## 로그인 세션과 SSH 키페어는 사용자로 기록된다

두 행 모두 자기 소속을 갖지 않고 소유한 사용자를 통해서만 읽힌다. 그래서 사용자를
지목한 조작 — 로그아웃, 세션 회수, SSH 키페어 발급·업로드 — 은 `single_entity` 로 그 사용자를
지목하고 `UPDATE` 를 선언한다. `DELETE` 를 선언하면 사용자 자체를 지운다는 뜻이 되고,
권한도 그것으로 확인된다. 계정을 비활성화하는 `signout` 만 `DELETE` 다.

관리자 쪽 회수(`global_revoke_login_session`)는 소유자를 읽지 않으므로 사용자를 지목할
수 없고, SUPERADMIN 게이트 뒤의 global 이다.

## 사용자 도메인의 SSH 키페어 액션과의 관계

`services/user` 의 `admin_get_ssh_keypair` · `admin_register_ssh_keypair` ·
`admin_delete_ssh_keypair` 는 관리자가 남의 키페어를 지목하는 경로다. 여기의
`get_ssh_keypair` · `generate_ssh_keypair` · `upload_ssh_keypair` 는 로그인한 사용자가
자기 세션의 액세스 키에 대해 하는 조작이고, 키 생성은 이쪽에만 있다.

## 로그인 세션과 이력은 사용자의 field group 이다

두 행 모두 사용자가 소유하는 field row 이므로 조회는 `user_group.field_group(...)` 이
내주는 하위 그룹에서 나온다. 소유자 lookup 은 그 그룹이 스스로 만들고, 도메인은 조회
네 건만 배선한다. 네 건 다 서비스 메서드 없이 `LoginSessionSearcher` ·
`LoginHistorySearcher` 스펙으로 ops 를 탄다.

스코프 조회가 `scope_search_ops` 가 아닌 이유는 그 결과가 답하는 데이터가
`EntityData` 여야 하기 때문이다. field row 는 엔티티가 아니라서 답할 id 가 없고,
`ScopedFieldsOpsResult` 가 그 자리를 맡는다.

없는 사용자로 스코프 조회를 하면 ops 가 스코프의 존재 검사를 먼저 돌므로 `UserNotFound`
가 그대로 난다.
