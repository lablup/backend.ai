# Fair Share Query Test Scenarios

이 문서는 Fair Share 기능의 3-tier 아키텍처(Resolver → Service → Repository)에 따라 테스트 시나리오를 정리합니다.

---

## 1. GQL Resolver Layer Tests

GQL Resolver 레이어는 API 엔드포인트로서 권한 체크, 파라미터 검증, Processor 호출을 담당합니다.

### 1.1 Admin Query Resolvers

#### 1.1.1 admin_domain_fair_share (단일 조회)

**성공 시나리오:**
- [ ] Admin 권한 체크(check_admin_only) 통과
- [ ] Processor에 올바른 GetDomainFairShareAction 파라미터 전달
- [ ] 응답이 DomainFairShareGQL 타입으로 반환됨

**실패 시나리오:**
- [ ] 비관리자 사용자 접근 시 HTTPForbidden 발생
- [ ] Service에서 DomainNotFound 발생 시 예외가 올바르게 전파됨
---

#### 1.1.2 admin_domain_fair_shares (목록 조회)

**성공 시나리오:**
- [ ] Admin 권한 체크(check_admin_only) 통과
- [ ] fetch_domain_fair_shares 호출됨
- [ ] DomainFairShareConnection 타입으로 반환됨

**실패 시나리오:**
- [ ] 비관리자 사용자 접근 시 HTTPForbidden 발생
- [ ] 빈 결과 반환 시 정상 처리
---

#### 1.1.3 admin_project_fair_share (단일 조회)

**성공 시나리오:**
- [ ] Admin 권한 체크 통과
- [ ] Processor에 올바른 GetProjectFairShareAction 파라미터 전달
- [ ] 응답이 ProjectFairShareGQL 타입으로 반환됨

**실패 시나리오:**
- [ ] 비관리자 사용자 접근 시 HTTPForbidden 발생
- [ ] Service에서 ProjectNotFound 발생 시 예외가 올바르게 전파됨

---

#### 1.1.4 admin_project_fair_shares (목록 조회)

**성공 시나리오:**
- [ ] Admin 권한 체크 통과
- [ ] fetch_project_fair_shares 호출됨
- [ ] ProjectFairShareConnection 타입으로 반환됨

**실패 시나리오:**
- [ ] 비관리자 사용자 접근 시 HTTPForbidden 발생
- [ ] 빈 결과 반환 시 정상 처리

---

#### 1.1.5 admin_user_fair_share (단일 조회)

**성공 시나리오:**
- [ ] Admin 권한 체크 통과
- [ ] Processor에 올바른 GetUserFairShareAction 파라미터 전달
- [ ] 응답이 UserFairShareGQL 타입으로 반환됨

**실패 시나리오:**
- [ ] 비관리자 사용자 접근 시 HTTPForbidden 발생
- [ ] Service에서 UserNotFound 발생 시 예외가 올바르게 전파됨

---

#### 1.1.6 admin_user_fair_shares (목록 조회)

**성공 시나리오:**
- [ ] Admin 권한 체크 통과
- [ ] fetch_user_fair_shares 호출됨
- [ ] UserFairShareConnection 타입으로 반환됨

**실패 시나리오:**
- [ ] 비관리자 사용자 접근 시 HTTPForbidden 발생
- [ ] 빈 결과 반환 시 정상 처리

---

### 1.2 Resource Group Scoped Query Resolvers

#### 1.2.1 rg_domain_fair_share (Scoped 단일 조회)

**성공 시나리오:**
- [ ] Superadmin이 모든 도메인 접근 가능
- [ ] Domain Admin이 자신의 도메인만 접근 가능
- [ ] 올바른 ResourceGroupDomainScope 객체 생성 및 전달
- [ ] DomainFairShareGQL 타입으로 반환됨

**실패 시나리오:**
- [ ] Domain Admin이 다른 도메인 접근 시 HTTPForbidden 발생
- [ ] 일반 사용자 접근 시 HTTPForbidden 발생
<!-- 여기도 action 요청 실패 시 raise 되는 예외 케이스 추가 가능 -->

---

#### 1.2.2 rg_domain_fair_shares (Scoped 목록 조회)

**성공 시나리오:**
- [ ] Superadmin이 scope 내 모든 도메인 조회 가능
- [ ] Domain Admin이 자신의 도메인만 조회 가능
- [ ] DomainFairShareConnection 타입으로 반환됨

**실패 시나리오:**
- [ ] Domain Admin이 다른 도메인 포함된 결과 조회 시 필터링됨
- [ ] 일반 사용자 접근 시 HTTPForbidden 발생
<!-- 여기도 action 요청 실패 시 raise 되는 예외 케이스 추가 가능 -->

---

#### 1.2.3 rg_project_fair_share (Scoped 단일 조회)

**성공 시나리오:**
- [ ] Superadmin이 모든 프로젝트 접근 가능
- [ ] Domain Admin이 자신의 도메인 내 프로젝트 접근 가능
- [ ] Project Admin이 자신의 프로젝트 접근 가능
- [ ] Project Member가 자신의 프로젝트 접근 가능
- [ ] 올바른 ResourceGroupProjectScope 객체 생성 및 전달
- [ ] ProjectFairShareGQL 타입으로 반환됨

**실패 시나리오:**
- [ ] Domain Admin이 다른 도메인의 프로젝트 접근 시 HTTPForbidden
- [ ] Project Member가 다른 프로젝트 접근 시 HTTPForbidden
- [ ] 프로젝트에 속하지 않은 사용자 접근 시 HTTPForbidden
<!-- 여기도 action 요청 실패 시 raise 되는 예외 케이스 추가 가능 -->

---

#### 1.2.4 rg_project_fair_shares (Scoped 목록 조회)

**성공 시나리오:**
- [ ] Superadmin이 scope 내 모든 프로젝트 조회 가능
- [ ] Domain Admin이 자신의 도메인 내 프로젝트만 조회 가능
- [ ] Project Member가 자신이 속한 프로젝트만 조회 가능
- [ ] ProjectFairShareConnection 타입으로 반환됨

**실패 시나리오:**
- [ ] Domain Admin이 다른 도메인의 프로젝트 조회 시 필터링됨
- [ ] Project Member가 속하지 않은 프로젝트 조회 시 필터링됨
<!-- 여기도 action 요청 실패 시 raise 되는 예외 케이스 추가 가능 -->

---

#### 1.2.5 rg_user_fair_share (Scoped 단일 조회)

**성공 시나리오:**
- [ ] Superadmin이 모든 사용자 접근 가능
- [ ] Domain Admin이 자신의 도메인 내 사용자 접근 가능
- [ ] Project Admin이 자신의 프로젝트 내 사용자 접근 가능
- [ ] **사용자 본인이 자신의 fair share 조회 가능** (중요)
- [ ] 올바른 ResourceGroupUserScope 객체 생성 및 전달
- [ ] UserFairShareGQL 타입으로 반환됨

**실패 시나리오:**
- [ ] Domain Admin이 다른 도메인의 사용자 접근 시 HTTPForbidden
- [ ] Project Admin이 다른 프로젝트의 사용자 접근 시 HTTPForbidden
- [ ] 일반 사용자가 다른 사용자 접근 시 HTTPForbidden
<!-- 여기도 action 요청 실패 시 raise 되는 예외 케이스 추가 가능 -->

---

#### 1.2.6 rg_user_fair_shares (Scoped 목록 조회)

**성공 시나리오:**
- [ ] Superadmin이 scope 내 모든 사용자 조회 가능
- [ ] Domain Admin이 자신의 도메인 내 사용자만 조회 가능
- [ ] Project Admin이 자신의 프로젝트 내 사용자만 조회 가능
- [ ] **일반 사용자가 자신만 조회 가능** (결과 필터링)
- [ ] UserFairShareConnection 타입으로 반환됨

**실패 시나리오:**
- [ ] Domain Admin이 다른 도메인의 사용자 조회 시 필터링됨
- [ ] Project Admin이 다른 프로젝트의 사용자 조회 시 필터링됨
- [ ] 일반 사용자가 다른 사용자 포함된 결과 조회 시 본인만 필터링됨
<!-- 여기도 action 요청 실패 시 raise 되는 예외 케이스 추가 가능 -->

---

## 2. Service Layer Tests

Service 레이어는 비즈니스 로직을 처리하며, default 값 생성, Scope validation, 데이터 조합을 담당합니다.

### 2.1 Admin Query Services

#### 2.1.1 get_domain_fair_share

**성공 시나리오:**
- [ ] 레코드가 있는 도메인은 실제 fair share 데이터 반환
- [ ] 레코드가 없지만 도메인이 존재하면 default 값 반환 (weight=None, sentinel UUID)
- [ ] Default 값 생성 시 scaling_group_spec의 설정값 사용

**실패 시나리오:**
- [ ] FairShareNotFoundError 발생 → 도메인 없음 → DomainNotFound 발생
- [ ] Repository 예외는 올바르게 전파됨

#### 2.1.2 search_domain_fair_shares

**성공 시나리오:**
- [ ] Repository에서 받은 entity 결과를 올바르게 조합
- [ ] details=None인 entity는 default 값으로 변환됨
- [ ] Filter, OrderBy, Pagination 파라미터가 Repository에 전달됨
- [ ] 빈 결과 반환 시 정상 동작 (에러 없음)

**실패 시나리오:**
- [ ] Repository 예외는 올바르게 전파됨

---

#### 2.1.3 get_project_fair_share

**성공 시나리오:**
- [ ] 레코드가 있는 프로젝트는 실제 fair share 데이터 반환
- [ ] 레코드가 없지만 프로젝트가 존재하면 default 값 반환
- [ ] Default 값 생성 시 scaling_group_spec의 설정값 사용

**실패 시나리오:**
- [ ] FairShareNotFoundError 발생 → 프로젝트 없음 → ProjectNotFound 발생
- [ ] Repository 예외는 올바르게 전파됨

#### 2.1.4 search_project_fair_shares

**성공 시나리오:**
- [ ] Repository 결과를 올바르게 조합
- [ ] details=None인 entity는 default 값으로 변환됨
- [ ] 빈 결과 반환 시 정상 동작

**실패 시나리오:**
- [ ] Repository 예외는 올바르게 전파됨

---

#### 2.1.5 get_user_fair_share

**성공 시나리오:**
- [ ] 레코드가 있는 사용자는 실제 fair share 데이터 반환
- [ ] 레코드가 없지만 사용자가 존재하면 default 값 반환
- [ ] Default 값 생성 시 scaling_group_spec의 설정값 사용

**실패 시나리오:**
- [ ] FairShareNotFoundError 발생 → 사용자 없음 → UserNotFound 발생
- [ ] Repository 예외는 올바르게 전파됨

#### 2.1.6 search_user_fair_shares

**성공 시나리오:**
- [ ] Repository 결과를 올바르게 조합
- [ ] details=None인 entity는 default 값으로 변환됨
- [ ] 빈 결과 반환 시 정상 동작

**실패 시나리오:**
- [ ] Repository 예외는 올바르게 전파됨

---

### 2.2 Resource Group Scoped Query Services

#### 2.2.1 search_rg_domain_fair_shares

**성공 시나리오:**
- [ ] Scope의 resource_group 필터가 Repository에 전달됨
- [ ] Scope의 domain_name 필터가 Repository에 전달됨 (지정된 경우)
- [ ] 레코드 없는 도메인도 default 값으로 반환
- [ ] 추가 Filter, OrderBy, Pagination 파라미터 적용

**실패 시나리오:**
- [ ] Repository 예외는 올바르게 전파됨

---

#### 2.2.2 search_rg_project_fair_shares

**성공 시나리오:**
- [ ] Scope 필터가 Repository에 올바르게 전달됨
- [ ] 레코드 없는 프로젝트도 default 값으로 반환
- [ ] 추가 Filter, OrderBy, Pagination 파라미터 적용

**실패 시나리오:**
- [ ] Repository 예외는 올바르게 전파됨

---

#### 2.2.3 search_rg_user_fair_shares

**성공 시나리오:**
- [ ] Scope 필터가 Repository에 올바르게 전달됨
- [ ] 레코드 없는 사용자도 default 값으로 반환
- [ ] 추가 Filter, OrderBy, Pagination 파라미터 적용

**실패 시나리오:**
- [ ] Repository 예외는 올바르게 전파됨

---

## 3. Repository Layer Tests

Repository 레이어는 데이터베이스 접근을 담당하며, SQL 쿼리 실행, JOIN 처리, 결과 변환을 수행합니다.

### 3.1 Entity-Based Search Methods

#### 3.1.1 search_domain_fair_share_entities

**성공 시나리오:**
- [ ] LEFT JOIN으로 모든 도메인 엔티티 반환 (fair share 레코드 유무 무관)
- [ ] Fair share 레코드가 있는 도메인: details 필드에 데이터 채워짐
- [ ] Fair share 레코드가 없는 도메인: details=None
- [ ] Filter 조건(resource_group, domain_name)이 WHERE 절에 정확히 적용됨
- [ ] OrderBy가 ORDER BY 절에 정확히 적용됨
  - fair_share_factor (details 필드 사용)
  - domain_name
  - created_at
- [ ] Pagination (limit, offset) 정확히 동작
- [ ] total_count 정확히 계산됨
- [ ] 도메인이 하나도 없으면 빈 결과 반환

**실패 시나리오:**
- [ ] 존재하지 않는 resource_group 필터 시 빈 결과 반환

---

#### 3.1.2 search_project_fair_share_entities

**성공 시나리오:**
- [ ] LEFT JOIN으로 모든 프로젝트 엔티티 반환
- [ ] Fair share 레코드가 있는 프로젝트: details 필드 채워짐
- [ ] Fair share 레코드가 없는 프로젝트: details=None
- [ ] Filter 조건(resource_group, project_id, domain_name)이 WHERE 절에 정확히 적용됨
- [ ] OrderBy(fair_share_factor, created_at) 정확히 동작
- [ ] Pagination 정확히 동작
- [ ] total_count 정확히 계산됨
- [ ] 프로젝트와 도메인 관계 JOIN 정확히 처리됨

**실패 시나리오:**
- [ ] 존재하지 않는 resource_group 필터 시 빈 결과 반환
- [ ] 존재하지 않는 domain_name 필터 시 빈 결과 반환

---

#### 3.1.3 search_user_fair_share_entities

**성공 시나리오:**
- [ ] LEFT JOIN으로 모든 사용자 엔티티 반환
- [ ] Fair share 레코드가 있는 사용자: details 필드 채워짐
- [ ] Fair share 레코드가 없는 사용자: details=None
- [ ] Filter 조건(resource_group, user_uuid, project_id, domain_name)이 WHERE 절에 정확히 적용됨
- [ ] OrderBy(fair_share_factor, created_at) 정확히 동작
- [ ] Pagination 정확히 동작
- [ ] total_count 정확히 계산됨
- [ ] 사용자-프로젝트-도메인 관계 JOIN 정확히 처리됨

**실패 시나리오:**
- [ ] 존재하지 않는 resource_group 필터 시 빈 결과 반환
- [ ] 존재하지 않는 project_id 필터 시 빈 결과 반환

---

## 테스트 구현 가이드

### Resolver Layer 테스트 패턴
```python
# resolver/domain.py의 resolver 함수 테스트
resolver_fn = domain_resolver.admin_domain_fair_share.base_resolver
result = await resolver_fn(mock_info, resource_group="default", domain_name="test")

# 권한 체크 테스트
monkeypatch.setattr(domain_resolver, "current_user", lambda: mock_regular_user)
with pytest.raises(web.HTTPForbidden):
    await resolver_fn(mock_info, ...)
```

### Service Layer 테스트 패턴
```python
# service 메서드 직접 호출
result = await fair_share_service.search_domain_fair_shares(
    querier=mock_querier,
    filter=mock_filter,
)

# default 값 생성 검증
assert result.items[0].details is None  # 레코드 없는 경우
assert result.items[0].fair_share_factor == 1.0  # default 값
```

### Repository Layer 테스트 패턴
```python
# 실제 DB 사용 (with_tables)
async with with_tables(db, [DomainRow, ScalingGroupRow, ...]):
    # 테스트 데이터 생성
    domain_with_record = await create_domain_with_fair_share(...)
    domain_without_record = await create_domain(...)

    # Repository 메서드 호출
    result = await repository.search_domain_fair_share_entities(querier)

    # 검증
    assert len(result.items) == 2
    assert result.items[0].details is not None
    assert result.items[1].details is None
```

---

## 시나리오 요약

### 레이어별 테스트 개수
- **GQL Resolver Layer**: 12개 API (Admin 6개 + Scoped 6개) × 평균 3개 시나리오 = **약 36개**
- **Service Layer**: 6개 메서드 (Admin 3개 + Scoped 3개) × 평균 5개 시나리오 = **약 30개**
- **Repository Layer**: 3개 메서드 × 평균 8개 시나리오 = **약 24개**
- **합계**: **약 90개 테스트 시나리오**

### 레이어별 주요 검증 사항
| 레이어 | 주요 검증 | 예외 처리 |
|--------|----------|----------|
| Resolver | 권한 체크, Processor 호출, 응답 타입 | HTTPForbidden |
| Service | Default 값 생성, Scope validation, 데이터 조합 | NotFound 예외 (Scaling Group, Domain, Project, User) |
| Repository | SQL 쿼리, LEFT JOIN, Filter/OrderBy/Pagination | 빈 결과 반환 |
