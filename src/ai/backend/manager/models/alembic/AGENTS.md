# Alembic 마이그레이션 — 가드레일

> 전체 백포트 절차와 예시는 이 디렉터리의 `README.md` 참고.

## 규칙

- **백포트 = 수정만** — 기능 수준의 스키마 변경은 백포트하지 않는다.
- **멱등성** — 모든 백포트 마이그레이션(`d`, `d'` 둘 다)은 존재 검사(`IF NOT EXISTS`, `IF EXISTS`,
  `inspector`)를 써서 재적용해도 안전해야 한다.
- **릴리스 버전 주석** — 모든 마이그레이션 파일은 revision 식별자 옆에
  `# Part of: <major>.<minor>.<patch>` 주석을 둔다. 백포트: `# Part of: 26.2.1 (backport), 26.3.0 (main)`.
- **릴리스된 마이그레이션의 revision 편집 금지** — 이미 릴리스된 마이그레이션의 `revision`/`down_revision`을
  수정하지 않는다. `down_revision` 편집은 머지 전 메인 체인에 백포트를 끼워 넣을 때만 허용.

## 향후 방향 (검토 중)

- 버전 주석은 `{NEXT_RELEASE_VERSION}`를 써서 릴리스 시 자동 동결한다 — 다음 버전을 하드코딩하지 않는다
  (GQL `added_version`과 동일 메커니즘, `scripts/freeze_release_version.py`가 `src/**/*.py`를 치환).
- 백포트에는 가능하면 alembic 마이그레이션을 추가하지 않는다. 불가피하게 추가하면 백포트 브랜치의 해당
  버전을 두고, 이후 main에도 그 downgrade가 포함되도록 정리한다.

## 데이터 마이그레이션 검증

정적 분석(lint, mypy)은 데이터 마이그레이션의 SQL 수준 오류를 못 잡는다. 마이그레이션이 DDL을 넘어
값 캐스팅/변환, 백필 쿼리의 교차 테이블 조인, 조건부 백필 로직을 할 때는 커밋 전 로컬 DB에 대해
**반드시** 검증한다.

### 절차

1. 부모 revision으로 `alembic downgrade`
2. 소스 테이블에 대표 테스트 데이터 `INSERT`
3. 대상 revision으로 `alembic upgrade`
4. 대상 테이블을 `SELECT`해 변환된 값 검증
5. 테스트 데이터 정리 또는 `alembic upgrade head`로 계속

### 커버할 것

- 애플리케이션 코드가 만들 수 있는 모든 값 포맷(예: BinarySize 접미사 `"32g"`, 일반 숫자, 분수 `"0.5"`)
- 컬럼이 허용하는 null·빈 값
- 교차 테이블 참조: 마이그레이션 체인의 그 시점에 참조 테이블/컬럼이 여전히 존재하는지 확인
