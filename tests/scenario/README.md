# 시나리오 테스트

어댑터 하나를 실제 데이터베이스와 함께 돌려, 요청 하나가 무엇을 답하는지 확인한다.
규칙은 `AGENTS.md`, 배경은 `KNOWLEDGE.md`에 있다.

## 한 행이 어떻게 도는가

```python
def ungranted_user_is_refused(seed: Seeder) -> DomainScenario:
    domain = seed.creating(seed_domain(name_hint="host"))
    stranger = seed_someone_of(seed, domain)
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
| `bai_scenario/seeds/` | 행을 만드는 write spec factory와 `Seeder` |
| `bai_scenario/components/` | 표가 쓰는 어휘 — 시나리오 타입, 자주 쓰는 조합 |
| `bai_scenario/runner/` | 시나리오 실행과 검사 |
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
python scripts/scenario-report.py dist/scenarios.jsonl > dist/scenarios.md
```

한 행이 이렇게 나온다. 첫 문장만 사람이 쓴 것이고 나머지는 실행에서 뽑은 것이다.

```markdown
#### a-user-granted-folder-create-makes-one-of-their-own — pass

자기 스코프에서 폴더 생성 권한을 받은 사용자가 폴더를 만들면, 그 폴더의 소유는 그 사용자에게 있다

1. a domain home-1
2. a project policy default-1
3. a user policy user-policy-1
4. a keypair policy keypair-policy-1
5. a user user-1
6. a role folder-owner-1
7. CREATE on vfolder on a role folder-owner-1
8. a user user-1 holds a role folder-owner-1
9. calls create
10. answers
```

레포트는 어댑터가 제공하는 호출 중 어느 시나리오도 부르지 않은 것도 함께 적는다.
