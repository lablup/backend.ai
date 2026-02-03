---
Author:
Status: Accepted
Created:
Created-Version:
Target-Version:
Implemented-Version:
---

# BEP-1010: GraphQL API Migration to Strawberry

## Overview

This BEP outlines the migration strategy from the deprecated Graphene library to Strawberry for GraphQL API implementation, including the creation of new endpoints and federation with existing ones.

## Background

- Current implementation uses Graphene for GraphQL API
- Graphene is deprecated and needs migration to Strawberry
- Existing endpoints have design limitations that need to be addressed:
  - Lack of proper filtering mechanisms
  - Inconsistent pagination patterns
  - Poor type safety
  - Non-standard GraphQL practices
- Need to maintain backward compatibility during transition
- Federation is required to enable gradual migration

## Goals

1. **Primary Migration**: Implement new GraphQL endpoints using Strawberry
2. **Federation**: Enable federation between new Strawberry endpoints and existing Graphene endpoints
3. **Improved Design**: Redesign endpoints to be more GraphQL-compliant
4. **Type Safety**: Implement proper type-based operations for queries and mutations
5. **Performance**: Achieve better query optimization and caching
6. **Developer Experience**: Provide better tooling and documentation

## Technical Stack

- **Strawberry GraphQL**: Latest stable version (>= 0.200.0)
- **Apollo Federation**: For schema composition
- **Python 3.9+**: Runtime environment
- **AsyncIO**: For async operations
- **Pydantic**: For data validation and serialization

## Technical Requirements

### Core Features

1. **Filter System**
   - Implement proper GraphQL filtering mechanisms
   - Support for complex filter operations
   - Type-safe filter definitions
   - Support for nested filtering

   **Implementation Example:**
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

2. **Ordering**
   - GraphQL-compliant ordering system
   - Support for multiple field ordering
   - Ascending/descending order options
   - Null handling options

   **Implementation Example:**
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

3. **Pagination**
   - Implement Relay-style cursor pagination
   - Support for offset-based pagination where needed
   - Proper connection types
   - Forward and backward pagination

   **Implementation Example:**
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

4. **Type System**
   - Strong typing for all GraphQL operations
   - Proper input/output type definitions
   - Type-based query and mutation operations
   - Automatic validation and serialization

   **Implementation Example:**
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

### Federation Strategy

1. **Endpoint Coexistence**
   - New Strawberry endpoints alongside existing Graphene endpoints
   - Federation layer to unify both implementations
   - Gradual migration path
   - Zero-downtime migration

2. **Schema Composition**
   - Unified schema combining both implementations
   - Proper type merging and conflict resolution
   - Consistent API surface
   - Version compatibility management

   **Implementation Example:**
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

3. **Migration Strategy**
   - Feature flag-based routing
   - Gradual traffic shifting
   - Rollback capabilities
   - Data consistency checks

   **Implementation Example:**
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

## Implementation Plan

### Phase 1: Foundation Setup (Week 1-2)
- Set up Strawberry infrastructure
- Define base types and schemas
- Implement core utilities (pagination, filtering, ordering)
- Set up development environment and tooling
- Create project structure and configuration

**Deliverables:**
- Strawberry project setup
- Base type definitions
- Core utility functions
- Development environment configuration

### Phase 2: New Endpoint Development (Week 3-6)
- Create new endpoints using Strawberry
- Implement improved filtering, ordering, and pagination
- Ensure type safety across all operations
- Add comprehensive error handling
- Implement authentication and authorization

**Deliverables:**
- User management endpoints
- Session management endpoints
- Kernel management endpoints
- Comprehensive test suite

### Phase 3: Federation Implementation (Week 7-8)
- Set up federation between Strawberry and Graphene endpoints
- Test schema composition and compatibility
- Implement conflict resolution strategies
- Set up Apollo Gateway
- Configure routing and load balancing

**Deliverables:**
- Apollo Gateway configuration
- Federation schema composition
- Conflict resolution mechanisms
- Integration tests

### Phase 4: Migration and Optimization (Week 9-12)
- Gradually migrate existing functionality
- Performance optimization
- Documentation and testing
- Feature flag implementation
- Production deployment preparation

**Deliverables:**
- Migration scripts
- Performance benchmarks
- Production deployment guide
- Rollback procedures
- Monitoring and alerting setup

## Additional Considerations

1. **Performance**
   - Query optimization strategies
   - Caching mechanisms (Redis, in-memory)
   - Database query efficiency
   - DataLoader pattern for N+1 query prevention
   - Connection pooling

   **Implementation Example:**
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

2. **Security**
   - Input validation and sanitization
   - Query depth limiting
   - Rate limiting considerations
   - Authentication and authorization
   - CORS configuration

   **Implementation Example:**
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

3. **Developer Experience**
   - Clear documentation
   - Type definitions and tooling
   - Migration guides
   - GraphQL playground integration
   - Schema introspection

4. **Testing**
   - Comprehensive test coverage
   - Federation testing
   - Performance benchmarks
   - Integration tests
   - Load testing

   **Implementation Example:**
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

5. **Monitoring**
   - Query performance metrics
   - Error tracking
   - Usage analytics
   - Health checks
   - Distributed tracing

   **Implementation Example:**
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

6. **Error Handling**
   - Consistent error response format
   - Error categorization
   - Proper HTTP status codes
   - Error logging and tracking

   **Implementation Example:**
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

## Success Criteria

- [ ] New endpoints implemented with Strawberry
- [ ] Federation working between old and new endpoints
- [ ] Improved GraphQL compliance (filtering, ordering, pagination)
- [ ] Type-safe operations throughout
- [ ] Backward compatibility maintained
- [ ] Performance metrics meet or exceed current implementation
- [ ] Zero-downtime migration capability
- [ ] Comprehensive test coverage (>90%)
- [ ] Production monitoring and alerting in place
- [ ] Developer documentation completed
- [ ] Migration runbook documented

## Timeline

**Total Duration**: 12 weeks

- **Week 1-2**: Foundation Setup
- **Week 3-6**: New Endpoint Development
- **Week 7-8**: Federation Implementation
- **Week 9-12**: Migration and Optimization

**Milestones:**
- Week 2: Demo of basic Strawberry setup
- Week 4: First working endpoint with new features
- Week 6: Complete endpoint coverage
- Week 8: Federation working in staging
- Week 10: Performance benchmarks completed
- Week 12: Production deployment ready

## Risk Mitigation

1. **Technical Risks**
   - Schema compatibility issues → Comprehensive testing and validation
   - Performance degradation → Benchmarking and optimization
   - Federation complexity → Gradual rollout with fallbacks

2. **Operational Risks**
   - Deployment issues → Blue-green deployment strategy
   - Data inconsistency → Transaction management and rollback procedures
   - Monitoring gaps → Comprehensive observability setup

3. **Timeline Risks**
   - Scope creep → Clear requirements and change management
   - Resource constraints → Parallel development and prioritization
   - Dependencies → Clear dependency mapping and contingency plans

## References

- [Strawberry GraphQL Documentation](https://strawberry.rocks/)
- [GraphQL Federation Specification](https://www.apollographql.com/docs/federation/)
- [Relay Cursor Pagination](https://relay.dev/graphql/connections.htm)
- [GraphQL Best Practices](https://graphql.org/learn/best-practices/)
- [Apollo Gateway Documentation](https://www.apollographql.com/docs/apollo-server/federation/gateway/)
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)
- [OpenTelemetry Python](https://opentelemetry-python.readthedocs.io/)
- [GraphQL Security Best Practices](https://github.com/dolevf/graphql-security-cheat-sheet)

## Appendix

### A. Migration Checklist

**Pre-Migration**
- [ ] Current API audit completed
- [ ] Performance baseline established
- [ ] Test coverage analysis
- [ ] Dependencies identified
- [ ] Team training completed

**During Migration**
- [ ] Feature flags implemented
- [ ] Monitoring dashboards created
- [ ] Rollback procedures tested
- [ ] Performance monitoring active
- [ ] Error tracking configured

**Post-Migration**
- [ ] Performance comparison completed
- [ ] User feedback collected
- [ ] Documentation updated
- [ ] Team retrospective conducted
- [ ] Lessons learned documented

### B. Configuration Examples

**Docker Configuration**
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Production Configuration**
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