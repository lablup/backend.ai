---
Author: 설계 논의
Status: 참고 문서
Created: 2025-11-05
---

# BEP-1012 RBAC 설계 결정 사항

이 문서는 BEP-1012 RBAC 기능 명세 개발 중 내린 주요 설계 결정을 기록합니다.

## 결정: Grant Operations을 Role Assignment 엔티티로 대체

### 배경

초기 설계 단계에서 RBAC 시스템은 다른 사용자에게 권한을 위임하기 위한 특수한 "grant" operation을 포함했습니다. 이러한 grant operations(grant:create, grant:read, grant:update, grant:soft-delete, grant:hard-delete, grant:assign)는 사용자가 리소스를 공유하고 권한을 위임할 수 있도록 제안되었습니다.

### 초기 설계 (Grant Operations)

**개념**: 권한 위임을 가능하게 하는 특수 operation

**구조**:
- Grant operations를 특수 권한 타입으로 정의
- `grant:create`: 다른 사람에게 create 권한 부여
- `grant:read`: 다른 사람에게 read 권한 부여
- `grant:update`: 다른 사람에게 update 권한 부여
- `grant:soft-delete`: 다른 사람에게 soft-delete 권한 부여
- `grant:hard-delete`: 다른 사람에게 hard-delete 권한 부여
- `grant:assign`: 다른 사람에게 assign 권한 부여 (Role 엔티티용)

**예시 플로우**:
```
사용자 A가 VFolder X를 사용자 B와 공유하려는 경우:
→ 사용자 A가 VFolder X에 대한 grant:read 권한 보유
→ 사용자 A가 사용자 B에게 read Object Permission 부여
→ 사용자 B가 이제 VFolder X를 읽을 수 있음
```

**발견된 문제점**:
1. **비일관성**: Grant operations는 다른 표준 operations(create, read, update, delete)와 달리 특수 목적용
2. **복잡성**: 별도의 권한 타입 시스템(grant:* operations) 필요
3. **Role Assignment 충돌**: Role과 Role Assignment가 별도 엔티티인 상황에서, Role 엔티티만을 위한 특수 `assign` operation이 필요하여 비일관성 발생
4. **업계 관행**: 주요 클라우드 제공업체(AWS, Azure, GCP)는 grant operations가 아닌 assignment 기반 모델 사용

### 설계 진화

#### 1단계: Role과 Role Assignment 엔티티 분리

팀은 역할 할당이 역할 자체와는 별도의 엔티티여야 한다고 인식했습니다. 이는 Azure RBAC 패턴을 따릅니다:

**근거**:
- Role은 권한을 정의 (무엇을 할 수 있는지)
- Role Assignment는 사용자와 역할을 매핑 (누가 어떤 역할을 가지는지)
- 분리를 통해 역할 수정 없이 유연한 할당 관리 가능

**이점**:
- 업계 표준과 일치 (Azure, AWS IAM)
- 역할 할당에 대한 명확한 감사 추적
- 여러 사용자에게 역할 재사용 가능
- 역할 할당 메타데이터 지원 (만료, 부여자 등)

#### 2단계: Grant Operations의 필요성 재검토

Role Assignment가 별도 엔티티가 되면서 다음 질문이 제기되었습니다:

**Role과 Role Assignment가 grant operations를 완전히 대체할 수 있는가?**

**분석**:

기존 grant 방식:
```
사용자 A가 VFolder X read 권한을 사용자 B에게 부여:
1. 사용자 A가 grant:read 권한 보유
2. 시스템이 사용자 B를 위한 Object Permission 생성
```

Role Assignment 방식:
```
사용자 A가 VFolder X read 권한을 사용자 B에게 부여:
1. 사용자 A가 VFolder X read Object Permission이 있는 Role 생성/검색
2. 사용자 A가 사용자 B를 해당 Role에 연결하는 Role Assignment 생성
```

**핵심 인사이트**: Role Assignment 방식이 역할 폭발을 야기하지 않음
- 하나의 "VFolder-X-Reader" Role을 여러 Role Assignment로 공유 가능
- Role 개수는 적게 유지, Assignment 개수만 증가

#### 3단계: 비교 분석

**Grant Operations 방식**:

장점:
- ✅ 직관적: "grant"가 사용자의 멘탈 모델과 일치
- ✅ 직접적: 한 번의 operation으로 권한 위임
- ✅ 관리할 엔티티 수 적음

단점:
- ❌ 특수 목적 operations가 일관성 저해
- ❌ 두 가지 operation 타입(일반 + grant)으로 복잡한 권한 모델
- ❌ 업계 표준과 불일치

**Role Assignment 방식**:

장점:
- ✅ 완전히 일관된 권한 모델
- ✅ 모든 권한이 표준 CRUD operations로 관리
- ✅ 업계 표준과 일치 (Azure, AWS, GCP)
- ✅ 더 나은 감사 추적
- ✅ 더 유연함 (할당에 메타데이터 추가 가능)

단점:
- ❌ 2단계 프로세스 (역할 생성/검색, 그 다음 할당 생성)
- ❌ 관리할 엔티티 수 증가
- ❌ 단순 공유 use case에서 덜 직관적

### 최종 결정

**선택적 편의 API와 함께 Role Assignment 방식 채택**

**결정**: 모든 grant operations를 Role과 Role Assignment 관리로 대체하되, 하위 호환성을 위한 편의 API 제공.

**구현 전략**:

#### Option 1: 순수 RBAC (신규 통합에 권장)
```
VFolder X를 사용자 B와 공유하려면:
1. VFolder X Object Permissions가 있는 Role 생성/검색
2. Role Assignment 생성: 사용자 B → Role
```

#### Option 3: 편의 API (하위 호환성용)
```
VFolder X를 사용자 B와 공유하려면:
1. 대상 사용자와 권한을 지정하여 공유 API 호출
2. 시스템이 자동으로:
   - 적절한 Role 생성/검색
   - Role Assignment 생성
```

**근거**:
1. **일관성**: 표준 operations만 사용하는 순수 RBAC 모델
2. **업계 정렬**: Azure RBAC, AWS IAM 패턴과 일치
3. **유연성**: Role Assignment 엔티티가 풍부한 메타데이터 지원
4. **하위 호환성**: 편의 API가 기존 워크플로우 유지
5. **점진적 마이그레이션**: 사용자가 편의 API에서 직접 RBAC로 시간에 걸쳐 전환 가능

### 명세서에 미친 영향

**제거됨**:
- Grant Operations 섹션 (grant:create, grant:read, grant:update, grant:soft-delete, grant:hard-delete)
- `assign` operation (Role 엔티티 전용 특수 목적)
- `grant:assign` grant operation

**추가됨**:
- 별도 엔티티로서의 Role Assignment
- Role + Role Assignment 방식을 설명하는 Permission Delegation 섹션
- 편의 API와 직접 RBAC 방식 모두를 포함한 VFolder 공유 use case
- 유연한 공유를 위한 Cross-scope Object Permissions

**변경됨**:
- Operations: 모든 엔티티에 대해 create, read, update, soft-delete, hard-delete로 통일
- Use cases: grant operations 대신 Role Assignment 생성을 사용하도록 업데이트
- Scope 규칙: 계층적 grant 위임이 아닌 스코프 로컬 관리에 초점을 맞춰 단순화

### 다른 시스템과의 비교

#### AWS IAM
- `AttachUserPolicy`, `DetachUserPolicy` 사용 - 우리의 Role Assignment 방식과 유사
- Policy 연결이 policy 정의와 분리됨
- ✅ 우리 설계와 일치

#### Azure RBAC
- Role Assignment를 일급 엔티티로 취급
- 역할 할당 관리를 위한 별도 권한: `Microsoft.Authorization/roleAssignments/write`
- ✅ 우리 설계와 직접 일치

#### Google Cloud IAM
- 역할을 사용자에게 할당하기 위해 "Policy Bindings" 사용
- Bindings가 역할 정의와 별도로 관리됨
- ✅ 우리의 Role Assignment와 개념적으로 유사

### 실현된 이점

1. **통일된 권한 모델**: 모든 권한이 표준 CRUD operations로 관리
2. **단순화된 멘탈 모델**: Roles는 권한을 정의, Assignments는 사용자에게 부여
3. **더 나은 확장성**: Role 재사용으로 사용자별 grant 레코드 대비 엔티티 수 감소
4. **향상된 감사**: Role Assignment 엔티티가 누가, 언제, 만료 시점 추적
5. **업계 표준**: 주요 클라우드 제공업체의 패턴과 일치
6. **유연한 진화**: 할당 승인 워크플로우, 임시 접근 등의 기능 추가 용이

### 참고 자료

- [BEP-1012: Backend.AI Role-Based Access Control (RBAC) 기능 명세](../BEP-1012-RBAC-feature-spec.md)
- [BEP-1008: Backend.AI Role-Based Access Control (RBAC) 기술 구현](../BEP-1008-RBAC.md)
- [Azure RBAC: Role Assignments](https://learn.microsoft.com/en-us/azure/role-based-access-control/role-assignments)
- [AWS IAM: Policies and Permissions](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html)
