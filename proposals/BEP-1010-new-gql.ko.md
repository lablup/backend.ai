# BEP-1010: GraphQL API 를 Strawberry 로 이전

## 개요

이 BEP 는 GraphQL API 구현을 폐기 예정인 Graphene 라이브러리에서 Strawberry 로 이전하는 전략을 정리한다. 새 엔드포인트의 생성과 기존 엔드포인트와의 federation 을 포함한다.

## 배경

- 현재 구현은 GraphQL API 에 Graphene 을 사용한다
- Graphene 은 폐기 예정이므로 Strawberry 로 이전해야 한다
- 기존 엔드포인트에는 해결해야 할 설계 한계가 있다
  - 적절한 필터링 수단이 없다
  - pagination 방식이 일관되지 않다
  - 타입 안전성이 낮다
  - 표준을 따르지 않는 GraphQL 관행이 있다
- 전환하는 동안 하위 호환성을 유지해야 한다
- 점진적 이전을 위해 federation 이 필요하다

## 목표

1. **주요 이전**: 새 GraphQL 엔드포인트를 Strawberry 로 구현한다
2. **federation**: 새 Strawberry 엔드포인트와 기존 Graphene 엔드포인트 사이의 federation 을 가능하게 한다
3. **설계 개선**: 엔드포인트를 GraphQL 규약에 더 맞게 다시 설계한다
4. **타입 안전성**: query 와 mutation 에 타입 기반 연산을 제대로 구현한다
5. **성능**: 더 나은 질의 최적화와 캐싱을 달성한다
6. **개발자 경험**: 더 나은 도구와 문서를 제공한다

## 기술 스택

- **Strawberry GraphQL**: 최신 stable version (>= 0.200.0)
- **Apollo Federation**: schema 구성에 사용한다
- **Python 3.9+**: 실행 환경
- **AsyncIO**: 비동기 연산에 사용한다
- **pydantic**: 데이터 검증과 직렬화에 사용한다

## 기술 요구 사항

### 핵심 기능

1. **필터 시스템**
   - GraphQL 필터링 수단을 제대로 구현한다
   - 복잡한 필터 연산을 지원한다
   - 타입 안전한 필터 정의를 둔다
   - 중첩 필터링을 지원한다

   **구현 예시:**
   ```python
   import strawberry
   from typing import Optional, List
   from enum import Enum
   
   @strawberry.enum
   class StringFilterOperator(Enum):
       EQ = "eq"
       CONTAINS = "contains"
       STARTS_WITH = "starts_with"
       ENDS_WITH = "ends_with"
   
   @strawberry.input
   class StringFilter:
       operator: StringFilterOperator
       value: str
   
   @strawberry.input
   class UserFilter:
       name: Optional[StringFilter] = None
       email: Optional[StringFilter] = None
       created_at: Optional[DateTimeFilter] = None
       and_: Optional[List["UserFilter"]] = None
       or_: Optional[List["UserFilter"]] = None
   
   @strawberry.type
   class Query:
       @strawberry.field
       async def users(
           self,
           filter: Optional[UserFilter] = None,
           info: strawberry.Info
       ) -> List[User]:
           # Convert GraphQL filter to database query
           query = build_database_query(filter)
           return await execute_query(query)
   ```

2. **정렬**
   - GraphQL 규약을 따르는 정렬 시스템
   - 여러 field 정렬 지원
   - 오름차순, 내림차순 옵션
   - null 처리 옵션

   **구현 예시:**
   ```python
   @strawberry.enum
   class OrderDirection(Enum):
       ASC = "asc"
       DESC = "desc"
   
   @strawberry.enum
   class NullsOrder(Enum):
       FIRST = "first"
       LAST = "last"
   
   @strawberry.input
   class OrderBy:
       field: str
       direction: OrderDirection = OrderDirection.ASC
       nulls: Optional[NullsOrder] = None
   
   @strawberry.type
   class Query:
       @strawberry.field
       async def users(
           self,
           order_by: Optional[List[OrderBy]] = None,
           info: strawberry.Info
       ) -> List[User]:
           # Convert GraphQL ordering to database query
           query = build_ordered_query(order_by)
           return await execute_query(query)
   ```

3. **pagination**
   - Relay 방식 cursor pagination 을 구현한다
   - 필요한 곳에서는 offset 기반 pagination 을 지원한다
   - 적절한 connection 타입
   - 정방향, 역방향 pagination

   **구현 예시:**
   ```python
   @strawberry.type
   class PageInfo:
       has_next_page: bool
       has_previous_page: bool
       start_cursor: Optional[str]
       end_cursor: Optional[str]
   
   @strawberry.type
   class UserEdge:
       cursor: str
       node: User
   
   @strawberry.type
   class UserConnection:
       edges: List[UserEdge]
       page_info: PageInfo
       total_count: int
   
   @strawberry.type
   class Query:
       @strawberry.field
       async def users(
           self,
           first: Optional[int] = None,
           after: Optional[str] = None,
           last: Optional[int] = None,
           before: Optional[str] = None,
           info: strawberry.Info
       ) -> UserConnection:
           # Implement cursor-based pagination
           return await paginate_users(first, after, last, before)
   ```

4. **타입 시스템**
   - 모든 GraphQL 연산에 강한 타입을 적용한다
   - 적절한 입력, 출력 타입 정의
   - 타입 기반 query, mutation 연산
   - 자동 검증과 직렬화

   **구현 예시:**
   ```python
   from datetime import datetime
   from typing import Optional
   import strawberry
   from pydantic import BaseModel, validator
   
   @strawberry.type
   class User:
       id: strawberry.ID
       name: str
       email: str
       created_at: datetime
       updated_at: datetime
   
   @strawberry.input
   class CreateUserInput:
       name: str
       email: str
       
       @validator('email')
       def validate_email(cls, v):
           if '@' not in v:
               raise ValueError('Invalid email format')
           return v
   
   @strawberry.input
   class UpdateUserInput:
       name: Optional[str] = None
       email: Optional[str] = None
   
   @strawberry.type
   class Mutation:
       @strawberry.mutation
       async def create_user(
           self,
           input: CreateUserInput,
           info: strawberry.Info
       ) -> User:
           # Type-safe mutation with automatic validation
           user_data = input.__dict__
           return await create_user_service(user_data)
   ```

### federation 전략

1. **엔드포인트 공존**
   - 새 Strawberry 엔드포인트를 기존 Graphene 엔드포인트와 함께 둔다
   - 두 구현을 하나로 묶는 federation 계층
   - 점진적 이전 경로
   - 무중단 이전

2. **schema 구성**
   - 두 구현을 합친 단일 schema
   - 적절한 타입 병합과 충돌 해결
   - 일관된 API 노출 범위
   - version 호환성 관리

   **구현 예시:**
   ```python
   # Strawberry service (new)
   import strawberry
   from strawberry.federation import build_schema
   
   @strawberry.federation.type(keys=["id"])
   class User:
       id: strawberry.ID
       name: str
       email: str
   
   @strawberry.type
   class Query:
       @strawberry.field
       async def user(self, id: strawberry.ID) -> Optional[User]:
           return await get_user_by_id(id)
   
   schema = build_schema(Query)
   
   # Apollo Gateway configuration
   # gateway.js
   const { ApolloGateway } = require('@apollo/gateway');
   
   const gateway = new ApolloGateway({
     serviceList: [
       { name: 'users-legacy', url: 'http://localhost:4001/graphql' }, // Graphene
       { name: 'users-new', url: 'http://localhost:4002/graphql' },     // Strawberry
     ],
   });
   ```

3. **이전 전략**
   - feature flag 기반 라우팅
   - 점진적 트래픽 전환
   - rollback 수단
   - 데이터 일관성 검사

   **구현 예시:**
   ```python
   # Feature flag-based routing
   @strawberry.type
   class Query:
       @strawberry.field
       async def users(
           self,
           filter: Optional[UserFilter] = None,
           info: strawberry.Info
       ) -> List[User]:
           # Check feature flag
           if await is_feature_enabled("strawberry_users", info.context):
               return await new_users_service(filter)
           else:
               return await legacy_users_service(filter)
   ```

## 구현 계획

### 1단계: 기반 구성 (1~2주)
- Strawberry 인프라를 구성한다
- 기본 타입과 schema 를 정의한다
- 핵심 유틸리티(pagination, 필터링, 정렬)를 구현한다
- 개발 환경과 도구를 구성한다
- 프로젝트 구조와 설정을 생성한다

**산출물:**
- Strawberry 프로젝트 구성
- 기본 타입 정의
- 핵심 유틸리티 함수
- 개발 환경 설정

### 2단계: 새 엔드포인트 개발 (3~6주)
- Strawberry 로 새 엔드포인트를 생성한다
- 개선한 필터링, 정렬, pagination 을 구현한다
- 모든 연산에 타입 안전성을 확보한다
- 포괄적인 에러 처리를 추가한다
- 인증과 인가를 구현한다

**산출물:**
- 사용자 관리 엔드포인트
- 세션 관리 엔드포인트
- kernel 관리 엔드포인트
- 포괄적인 테스트 스위트

### 3단계: federation 구현 (7~8주)
- Strawberry 엔드포인트와 Graphene 엔드포인트 사이의 federation 을 구성한다
- schema 구성과 호환성을 테스트한다
- 충돌 해결 전략을 구현한다
- Apollo Gateway 를 구성한다
- 라우팅과 로드밸런싱을 설정한다

**산출물:**
- Apollo Gateway 설정
- federation schema 구성
- 충돌 해결 수단
- 통합 테스트

### 4단계: 이전과 최적화 (9~12주)
- 기존 기능을 점진적으로 이전한다
- 성능 최적화
- 문서와 테스트
- feature flag 구현
- 프로덕션 배포 준비

**산출물:**
- 이전 스크립트
- 성능 벤치마크
- 프로덕션 배포 안내
- rollback 절차
- 모니터링과 알림 구성

## 추가 고려 사항

1. **성능**
   - 질의 최적화 전략
   - 캐싱 수단(Valkey, 메모리 내)
   - 데이터베이스 질의 효율
   - N+1 질의를 방지하는 DataLoader 패턴
   - connection pooling

   **구현 예시:**
   ```python
   from strawberry.dataloader import DataLoader
   from typing import List
   
   async def load_users_by_ids(ids: List[str]) -> List[User]:
       # Batch load users to prevent N+1 queries
       return await batch_get_users(ids)
   
   @strawberry.type
   class Query:
       @strawberry.field
       async def posts(self, info: strawberry.Info) -> List[Post]:
           user_loader = DataLoader(load_users_by_ids)
           posts = await get_posts()
           
           # Load users in batch
           for post in posts:
               post.user = await user_loader.load(post.user_id)
           
           return posts
   ```

2. **보안**
   - 입력 검증과 정제
   - 질의 깊이 제한
   - 최대 요청수 적용 고려 사항
   - 인증과 인가
   - CORS 설정

   **구현 예시:**
   ```python
   from strawberry.permission import BasePermission
   from strawberry.types import Info
   
   class IsAuthenticated(BasePermission):
       message = "User is not authenticated"
       
       def has_permission(self, source, info: Info, **kwargs) -> bool:
           return info.context.user is not None
   
   class IsOwner(BasePermission):
       message = "User is not the owner"
       
       def has_permission(self, source, info: Info, **kwargs) -> bool:
           return source.user_id == info.context.user.id
   
   @strawberry.type
   class Mutation:
       @strawberry.mutation(permission_classes=[IsAuthenticated])
       async def create_post(self, input: CreatePostInput) -> Post:
           return await create_post_service(input)
   
   # Query depth limiting
   from strawberry.extensions import QueryDepthLimiter
   
   schema = strawberry.Schema(
       query=Query,
       extensions=[
           QueryDepthLimiter(max_depth=10)
       ]
   )
   ```

3. **개발자 경험**
   - 명확한 문서
   - 타입 정의와 도구
   - 이전 안내
   - GraphQL playground 통합
   - schema introspection

4. **테스트**
   - 포괄적인 테스트 커버리지
   - federation 테스트
   - 성능 벤치마크
   - 통합 테스트
   - 부하 테스트

   **구현 예시:**
   ```python
   import pytest
   from strawberry.test import BaseGraphQLTestClient
   
   @pytest.fixture
   def client():
       return BaseGraphQLTestClient(schema)
   
   async def test_create_user(client):
       query = """
       mutation {
           createUser(input: { name: "John Doe", email: "john@example.com" }) {
               id
               name
               email
           }
       }
       """
       
       result = await client.query(query)
       assert result.errors is None
       assert result.data["createUser"]["name"] == "John Doe"
   ```

5. **모니터링**
   - 질의 성능 지표
   - 에러 추적
   - 사용량 분석
   - 헬스 체크
   - 분산 트레이싱

   **구현 예시:**
   ```python
   from strawberry.extensions import SchemaExtension
   from opentelemetry import trace
   import time
   
   class MetricsExtension(SchemaExtension):
       def on_request_start(self):
           self.start_time = time.time()
       
       def on_request_end(self, result):
           duration = time.time() - self.start_time
           
           # Log metrics
           logger.info(f"GraphQL query completed in {duration:.2f}s")
           
           # Send to monitoring service
           metrics.histogram("graphql.query.duration", duration)
   
   schema = strawberry.Schema(
       query=Query,
       extensions=[MetricsExtension()]
   )
   ```

6. **에러 처리**
   - 일관된 에러 응답 형식
   - 에러 분류
   - 적절한 HTTP 상태 코드
   - 에러 로깅과 추적

   **구현 예시:**
   ```python
   from enum import Enum
   import strawberry
   
   @strawberry.enum
   class ErrorCode(Enum):
       VALIDATION_ERROR = "VALIDATION_ERROR"
       NOT_FOUND = "NOT_FOUND"
       UNAUTHORIZED = "UNAUTHORIZED"
       INTERNAL_ERROR = "INTERNAL_ERROR"
   
   @strawberry.type
   class Error:
       code: ErrorCode
       message: str
       field: Optional[str] = None
   
   @strawberry.type
   class UserResult:
       user: Optional[User] = None
       errors: List[Error] = strawberry.field(default_factory=list)
   
   @strawberry.type
   class Mutation:
       @strawberry.mutation
       async def create_user(self, input: CreateUserInput) -> UserResult:
           try:
               user = await create_user_service(input)
               return UserResult(user=user)
           except ValidationError as e:
               return UserResult(
                   errors=[
                       Error(
                           code=ErrorCode.VALIDATION_ERROR,
                           message=str(e),
                           field=e.field_name
                       )
                   ]
               )
   ```

## 성공 기준

- [ ] 새 엔드포인트를 Strawberry 로 구현
- [ ] 기존 엔드포인트와 새 엔드포인트 사이의 federation 동작
- [ ] GraphQL 규약 준수 개선(필터링, 정렬, pagination)
- [ ] 모든 연산의 타입 안전성
- [ ] 하위 호환성 유지
- [ ] 성능 지표가 현재 구현과 같거나 높은 수준
- [ ] 무중단 이전 가능
- [ ] 포괄적인 테스트 커버리지(90% 초과)
- [ ] 프로덕션 모니터링과 알림 구성
- [ ] 개발자 문서 완성
- [ ] 이전 runbook 문서화

## 일정

**전체 기간**: 12주

- **1~2주**: 기반 구성
- **3~6주**: 새 엔드포인트 개발
- **7~8주**: federation 구현
- **9~12주**: 이전과 최적화

**마일스톤:**
- 2주: 기본 Strawberry 구성 시연
- 4주: 새 기능을 갖춘 첫 동작 엔드포인트
- 6주: 엔드포인트 전체 범위 확보
- 8주: staging 에서 federation 동작
- 10주: 성능 벤치마크 완료
- 12주: 프로덕션 배포 준비 완료

## 위험 완화

1. **기술 위험**
   - schema 호환성 문제 → 포괄적인 테스트와 검증
   - 성능 저하 → 벤치마크와 최적화
   - federation 복잡도 → fallback 을 둔 점진적 배포

2. **운영 위험**
   - 배포 문제 → 블루그린 배포 전략
   - 데이터 불일치 → 트랜잭션 관리와 rollback 절차
   - 모니터링 공백 → 포괄적인 observability 구성

3. **일정 위험**
   - 범위 확대 → 명확한 요구 사항과 변경 관리
   - 자원 제약 → 병렬 개발과 우선순위 조정
   - 의존성 → 명확한 의존성 정리와 대비 계획

## 참고

- [Strawberry GraphQL 문서](https://strawberry.rocks/)
- [GraphQL federation 명세](https://www.apollographql.com/docs/federation/)
- [Relay cursor pagination](https://relay.dev/graphql/connections.htm)
- [GraphQL 모범 사례](https://graphql.org/learn/best-practices/)
- [Apollo Gateway 문서](https://www.apollographql.com/docs/apollo-server/federation/gateway/)
- [pydantic 문서](https://pydantic-docs.helpmanual.io/)
- [OpenTelemetry Python](https://opentelemetry-python.readthedocs.io/)
- [GraphQL 보안 모범 사례](https://github.com/dolevf/graphql-security-cheat-sheet)

## 부록

### A. 이전 체크리스트

**이전 전**
- [ ] 현재 API 감사 완료
- [ ] 성능 기준선 수립
- [ ] 테스트 커버리지 분석
- [ ] 의존성 파악
- [ ] 팀 교육 완료

**이전 중**
- [ ] feature flag 구현
- [ ] 모니터링 대시보드 생성
- [ ] rollback 절차 테스트
- [ ] 성능 모니터링 활성
- [ ] 에러 추적 설정

**이전 후**
- [ ] 성능 비교 완료
- [ ] 사용자 피드백 수집
- [ ] 문서 갱신
- [ ] 팀 회고 진행
- [ ] 교훈 문서화

### B. 설정 예시

**Docker 설정**
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**프로덕션 설정**
```python
# settings.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    database_url: str
    redis_url: str
    jwt_secret: str
    cors_origins: List[str]
    debug: bool = False
    
    class Config:
        env_file = ".env"

settings = Settings()
```
