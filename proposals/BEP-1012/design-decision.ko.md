# BEP-1012 RBAC 설계 결정

이 문서는 BEP-1012 RBAC 기능 명세를 개발하며 내린 주요 설계 결정을 기록한다.

## 결정: 권한 부여 연산을 역할 할당 엔티티로 대체

### 배경

첫 설계 단계에서 RBAC 시스템은 다른 사용자에게 권한을 위임하는 특수한 "권한 부여" 연산을 두었다. 이 권한 부여 연산(grant:create, grant:read, grant:update, grant:soft-delete, grant:hard-delete, grant:assign)을 사용자가 자원을 공유하고 권한을 위임할 수 있게 하려고 제안했다.

### 첫 설계 (권한 부여 연산)

**개념**: 권한 위임을 가능하게 하는 특수 연산

**구조**:
- 권한 부여 연산을 특수 권한 타입으로 정의한다
- `grant:create`: 다른 사용자에게 create 권한을 부여한다
- `grant:read`: 다른 사용자에게 read 권한을 부여한다
- `grant:update`: 다른 사용자에게 update 권한을 부여한다
- `grant:soft-delete`: 다른 사용자에게 soft-delete 권한을 부여한다
- `grant:hard-delete`: 다른 사용자에게 hard-delete 권한을 부여한다
- `grant:assign`: 다른 사용자에게 assign 권한을 부여한다(역할 엔티티용)

**예시 흐름**:
```
When User A wants to share VFolder X with User B:
→ User A has grant:read permission on VFolder X
→ User A grants read Object Permission to User B
→ User B can now read VFolder X
```

**확인한 문제**:
1. **불일치**: 권한 부여 연산은 다른 표준 연산(create, read, update, delete)과 달리 특수 목적이다
2. **복잡성**: 별도 권한 타입 시스템(grant:* 연산)이 필요하다
3. **역할 할당 충돌**: 역할과 역할 할당이 별도 엔티티인 상황에서 역할 엔티티에만 특수한 `assign` 연산을 요구하면 불일치가 생긴다
4. **업계 관행**: 주요 클라우드 provider(AWS, Azure, GCP)는 권한 부여 연산이 아니라 할당 기반 모델을 사용한다

### 설계 진화

#### 단계 1: 역할과 역할 할당 엔티티 분리

팀은 역할 할당이 역할 자체와 별도 엔티티여야 한다고 판단했다. 이는 Azure RBAC 패턴을 따른다.

**근거**:
- 역할은 권한을 정의한다(무엇을 할 수 있는지)
- 역할 할당은 사용자를 역할에 매핑한다(누가 어떤 역할을 가지는지)
- 분리는 역할을 변경하지 않고 유연하게 할당을 관리하게 한다

**이점**:
- 업계 표준(Azure, AWS IAM)을 따른다
- 역할 할당의 명확한 감사 추적
- 여러 사용자가 역할을 재사용할 수 있다
- 역할 할당 메타데이터(만료, 부여자 등)를 지원한다

#### 단계 2: 권한 부여 연산의 필요성 재검토

역할 할당이 별도 엔티티가 되면서 다음 질문이 나왔다.

**역할과 역할 할당이 권한 부여 연산을 완전히 대체할 수 있는지 검토한다**

**분석**:

전통적인 권한 부여 방식:
```
User A grants VFolder X read permission to User B:
1. User A has grant:read permission
2. System creates Object Permission for User B
```

역할 할당 방식:
```
User A grants VFolder X read permission to User B:
1. User A creates/retrieves Role with VFolder X read Object Permission
2. User A creates Role Assignment connecting User B to that Role
```

**핵심 통찰**: 역할 할당 방식은 역할 폭증을 일으키지 않는다.
- "VFolder-X-Reader" 역할 하나를 여러 역할 할당에 공유할 수 있다
- 역할 수는 적게 유지되고 역할 할당 수만 늘어난다

#### 단계 3: 비교 분석

**권한 부여 연산 방식**:

장점:
- ✅ 직관적: "grant" 가 사용자의 사고 모델과 맞는다
- ✅ 직접적: 권한 위임에 연산 하나를 사용한다
- ✅ 관리할 엔티티가 적다

단점:
- ❌ 특수 목적 연산이 일관성을 해친다
- ❌ 일반 연산과 권한 부여 연산 두 종류를 가진 복잡한 권한 모델
- ❌ 업계 표준과 맞지 않는다

**역할 할당 방식**:

장점:
- ✅ 완전히 일관된 권한 모델
- ✅ 모든 권한을 표준 CRUD(생성, 조회, 변경, 삭제) 연산으로 관리한다
- ✅ 업계 표준(Azure, AWS, GCP)을 따른다
- ✅ 더 나은 감사 추적
- ✅ 더 유연하다(할당에 메타데이터를 추가할 수 있다)

단점:
- ❌ 2단계 절차(역할을 생성하거나 조회한 뒤 할당을 생성한다)
- ❌ 관리할 엔티티가 많다
- ❌ 단순한 공유 사용 사례에는 직관적이지 않다

### 최종 결정

**편의 API 를 선택 사항으로 두고 역할 할당 방식을 채택한다**

**결정**: 모든 권한 부여 연산을 역할과 역할 할당 관리로 대체하되 하위 호환을 위해 편의 API 를 제공한다.

**구현 전략**:

#### 옵션 1: 순수 RBAC (새 통합에 권장)
```
To share VFolder X with User B:
1. Create/retrieve Role with VFolder X Object Permissions
2. Create Role Assignment: User B → Role
```

#### 옵션 3: 편의 API (하위 호환용)
```
To share VFolder X with User B:
1. Call sharing API specifying target user and permissions
2. System automatically:
   - Creates/retrieves appropriate Role
   - Creates Role Assignment
```

**근거**:
1. **일관성**: 표준 연산만 사용하는 순수 RBAC 모델
2. **업계 표준과의 일치**: Azure RBAC, AWS IAM 패턴과 맞는다
3. **유연성**: 역할 할당 엔티티가 풍부한 메타데이터를 지원한다
4. **하위 호환**: 편의 API 가 기존 작업 흐름을 유지한다
5. **점진적 이전**: 사용자가 시간이 지나며 편의 API 에서 직접 RBAC 로 전환할 수 있다

### 명세에 미친 영향

**제거**:
- 권한 부여 연산 항목(grant:create, grant:read, grant:update, grant:soft-delete, grant:hard-delete)
- `assign` 연산(역할 엔티티 전용 특수 목적)
- `grant:assign` 권한 부여 연산

**추가**:
- 별도 엔티티로서 역할 할당
- 역할과 역할 할당 방식을 설명하는 권한 위임 항목
- 편의 API 와 직접 RBAC 방식을 모두 포함하는 vfolder 공유 사용 사례
- 유연한 공유를 위한 스코프 간 object 권한

**변경**:
- 연산: 모든 엔티티에 create, read, update, soft-delete, hard-delete 로 통합
- 사용 사례: 권한 부여 연산 대신 역할 할당 생성을 사용하도록 변경
- 스코프 규칙: 계층적 권한 부여 위임 대신 스코프 로컬 관리에 집중하도록 단순화

### 다른 시스템과 비교

#### AWS IAM
- `AttachUserPolicy`, `DetachUserPolicy` 를 사용한다. 우리 역할 할당 방식과 비슷하다
- policy 연결과 policy 정의는 별도다
- ✅ 우리 설계와 맞는다

#### Azure RBAC
- 역할 할당을 일급 엔티티로 다룬다
- 역할 할당 관리를 위한 별도 권한: `Microsoft.Authorization/roleAssignments/write`
- ✅ 우리 설계와 정확히 맞는다

#### Google Cloud IAM
- "Policy Bindings" 로 사용자에게 역할을 부여한다
- 바인딩은 역할 정의와 별도로 관리한다
- ✅ 개념적으로 우리 역할 할당과 비슷하다

### 얻은 이점

1. **통합 권한 모델**: 모든 권한을 표준 CRUD 연산으로 관리한다
2. **단순해진 사고 모델**: 역할은 권한을 정의하고 할당은 사용자에게 권한을 부여한다
3. **나은 확장성**: 역할 재사용으로 사용자별 권한 부여 레코드보다 엔티티 수가 적다
4. **강화된 감사**: 역할 할당 엔티티가 누가, 언제, 만료를 기록한다
5. **업계 표준**: 주요 클라우드 provider 의 패턴과 맞는다
6. **유연한 진화**: 할당 승인 흐름, 임시 접근 같은 기능을 쉽게 추가할 수 있다

### 참고

- [BEP-1012: Backend.AI 역할 기반 접근 제어(RBAC) 기능 명세](./BEP-1012-main.md)
- [BEP-1008: Backend.AI 역할 기반 접근 제어(RBAC) 기술 구현](./BEP-1008-RBAC.md)
- [Azure RBAC: Role Assignments](https://learn.microsoft.com/en-us/azure/role-based-access-control/role-assignments)
- [AWS IAM: Policies and Permissions](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html)
