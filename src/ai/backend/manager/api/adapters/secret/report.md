## secret

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/secret/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/secret/adapter.py)

Not exercised by any scenario: batch_load_fields.

### reencrypting

#### [a-user-who-is-not-the-superadmin-may-not-reencrypt-secrets](/tests/scenario/bai_scenario/manager/secret/test_reencrypting.py) — pass

슈퍼관리자가 아닌 사용자가 재암호화를 실행하면 역할 부족으로 거부된다

Given

- 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- SecretAdapter.admin_reencrypt_secrets — user-1이 비밀 키 전부를 재암호화

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [reencrypting-moves-plaintext-secrets-onto-the-config-key](/tests/scenario/bai_scenario/manager/secret/test_reencrypting.py) — pass

설정 키가 쓰기 제공자일 때 평문 비밀 키 둘을 재암호화하면, 둘을 스캔해 둘을 다시 썼다는 응답과 함께 둘 다 그 키로 암호화되고 평문은 없는 상태가 반환된다

Given

- 슈퍼관리자 한 명, 평문 비밀 키를 가진 사용자 1명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다

When

- SecretAdapter.admin_reencrypt_secrets — user-1이 비밀 키 전부를 재암호화

Then

- 모두 스캔해 모두 다시 쓰고, 전부 쓰기 제공자로 옮겨진 상태가 반환된다
  - scanned = 2
  - reencrypted = 2
  - status.write_provider_type = 'config'
  - status.counts = [('keypairs.secret_key', 'config', 'k1', 2)]

#### [reencrypting-rewrites-secrets-already-on-the-config-key](/tests/scenario/bai_scenario/manager/secret/test_reencrypting.py) — pass

설정 키가 쓰기 제공자이고 비밀 키 둘이 이미 그 키로 암호화돼 있을 때 재암호화하면, 둘을 스캔해 둘을 다시 썼다는 응답이 반환되고 상태는 그대로 그 키로 암호화된 것 둘이다

Given

- 슈퍼관리자 한 명, 설정 키로 암호화된 비밀 키를 가진 사용자 1명
  - 도메인 home-1
  - 암호화된 비밀 키를 가진 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다, 비밀 키는 암호화돼 있다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다, 비밀 키는 암호화돼 있다

When

- SecretAdapter.admin_reencrypt_secrets — user-1이 비밀 키 전부를 재암호화

Then

- 모두 스캔해 모두 다시 쓰고, 전부 쓰기 제공자로 옮겨진 상태가 반환된다
  - scanned = 2
  - reencrypted = 2
  - status.write_provider_type = 'config'
  - status.counts = [('keypairs.secret_key', 'config', 'k1', 2)]

#### [reencrypting-with-a-plain-writer-rewrites-plaintext-secrets-as-plaintext](/tests/scenario/bai_scenario/manager/secret/test_reencrypting.py) — pass

쓰기 제공자가 평문일 때 평문 비밀 키 둘을 재암호화하면, 둘을 스캔해 둘을 다시 썼다는 응답이 반환되고 상태는 그대로 평문 둘이다. 다시 쓴 수는 값이 바뀌었는지가 아니라 행을 다시 썼는지를 센다

Given

- 슈퍼관리자 한 명, 평문 비밀 키를 가진 사용자 1명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다

When

- SecretAdapter.admin_reencrypt_secrets — user-1이 비밀 키 전부를 재암호화

Then

- 모두 스캔해 모두 다시 쓰고, 전부 쓰기 제공자로 옮겨진 상태가 반환된다
  - scanned = 2
  - reencrypted = 2
  - status.write_provider_type = 'plain'
  - status.counts = [('keypairs.secret_key', 'plain', None, 2)]

#### [reencrypting-with-a-plain-writer-turns-an-encrypted-secret-back-to-plaintext](/tests/scenario/bai_scenario/manager/secret/test_reencrypting.py) — pass

쓰기 제공자가 평문이고 설정 키 제공자는 읽기 전용일 때 그 키로 암호화된 비밀 키를 재암호화하면, 하나를 스캔해 하나를 다시 썼다는 응답이 반환되고 상태는 평문뿐이다

Given

- 슈퍼관리자 한 명
  - 도메인 home-1
  - 암호화된 비밀 키를 가진 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다, 비밀 키는 암호화돼 있다

When

- SecretAdapter.admin_reencrypt_secrets — user-1이 비밀 키 전부를 재암호화

Then

- 모두 스캔해 모두 다시 쓰고, 전부 쓰기 제공자로 옮겨진 상태가 반환된다
  - scanned = 1
  - reencrypted = 1
  - status.write_provider_type = 'plain'
  - status.counts = [('keypairs.secret_key', 'plain', None, 1)]

#### [the-monitor-may-not-reencrypt-secrets](/tests/scenario/bai_scenario/manager/secret/test_reencrypting.py) — pass

모니터 역할이 재암호화를 실행하면 역할 부족으로 거부된다. 상태는 조회할 수 있지만 재암호화는 쓰기 연산이라 통과하지 못한다

Given

- 모니터 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 모니터 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- SecretAdapter.admin_reencrypt_secrets — user-1이 비밀 키 전부를 재암호화

Then

- 거부된다
  - 거부: InsufficientPrivilege

### status

#### [a-user-who-is-not-the-superadmin-may-not-read-the-secret-status](/tests/scenario/bai_scenario/manager/secret/test_status.py) — pass

슈퍼관리자가 아닌 사용자가 상태를 조회하면 역할 부족으로 거부된다

Given

- 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- SecretAdapter.admin_secret_status — user-1이 비밀 상태를 조회

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [secrets-on-different-keys-are-counted-apart](/tests/scenario/bai_scenario/manager/secret/test_status.py) — pass

설정 키로 암호화된 비밀 키와 평문 비밀 키가 섞여 있을 때 상태를 조회하면, 그 키로 암호화된 수와 평문인 수가 두 항목으로 따로 반환된다

Given

- 슈퍼관리자 한 명, 설정 키로 암호화된 비밀 키를 가진 사용자 1명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 암호화된 비밀 키를 가진 사용자 한 명 준비
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다, 비밀 키는 암호화돼 있다

When

- SecretAdapter.admin_secret_status — user-1이 비밀 상태를 조회

Then

- 미리 만들어 둔 비밀 키가 암호화 키별로 집계되어 반환된다
  - write_provider_type = 'config'
  - counts = [('keypairs.secret_key', 'config', 'k1', 1), ('keypairs.secret_key', 'plain', None, 1)]

#### [the-monitor-reads-the-secret-status-like-the-superadmin](/tests/scenario/bai_scenario/manager/secret/test_status.py) — pass

모니터 역할이 상태를 조회하면 슈퍼관리자와 같은 응답이 반환된다. 전역 역할 검사는 모니터의 읽기를 허용한다

Given

- 모니터 한 명, 평문 비밀 키를 가진 사용자 1명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 모니터 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다

When

- SecretAdapter.admin_secret_status — user-1이 비밀 상태를 조회

Then

- 미리 만들어 둔 비밀 키가 암호화 키별로 집계되어 반환된다
  - write_provider_type = 'plain'
  - counts = [('keypairs.secret_key', 'plain', None, 2)]

#### [the-superadmin-reads-a-status-counting-the-plaintext-secrets](/tests/scenario/bai_scenario/manager/secret/test_status.py) — pass

쓰기 제공자가 평문일 때 슈퍼관리자가 상태를 조회하면, 쓰기 제공자는 평문이고 집계는 호출자까지 포함해 평문 비밀 키를 가진 수 한 항목이다

Given

- 슈퍼관리자 한 명, 평문 비밀 키를 가진 사용자 1명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다

When

- SecretAdapter.admin_secret_status — user-1이 비밀 상태를 조회

Then

- 미리 만들어 둔 비밀 키가 암호화 키별로 집계되어 반환된다
  - write_provider_type = 'plain'
  - counts = [('keypairs.secret_key', 'plain', None, 2)]

