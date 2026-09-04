---
name: auth-service-composition
type: decision-table
description: 인증 도메인의 액션이 왜 auth 와 user 두 그룹으로 갈리는지, 게이트 없는 네 배선이 무엇으로 호출자를 확인하는지, 로그인 세션과 SSH 키페어 조작이 왜 사용자 단위로 기록되는지
scope: src/ai/backend/manager/services/auth
keywords:
  - AuthProcessors
  - AUTH_ENTITY_TYPE
  - anonymous_global
  - PublicActionProcessor
  - RevokeLoginSessionAction
sources:
  - src/ai/backend/manager/services/auth/processors.py
  - src/ai/backend/manager/api/rest/auth/registry.py
generated:
  by: claude-code/opus-5
  at: 2026-08-23
status: draft
---

# 인증 서비스

## 그룹이 둘인 이유

`auth` 그룹은 어떤 사용자 행도 답하지 않는 상태 — 자격 증명과 로그인 세션 — 을 맡는다.
로그인·로그아웃·비밀번호 재설정은 호출자가 아직 주체를 갖지 않은 채 들어오고, 관리자가
전체 세션에 닿는 조회도 어떤 사용자를 지목하지 않는다. `user` 그룹은 한 사용자의 행,
자격 증명, 로그인 기록이 답하는 것을 맡는다.

## 게이트 없는 세 배선

`authorize`, `signup`, `update_password_no_auth` 는 `anonymous_global` 로 배선된다.
셋 다 인증 미들웨어가 없는 라우트(`api/rest/auth/registry.py`)에 걸려 있어 확인할
호출자 맥락 자체가 없다. 대신 서비스가 호출자를 직접 확인한다 — 비밀번호, 즉 행이
보관한 비밀과 대조한다. `signup` 은 대조할 행이 아직 없고, 훅 플러그인이 가입 요청을
판정한다.

`logout` 은 여기 들지 않는다. 로그아웃하는 호출자는 이미 세션을 들고 있으므로
라우트가 인증을 요구하고, 액션은 그 사용자를 지목한다. 세션 토큰은 그대로 어느 세션을
끝낼지 고르는 값으로 남는다.

## 인증만 요구하는 네 읽기

`public_get_role`, `public_resolve_access_key_scope`, `public_resolve_user_scope`,
`public_resolve_default_keypair_rate_limit` 는 호출자 맥락에서 대상이 정해진다. 호출자가
지목할 수 있는 대상이 자기 자신뿐이므로 권한 확인이 더할 것이 없고, 인증만 확인한다.
위임 대상을 지목하는 경우는 서비스가 요청자와 대상의 역할·도메인을 비교해 판정한다.
`public_resolve_default_keypair_rate_limit` 는 핸들러가 아니라 rate limit 미들웨어가
부르며, 사용자의 window가 한도 없이 열렸을 때 한 번 default 키페어의 한도를 읽는다.

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

## 액세스 키로 사용자를 찾는 lookup

`lookup_user_by_access_key` 는 액세스 키라는 외부 키를 사용자 id 로 바꾸므로 lookup 이다.
인증을 먼저 확인하고, 키가 가리킨 사용자에 대한 읽기 권한을 그 다음에 확인한다. 서비스
메서드 없이 `KeypairAccessKeyUserLookup` 스펙으로 ops 를 탄다. `services/user` 의
`lookup_keypair_owner_by_access_key` 는 같은 키에서 키페어 행의 소유자를 찾고, 이쪽은
사용자 자신을 답한다 — 쿼리는 같다.

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
