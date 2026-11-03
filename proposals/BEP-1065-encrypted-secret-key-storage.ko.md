# secret key 암호화 저장

## 관련 이슈

- Epic **BA-6958**, 이 BEP **BA-6959**
- 관련 **BEP-1068**(Login Session Improvements). 목적은 같고(저장된 key 의 위험을 줄인다) 방법이 다르다. 1.2 범위 밖 참고
- 후속: 승인 후 `/bep-to-issues` 로 BA-6958 아래 구현 Story 로 나눈다

## 1. 목표

### 1.1 문제

`keypairs.secret_key` 는 **평문 `String(40)`** 으로 저장된다. 모든 API 요청의 HMAC 서명 key 이고 JWT 서명 key 이므로, DB dump, backup, snapshot 이 유출되면 **모든 사용자의 자격 증명이 그대로 노출된다**. 비밀번호와 달리 서명 검증에는 원래 값이 필요하므로 hash 를 사용할 수 없고 **가역 암호화**만 선택지다.

이 BEP 는 그 값의 **저장 시 암호화**를 정한다. 위협 model 은 **DB 내용 자체의 유출**이고, DB 와 key 재료가 따로 저장된다는 가정 아래에서만 성립한다. manager process 전체가 장악된 상황은 방어하지 않는다.

### 1.2 범위 밖

| 항목 | 이유 |
|---|---|
| API 와 CLI 가 secret key 를 아예 반환하지 않게 하는 일 | 인증 알고리즘을 변경하는 일이다. **BEP-1068** 이 다룬다 |
| Valkey 로그인 세션과 webserver session store 에 남는 평문 사본 | 같은 이유로 BEP-1068 의 영역이다 |
| client 의 `~/.config` 와 `BACKEND_SECRET_KEY` 환경 변수 | 사용자 machine 이다 |
| **KMS 연동** | 후속. key 조회는 interface 뒤에 두지만 KMS 구현은 이 BEP 에 들어오지 않는다 |
| **`keypairs.ssh_private_key`** | 이 BEP 의 목적(API 자격 증명 보호)이 아니다. 같은 column type 을 나중에 재사용할 수 있다 |
| `object_storages.secret_key`, `reservoir_registries.secret_key`, container registry 비밀번호 | 같은 장치를 재사용하는 **후속 작업**. 이 BEP 는 column type 만 제공한다 |
| account_manager 컴포넌트의 별도 `keypairs` 테이블 | 별도 DB 와 컴포넌트이므로 후속 |

**BEP-1068 과의 관계**: 1068 은 인증 방식을 변경해 webserver 가 secret key 를 보유하거나 복호화하지 않아도 되게 한다(노출 경로를 줄인다). 이 BEP 는 저장되는 값 자체를 암호화한다(저장되는 것을 줄인다). 둘은 **상호 보완이고 배타적이지 않다**. 1068 이 들어오면 1.2 의 "평문 사본" row 도 함께 해소된다.

### 1.3 필수 요구 사항

**기존 key 를 사용하는 사용자는 그대로 동작해야 한다.** 이전 시점의 일괄 변환도, 강제 재로그인도, key 재발급도 없다. 따라서 저장 값은 **row 마다 자기 서술적(self-describing)** 이어야 하고, 평문 row 와 암호문 row 가 무기한 공존할 수 있어야 한다.

## 2. 영역별 현재 상태와 범위

영역마다 **✅ 이미 있는 것**과 **➕ 추가할 것**을 나눈다.

### 2.1 설정

| | 항목 |
|---|---|
| ✅ | `ManagerUnifiedConfig` 의 pydantic section 패턴(`AuthConfig` 등). 비밀번호 hash 알고리즘 설정이 선례다 |
| ✅ | 통합 설정은 컴포넌트 시작 시 읽어 들이고 runtime 에 `ManagerConfigProvider` 로 접근한다 |
| ✅ | one-shot CLI 명령을 위한 `ManagerConfigProvider` 조립 경로가 있다. CLI 도 통합 설정 전체를 읽으므로 key 주입 경로를 따로 둘 필요가 없다(3.5 key 재료의 위치) |
| ➕ | 새 section `secret-encryption`: **어느 provider type 이 사용하는지**, 그리고 provider type 별 선택 subsection |

- **별도 on/off 값이 없다.** 쓰기를 담당하는 provider type 을 지정하는 것이 암호화를 활성화하는 일이고, 다시 `plain` 을 지정하는 것이 비활성화하는 일이다. 기본값이 `plain` 이므로 opt-in 이다.
- **읽기는 저장 값이 정한다.** 값이 자기를 읽을 provider type 을 담으므로, 쓰기를 평문으로 되돌려도 이미 암호화된 row 는 읽을 수 있다.
- 없는 provider subsection 은 그 provider 를 등록하지 않은 채로 둔다. 있는 subsection 은 활성 key 를 지정하고 key 목록을 담아야 한다.

```toml
[secret-encryption]
write-provider-type = "config"        # defaults to "plain"

[secret-encryption.config-provider]
active-key-id = "v2"

[secret-encryption.config-provider.keys]
v1 = "Zn1QcOyzGX9OfSV9/XThDEPGTVFH2n0+PgZ7sDd1lDM="
v2 = "hK8vN2pQrL4xW9cE1mYbT7uZ0aJ6dF3sG5nR8iO2kP4="
```

key 는 base64 로 인코딩한 32 byte 무작위 값이고 `openssl rand -base64 32` 로 생성한다. 표준과 url-safe alphabet 을 모두 받는다. 통합 설정 loader chain 은 TOML 과 etcd 만 담으므로 **환경 변수로 key 를 전달할 수 없다.**

### 2.2 DB(저장 schema)

| | 항목 |
|---|---|
| ✅ | `keypairs.secret_key` 는 평문 `String(40)`, nullable. `secrets.token_urlsafe(30)` 이 정확히 40자리를 채운다 |
| ✅ | **`secret_key` 로 비교, filter, 정렬하는 SQL 질의가 없다.** 모든 비교는 row 를 가져온 뒤 Python 에서 한다. 비결정적 암호화의 전제 조건을 이미 충족한다 |
| ✅ | 같은 테이블의 `keypairs.ssh_private_key` 는 이미 `Text` 다 |
| ➕ | `secret_key` 를 `Text` 로 변경한다. **길이 제한 없음** |
| ➕ | **추가 metadata column 없음.** 저장 값 하나가 읽는 데 필요한 모든 것을 담는다(3.1 저장 형식) |

> 길이 제한을 두지 않는 것은 알 수 없기 때문이다. 저장 값의 크기는 key provider 가 정하는 두 값을 따른다. 값이 지정하는 key id(GCP CryptoKey 이름만 70~80자다)와 감싼 data encryption key 의 크기다. column 에 제한을 두면 provider 를 변경하는 일이 migration 이 된다. PostgreSQL 에서 `varchar(n)` 과 `text` 는 같은 방식으로 저장되고 성능도 같으므로 제한은 순수한 비용이다. config provider 기준으로 저장 값은 약 190자다.

> 기존 column 은 평문 문자열을 담으므로 `text` 가 된다.

### 2.3 암호화 계층

| | 항목 |
|---|---|
| ✅ | `models/base.py` 의 TypeDecorator 관례와 **`PasswordColumn` 선례**. raw 문자열 binding 을 거부하고 값 객체를 요구한다 |
| ✅ | 의존성(`cryptography`)은 이미 있다 |
| ❌ | **가역 저장 시 암호화의 선례가 없다.** |
| ➕ | `SecretColumn`: 저장 문자열과 파싱한 형태 사이를 변환하고 암호화는 하지 않는다(3.3 column type) |
| ➕ | 저장 형태를 표현하는 값 type(3.1 저장 형식) |
| ➕ | `KeyProvider`: 값 하나를 암호화하고 복호화한다(3.2 key provider 와 pool) |
| ➕ | `KeyProviderPool`: 읽기는 값이 지정한 provider 로 보내고 쓰기는 쓰기 담당 provider 로 보낸다 |
| ➕ | `populate_fixture` 의 새 column type 분기(fixture 는 평문을 담으므로 key 가 필요 없다) |

### 2.4 생성과 읽기 경로

| | 항목 |
|---|---|
| ✅ | 생성: 사용자 생성의 `generate_keypair()`, `issue_my_keypair`, 관리자 생성, signup, OpenID plugin, legacy GQL mutation |
| ✅ | 읽기(빠른 경로): REST 인증 middleware 가 access key 로 keypair row 를 core select 하고 HMAC 서명을 다시 계산하며 JWT 를 검증한다 |
| ✅ | 읽기(나머지): keypair plugin 의 `/login` 평문 `compare_digest`, plugin hook 의 token 서명, legacy GQL `KeyPair.secret_key`, `/auth/authorize` 와 `/auth/signup` 응답 |
| ➕ | 쓰기 경로가 provider 를 통해 암호화하고 결과를 bind 한다. **암호화는 비동기이므로 bind 전에 끝난다** |
| ➕ | 읽기 경로가 `str` 대신 파싱한 값을 받고, 평문이 필요한 곳마다 pool 을 통해 명시적으로 복호화한다 |
| ➕ | **REST API, GQL, admin CLI 세 곳 모두**에 일괄 재암호화를 노출한다(3.4 key 교체와 재암호화) |

> **모든 읽기 경로를 변경해야 한다.** 대신 column 의 정적 type 이 더 이상 `str` 이 아니므로 변경하지 않은 곳은 type 검사에서 실패한다. 암호문 문자열이 평문으로 위장해 하위로 흐르는 것을 구조적으로 불가능하게 만드는 것이 이 접근의 핵심 이점이다.

### 2.5 migration 과 운영

| | 항목 |
|---|---|
| ✅ | alembic 관례. backport 의 idempotency 요구를 포함한다 |
| ✅ | 평문 fixture(`example-keypairs.json`)와 alembic migration 안의 keypair 생성 |
| ➕ | column type migration 하나. **데이터 변환 없음**(기존 row 는 표식이 없으므로 평문으로 읽힌다) |
| ➕ | 배포와 rollback 절차, 경고 포함(3.6 migration 과 배포) |
| ➕ | key id 별로 남은 row 수를 세는 방법 |

## 3. 구현 설계

**핵심 흐름:** 쓰기에서 값마다 새 data encryption key 를 뽑아 값을 그것으로 암호화하고, 그 key 를 provider 의 활성 key 로 감싼 뒤 자기 서술적 문자열을 저장한다. 읽기에서 column 은 **파싱만** 하고, 값은 자기가 지정한 provider 를 통해 복호화한다. key 를 교체한 뒤에는 저장 값을 다시 암호화하는 일괄 pass 가 따르고, row 마다 새 data encryption key 를 뽑는다.

### 3.1 저장 형식(자기 서술적)

```
bai-enc:1:<provider type>:<key id>:<wrapped data key>:<nonce>:<ciphertext>
```

| field | 뜻 |
|---|---|
| `bai-enc` | 표식. 없으면 legacy 평문이다 |
| `1` | 형식 version |
| provider type | 이 값을 읽는 provider. 평문은 표식 없이 저장되므로 `plain` 은 올 수 없다 |
| key id | 그 provider 안의 어느 key 인지. **provider 가 정한다** |
| wrapped data key | 이 값 자신의 data encryption key 를 provider 의 key 로 감싼 것 |
| nonce | 암호화마다 새로 뽑는다 |
| ciphertext | 암호문과 인증 tag |

- **legacy 판별**: 기존 secret key 는 `token_urlsafe` 출력이라 `:` 를 포함할 수 없으므로 표식과 충돌하지 않는다.
- **AAD**: column 이름이 associated data 이고, 다른 column 의 값을 옮겨 붙이는 것을 차단한다.
- **무결성**: 별도 평문 hash 를 두지 않는다. AEAD 인증 tag 가 잘못된 key 와 변조를 모두 잡는다.
- **알고리즘 field 가 없다.** 형식 version 이 알고리즘을 함의하고, 알고리즘을 변경하면 version 을 올린다.
- **길이 prefix 가 없다.** 뒤의 세 field 는 base64url 이고 구분자를 담지 않으므로 오른쪽부터 나누면 모호하지 않다. provider 가 정한 key id 가 구분자를 담을 수 있는 이유다.
- **data encryption key 는 row 하나에 속한다.** 두 사용자의 값을 같은 key 로 암호화하지 않는다.
- 형식 version 은 읽기에서 분기다. 새 version 은 기존 분기를 교체하지 않고 **추가**하므로 이전 build 가 쓴 값도 계속 파싱된다.

### 3.2 key provider 와 pool

`KeyProvider` 는 **값 하나를** 다룬다. 어느 key id 로 쓰고 data encryption key 를 감싸는 방법은 각자의 일이며, 저장 값은 되돌려 줄 provider 만 지정한다.

| method | 계약 |
|---|---|
| `provider_type()` | 저장 값에 기록되는 type |
| `encrypt(plaintext, context)` | 이 provider 의 현재 key 로 새 값을 암호화한다 |
| `decrypt(value, context)` | 이 provider 가 쓴 값의 평문을 복원한다 |

지금 구현은 config 기반 하나뿐이다. 값마다 data encryption key 를 뽑아 값을 암호화하고, 그 key 를 활성 key 로 감싼다. KMS 는 나중에 같은 interface 에 붙는다.

`KeyProviderPool` 은 등록된 provider 와 쓰기 담당 하나를 보유한다.

- 읽기는 값이 지정한 provider 로 간다. 표식이 없으면 평문이므로 그대로 반환한다.
- 쓰기는 쓰기 담당 provider 로 간다. 그것이 `plain` 이면 값은 암호화하지 않고 저장된다.
- 알 수 없는 provider type 이거나 설정되지 않은 provider 면 예외를 낸다.

**주입 지점**: 복호화가 필요한 곳은 인증 middleware, keypair plugin(로그인 비교와 token 서명), 인증 service, legacy GQL resolver 다. 원칙은 **repository 경계에서 복호화하고 data 객체를 위로 전달하는 것**이다. 인증 middleware 처럼 core select 를 직접 사용하는 곳은 거기에 pool 을 주입한다.

복호화는 메모리 안 key 를 대상으로 하는 순수 CPU 작업이고 원격 I/O 가 없으므로 인증 빠른 경로에서 안전하다.

### 3.3 column type

`SecretColumn` 은 저장 문자열과 파싱한 형태 사이를 변환하고 **암호화는 하지 않는다**. 암호화에는 key provider 가 필요하고 비동기라서 SQLAlchemy 의 동기 bind hook 이 할 수 없다. 따라서 값은 암호화를 마친 상태로 column 에 도달한다.

| 방향 | 입출력 | column 이 하는 일 |
|---|---|---|
| 쓰기 | 파싱한 값을 bind | 저장 문자열로 직렬화한다. **파싱한 값이 아니면 거부한다** |
| 읽기 | 파싱한 값 반환 | 저장 문자열을 파싱하고, 표식이 없는 값을 평문으로 표시한다 |

- raw `str` 을 거부하는 것이 평문 문자열이 실수로 저장되는 것을 차단한다.
- column 의 `context` 인자는 자기 이름이고, 호출자가 provider 에 associated data 로 전달하는 값이다. **private 이 아니라 plain attribute 여야 한다.** SQLAlchemy 는 plain attribute 로 찾은 `__init__` 인자로 type 의 statement cache key 를 생성하므로, 숨기면 두 column 이 cache key 를 공유해 컴파일된 statement 가 다른 column 의 associated data 로 값을 bind 할 수 있다.
- 평문 row 와 암호화 row 는 **하나의 type 으로 표현**되므로 소비자가 분기하지 않는다.
- 값 type 은 frozen dataclass 이고, 평문도 key 재료도 `repr` 에 나오지 않는다.

### 3.4 key 교체와 재암호화

key 교체는 **설정에 새 key 를 추가하고 활성 key id 를 변경하는 것**이다. 옛 key 는 복호화용으로만 남는다.

**재암호화의 정의**: 값을 복호화한 뒤 쓰기 provider 를 통해 다시 암호화한다. row 마다 새 data encryption key 를 뽑으므로 wrapped key, nonce, ciphertext 가 모두 변경된다.

**어떤 row 도 다르게 취급하지 않는다.** 이미 활성 key 에 있는 값을 건너뛰는 경로도, data encryption key 만 다시 감싸는 경로도 없다. 값이 어느 key 에 있었든 같은 작업을 한다.

**pass 는 호출자가 지정한 하나가 아니라 암호화 column 전체를 한 번에 다룬다.** column 은 pass 가 읽는 catalog 이므로, column 은 자기 동작을 얻어서가 아니라 거기 등재되어 catalog 에 들어온다. 각 column 은 자기 column type 이 가진 associated data 로 읽히고, 그래서 secret 을 담지 않는 column 은 catalog 에 들지 않는다.

설정에 남긴 옛 key 는 그 값을 계속 읽을 수 있게 한다. 그 key 를 제거하려면 수렴이 필요하고, 일괄 pass 가 그것을 한다.

일괄 pass 는 방향 flag 를 받지 않는다.

| 쓰기 대상 | 일괄 pass 가 하는 일 |
|---|---|
| provider | 모든 값을 그 provider 의 활성 key 로 다시 암호화한다 |
| `plain` | 모든 값을 평문으로 되돌린다 |

암호문을 다시 평문으로 만드는 것은 별도 기능이 아니라 설정의 결과다.

재암호화에는 따라야 할 제약이 하나 있다.

| 제약 | 이유 |
|---|---|
| **조건부 UPDATE**: 방금 읽은 정확한 문자열일 때만 UPDATE 한다 | **읽기와 쓰기 사이에 keypair 가 재발급되면 낡은 값이 새 값을 대체해 버린다.** 조건이 그것을 차단한다. 여러 manager 가 한 row 에 경합하면 하나가 성공하고 나머지는 무해한 no-op 이다 |

- 전체 쓰기량은 **row 당 쓰기 하나**이고 keypair 수에 비례하는 일회성 부하이다.
- pass 가 값을 복호화하므로 **평문을 다룰 권한이 필요하다**.
- 실패해도 저장 값은 그대로 유효하고 다음 실행이 다시 처리한다.

**일괄 pass 는 세 곳 모두에 제공한다.**

| 표면 | 용도 |
|---|---|
| REST API(admin) | 자동화와 운영 도구에서 호출한다 |
| GQL mutation(admin) | 관리 console 연동 |
| `mgr` admin CLI | migration 작업을 위해 server 밖에서 직접 실행한다 |

공통 요구 사항: 암호화 column 전체를 **chunk 단위로** 정리하고, column 과 key id 별 count 를 보고하며, 저장 상태를 조회할 수 있게 한다. chunk 크기는 구현이 정하고 호출자가 전달하지 않는다. 중단된 pass 는 다시 실행해 이어 간다.

### 3.5 key 재료의 위치

**통합 설정의 새 section 만으로 충분하다.** 별도 경로가 필요 없다.

| process | key 필요 | 근거 |
|---|---|---|
| manager server | 예 | `ManagerConfigProvider` 로 통합 설정에 접근한다 |
| `mgr` CLI(일괄 재암호화) | 예 | one-shot CLI 명령용 `ManagerConfigProvider` 조립 경로가 이미 있다 |
| alembic | **아니오** | column type 변경뿐이고 데이터 변환이 없다 |
| fixture 적재 | **아니오** | 평문으로 기록하고 나중에 일괄 pass 가 옮긴다 |

읽기가 파싱만 하므로 bootstrap 단계(alembic, fixture)는 key 에 전혀 의존하지 않는다.

key 를 파일 대신 etcd 에 두는 데는 code 변경이 없다. etcd 는 이미 통합 설정 loader chain 에 있고, 변경 시 통합 설정 전체를 다시 검증하는 watcher 가 이미 실행된다. etcd 는 PostgreSQL 과 별도 저장소이므로 "DB 만 유출된다"는 위협 model 은 그대로 성립한다.

### 3.6 migration 과 배포

migration 은 데이터 변환이 없는 **column type 변경 하나**이고 backport 를 위해 idempotent 하게 작성한다. `varchar(40)` 에서 `text` 로는 binary coercible 이라 table rewrite 가 없고, 이 column 에는 index 가 없다.

배포 순서:

1. code 를 배포한다(column type 적용, 쓰기는 아직 `plain`). 저장 동작은 변하지 않는다.
2. key 를 설정한 뒤 쓰기 provider type 을 지정한다. 새 keypair 가 암호화되어 저장된다.
3. 필요하면 일괄 pass 로 기존 row 를 옮긴다.

**rollback 경고**: 1단계로 되돌리는 것은 안전하다(모든 row 가 평문이다). 그러나 **2단계 이후에 이전 build 로 되돌리면 암호문을 평문으로 오인해 인증이 깨진다.** 되돌리려면 쓰기 대상을 `plain` 으로 되돌리고 일괄 변환을 먼저 끝내야 한다. release note 에 밝힌다.

**성능**: 복호화는 메모리 안 key 를 대상으로 하는 microsecond 단위 작업이라 인증 빠른 경로에 유의미한 영향을 주지 않는다. 값 하나를 읽으면 data encryption key 를 푸는 AES 연산과 값 복호화, 두 번의 AES 연산을 한다.

## 결정 요약

| 결정 | 내용 |
|---|---|
| 활성화와 비활성화 | 별도 값이 없다. **쓰기 provider type 지정**이 활성화이고 `plain` 지정이 비활성화다. 기본값은 `plain` |
| 읽기 | **저장 값이 정한다.** 값이 자기를 읽을 provider 를 지정하므로 읽기는 쓰기 설정과 무관하다 |
| 저장 형식 | 단일 column 자기 서술적 `bai-enc:<format version>:<provider type>:<key id>:<wrapped data key>:<nonce>:<ciphertext>`. 표식이 없으면 legacy 평문 |
| 알고리즘 field | 없음. 형식 version 이 함의한다 |
| 길이 prefix | 없음. 뒤의 세 field 가 base64url 이라 오른쪽부터 나누면 모호하지 않다 |
| 추가 metadata column | 없음 |
| data encryption key 범위 | **row 하나.** 두 사용자의 값을 같은 key 로 암호화하지 않는다 |
| column type | 저장 문자열과 파싱한 형태 사이만 변환한다. **암호화는 하지 않는다.** 암호화는 비동기이고 bind 전에 끝난다. raw 문자열은 거부한다 |
| 복호화 지점 | 평문이 필요한 곳에서 pool 을 통해 명시적으로 호출한다. 모든 읽기 경로를 변경하고, 빠뜨린 곳은 type 검사에서 실패한다 |
| 알고리즘 | AEAD(AES-256-GCM). 별도 평문 hash 가 없다. column 이름을 associated data 로 bind 한다 |
| key 관리 | provider 마다 key 를 id 로 보유하고 활성 id 를 지정한다. 값이 지정한 id 로 복호화하고 새 값은 활성 id 로 감싼다 |
| key provider 추상화 | `KeyProvider` 가 값 하나를 암호화하고 복호화한다. config 기반 구현 하나가 있고 KMS 는 나중에 같은 interface 에 붙는다 |
| key 교체 | 설정에 key 를 추가하고 활성 id 를 변경하는 것이 전부다. **일괄 pass 가 모든 값을 새 data encryption key 로 다시 암호화한다** |
| 즉시 수렴 | 하지 않는다. 설정에 남은 옛 key 가 값을 계속 읽을 수 있게 하고, 그 key 를 제거할 때 일괄 pass 로 수렴한다 |
| 재암호화 제약 | **조건부 UPDATE**(재발급 경합을 차단한다) |
| 일괄 범위 | **암호화 column 전체를 한 번에**, 호출자가 아니라 catalog 가 지정한다. column 은 자기 동작을 얻어서가 아니라 등재되어 참여한다 |
| 일괄 표면 | **REST admin API, GQL mutation, `mgr` admin CLI 세 곳 모두.** chunk 단위이고 column 과 key id 별 count 를 보고한다 |
| 일괄 방향 | 방향 flag 가 없다. **현재 쓰기 대상이 정한 대로 정규화**하므로 `plain` 이면 평문 변환이 된다 |
| column type 변경 | `String(40)` 에서 `Text`, **길이 제한 없음**. 저장 크기는 provider 구현을 따르므로 제한을 알 수 없다. `varchar` 에서 `text` 는 table rewrite 가 필요 없다 |
| 하위 호환 | 평문과 암호화 row 가 무기한 공존한다. 일괄 변환, 강제 재로그인, key 재발급이 없다 |
| key 재료 위치 | **새 통합 설정 section 만으로 충분하다.** CLI 가 같은 조립 경로로 읽고, alembic 과 fixture 는 key 가 필요 없으며 etcd 는 code 변경 없이 동작한다 |
| 첫 대상 | 단일 column `keypairs.secret_key` |
| 범위 밖 | KMS, `ssh_private_key`, 노출 경로 축소(BEP-1068), Valkey 와 webserver 사본, 다른 테이블과 컴포넌트의 secret column |

## 열린 질문

- **옛 key 은퇴 자동화 수준.** 남은 count 가 0인지 운영자가 판단하는 방식과 일괄 pass 가 "은퇴 가능" 신호를 내는 방식.
- **다른 secret column 으로의 확장 시점.** object storage, reservoir registry, container registry 를 후속 Story 로 두는 방식과 같은 Epic 안에서 계속하는 방식.

## 참고

- **BEP-1068** Login Session Improvements. 상호 보완이며 인증 알고리즘 변경으로 노출 경로를 줄인다
- 선례: `PasswordColumn`(단방향 hash column type). 값 객체 binding 과 fixture 분기의 구조적 template
- 형식 선례: Google Tink keyset 의 key id 기반 교체
