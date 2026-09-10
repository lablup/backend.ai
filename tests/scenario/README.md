# 시나리오 테스트

어댑터 하나를 실제 데이터베이스와 함께 돌려, 요청 하나가 무엇을 답하는지 확인한다.
규칙은 `AGENTS.md`, 배경은 `KNOWLEDGE.md`에 있다.

## 한 행이 어떻게 도는가

```python
def ungranted_user_is_refused(seed: Seeder) -> DomainScenario:
    domain = seed.creating(SeedDomain(name_hint="host"))
    stranger = seed.within(SomeoneOf(domain))
    return TypedScenario.error(
        "a-user-granted-nothing-may-not-read-a-domain",
        description="같은 도메인이 있고 사용자가 아무 권한도 받지 않았을 때, "
                    "이름으로 조회하면 권한 부족으로 거부된다",
        actor=stranger,
        given=seed.situation(),
        when=after(domain, lambda d: call(DomainAdapter.get, d.name)),
        then=NotEnoughPermission,
    )
```

1. 테스트마다 템플릿 데이터베이스를 복제한다. 템플릿에는 스키마만 있고 행은 없다.
2. 빌더가 심겠다고 한 행을 한 트랜잭션에 쓴다. 여러 행이 딛는 행은 한 번만 쓴다.
3. 행위자 명의로 어댑터 메서드를 부른다.
4. 답 또는 예외를 `then`에 맞춰 본다.

## 무엇이 어디에 있는가

| 자리 | 무엇 |
|---|---|
| `bai_scenario/manager/<컴포넌트>/` | 시나리오 표와, 어댑터를 조립하는 conftest |
| `bai_scenario/seeds/` | 행 하나를 뜻하는 seed 클래스와 `Seeder` |
| `bai_scenario/components/` | 표가 쓰는 어휘 — 시나리오 타입, 자주 쓰는 묶음 |
| `bai_scenario/runner/` | 시나리오 실행과 검사, 픽스처로 심는 자리 |
| `bai_scenario/setup/` | 공용 셋업이 무엇을 만드는지 확인하는 테스트 |
| `bai_scenario/fakes/` | 외부 서비스 대역 |
| `bai_scenario/{db,schema,config,validators,monitors}.py` | 실행 하나가 필요로 하는 것 |

패키지는 자랄 것에만 둔다. 파일 하나로 끝나는 것은 위 모듈들처럼 평평하게 둔다.

## 돌리는 법

```bash
pants test tests/scenario::
```

## 레포트

실행 결과에서 각 도메인이 무엇을 보장하는지 뽑는다. 릴리스 PR에 붙일 용도다.

```bash
BACKEND_SCENARIO_LOG=dist/scenarios.jsonl pants test tests/scenario::
python scripts/scenario-report.py dist/scenarios.jsonl -o dist/scenarios.md
```

`--split <디렉터리>`를 주면 컴포넌트마다 파일 하나로 나온다. 엔티티 패키지의 `KNOWLEDGE.md`에
되붙일 때 쓴다.

```bash
python scripts/scenario-report.py dist/scenarios.jsonl --split dist/by-component
```

세 가지 형식으로 나온다.

| `--format` | 무엇 |
|---|---|
| `markdown` (기본) | 사람이 읽는 문서. 릴리스 PR에 붙인다 |
| `json` | 도구가 읽는 같은 내용 |
| `summary` | 개수만. 빌드 로그 한 줄 |

한 행이 이렇게 나온다. 사람이 쓴 것은 첫 문장뿐이고, 셋으로 나뉜 아래는 실행에서 뽑은 것이다.
묶음으로 심은 행은 그 묶음 아래로 들여쓰인다.

```markdown
#### a-user-granted-folder-create-makes-one-of-their-own — pass

자기 스코프에서 폴더 생성 권한을 받은 사용자가 폴더를 만들면, 그 폴더의 소유는 그 사용자에게 있다

Given

- 도메인 home-1, 이 도메인의 폴더는 local:volume1에 놓을 수 있다
- 폴더를 만들 수 있는 사용자 준비
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default, 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1, 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1, 동시 세션 5개까지, 폴더는 local:volume1에 놓을 수 있다
    - 일반 사용자 user-1, 도메인 home-1 소속, 자기 키와 개인 프로젝트를 갖는다  ← 행위자
  - 역할 folder-owner-1, 일반 사용자 user-1 범위 안에서만 통한다
  - 역할 folder-owner-1: vfolder 전체에 CREATE 허용
  - 일반 사용자 user-1: 역할 folder-owner-1 보유

When

- 일반 사용자 user-1의 create 호출
  - CreateVFolderInput(name='mine', host='local:volume1')

Then

- vfolder.access_control.ownership_type = 'user'
```

레포트는 어댑터가 제공하는 호출 중 어느 시나리오도 부르지 않은 것도 함께 적는다.

문장은 한글 초안이다. 리뷰를 통과하면 영문으로 옮긴다.
