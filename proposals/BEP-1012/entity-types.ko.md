# BEP-1012 RBAC 엔티티와 field 타입

이 문서는 Backend.AI RBAC 시스템이 관리하는 엔티티 타입과 field 타입을 정의한다.

## 엔티티 타입

엔티티 타입은 RBAC 시스템에서 권한 검사의 주요 대상이다. 각 엔티티 타입은 표준 연산(create, read, update, soft-delete, hard-delete)을 지원한다.

### 분류

| 분류 | 예 | 설명 |
|----------|----------|-------------|
| 자원 | vfolder, 세션, 이미지 등 | RBAC 가 보호하는 실제 업무 객체 |
| 스코프 | 도메인, 프로젝트, 사용자 | 권한 경계를 정의하는 조직 구조 |
| 메타 엔티티 | 역할, {Entity}:assignment | RBAC 시스템 자체를 이루는 엔티티 |

> **참고**: 구현이 끝나면 확인 목록을 갱신한다.

| 엔티티 타입 | 설명 | 이중 역할 | 비고 | 마이그레이션 | validator | repository 패턴 |
|-------------|-------------|-----------|-------|:---------:|:---------:|:------------:|
| 세션 | 연산 작업과 컨테이너 | 엔티티만 | | [ ] | [ ] | [ ] |
| 세션 템플릿 | 미리 정의된 세션 설정 | 엔티티만 | | [ ] | [ ] | [ ] |
| vfolder | 데이터를 저장하는 vfolder | 엔티티만 | | [ ] | [ ] | [ ] |
| 이미지 | 세션용 container image | 엔티티만 | | [ ] | [ ] | [ ] |
| 배포 | 모델 서빙 배포 | 엔티티만 | | [ ] | [ ] | [ ] |
| 아티팩트 | 아티팩트 레지스트리에 있는 모델, 패키지, 이미지 | 엔티티만 | | [ ] | [ ] | [ ] |
| 아티팩트 레지스트리 | 아티팩트를 저장하고 관리하는 레지스트리 | 엔티티만 | | [ ] | [ ] | [ ] |
| 에이전트 | 컴퓨팅 자원을 제공하는 에이전트 노드 | 엔티티만 | | [ ] | [ ] | [ ] |
| 자원 그룹 | 에이전트의 논리 그룹 | 엔티티만 | | [ ] | [ ] | [ ] |
| 스토리지 호스트 | 스토리지 backend host | 엔티티만 | | [ ] | [ ] | [ ] |
| 앱 설정 | 애플리케이션 설정 항목 | 엔티티만 | | [ ] | [ ] | [ ] |
| 알림 채널 | 알림을 전달하는 채널 | 엔티티만 | | [ ] | [ ] | [ ] |
| 알림 규칙 | 알림을 발생시키는 규칙 | 엔티티만 | | [ ] | [ ] | [ ] |
| 도메인 | 관리 도메인 묶음 | 엔티티와 스코프 | | [ ] | [ ] | [ ] |
| 프로젝트 | 도메인 안의 프로젝트 묶음 | 엔티티와 스코프 | | [ ] | [ ] | [ ] |
| 사용자 | 사용자 계정 | 엔티티와 스코프 | | [ ] | [ ] | [ ] |
| 역할 | 권한 묶음 정의 | 엔티티만 | | [ ] | [ ] | [ ] |
| {Entity}:assignment | 특정 엔티티를 다른 사용자와 공유하는 매핑 | 엔티티만 | 예: vfolder:assignment, compute_session:assignment | [ ] | [ ] | [ ] |

**참고**:
- **이중 역할**: 도메인, 프로젝트, 사용자는 관리 가능한 엔티티이면서 권한 스코프로도 동작한다.
- **{Entity}:assignment**: 사용자와 특정 엔티티 인스턴스의 공유 관계를 나타내는 메타 엔티티다.
- **마이그레이션**: 이 엔티티 타입의 RBAC 마이그레이션이 끝났는지 나타낸다.
- **validator**: 이 엔티티 타입의 RBAC 권한 validator 를 구현했는지 나타낸다.
- **repository 패턴**: RBAC repository 패턴(Creator/Granter/Purger)을 구현했는지 나타낸다.

## field 타입

field 타입은 자체 권한 검사가 없는 객체다. field 에 대한 권한 검사는 그 field 가 속한 엔티티에 위임한다. 이 설계는 결합이 강한 객체의 권한 관리를 단순화한다.

### 개념

field 객체의 권한을 검사할 때의 절차는 다음과 같다.
1. 시스템이 `entity_fields` 테이블로 연결된 엔티티를 조회한다
2. 대신 그 엔티티에 대해 권한 검사를 실행한다
3. 연산 타입은 그대로 유지한다(예: `kernel:read` → `session:read`)

### field 타입 표

> **참고**: 구현이 끝나면 확인 목록을 갱신한다.

| field 타입 | 엔티티 타입 | 설명 | 마이그레이션 | validator | repository 패턴 |
|------------|-------------|-------------|:---------:|:---------:|:-------------:|
| 커널 | 세션 | 세션 안의 개별 container 인스턴스 | [ ] | [ ] | [ ] |
| 세션 이력 | 세션 | 세션 실행의 과거 기록 | [ ] | [ ] | [ ] |
| 모델 리비전 | 배포 | 배포의 버전 스냅샷 | [ ] | [ ] | [ ] |
| 배포 이력 | 배포 | 배포 변경의 과거 기록 | [ ] | [ ] | [ ] |
| 라우트 | 배포 | 모델 엔드포인트의 트래픽 라우팅 설정 | [ ] | [ ] | [ ] |
| 라우트 이력 | 배포 | 라우팅 변경의 과거 기록 | [ ] | [ ] | [ ] |
| 엔드포인트 토큰 | 배포 | 모델 엔드포인트의 인증 token | [ ] | [ ] | [ ] |
| 아티팩트 리비전 | 아티팩트 | 아티팩트의 버전 스냅샷 | [ ] | [ ] | [ ] |
| object 권한 | 역할 | object 수준 권한 할당 | [ ] | [ ] | [ ] |
| 권한 | 역할 | 타입 수준 권한 정의 | [ ] | [ ] | [ ] |
| 권한 그룹 | 역할 | 스코프별로 묶은 권한 | [ ] | [ ] | [ ] |

**참고**:
- **마이그레이션**: 이 field 타입의 RBAC 마이그레이션이 끝났는지 나타낸다.
- **validator**: 이 field 타입의 RBAC 권한 validator 를 구현했는지 나타낸다.
- **repository 패턴**: RBAC repository 패턴(Creator/Granter/Purger)을 구현했는지 나타낸다.

### 예: 커널 권한 검사

```
Permission check: "Does User A have read permission on Kernel X?"

1. Look up entity_fields table:
   - field_type: "kernel"
   - field_id: "X"
   → Returns: entity_type: "compute_session", entity_id: "session-123"

2. Perform permission check on the associated entity:
   - "Does User A have read permission on Compute Session session-123?"

3. Return the result of the entity's permission check
```

### 데이터베이스 스키마

`entity_fields` 테이블은 field 객체를 연결된 엔티티에 매핑한다.

```sql
CREATE TABLE entity_fields (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(64) NOT NULL,  -- Entity type
    entity_id VARCHAR(64) NOT NULL,    -- Entity ID
    field_type VARCHAR(64) NOT NULL,   -- Field type
    field_id VARCHAR(64) NOT NULL,     -- Field ID
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    UNIQUE (entity_type, entity_id, field_type, field_id)
);

-- Indexes for efficient lookups
CREATE INDEX ix_entity_fields_entity_lookup ON entity_fields (entity_type, entity_id);
CREATE INDEX ix_entity_fields_field_lookup ON entity_fields (field_type, field_id);
```

## Related documents

- [BEP-1012: RBAC 기능 명세](./BEP-1012-main.md) - 주요 기능 명세
- [BEP-1008: RBAC 기술 구현](./BEP-1008-RBAC.md) - 기술 구현 세부 사항
