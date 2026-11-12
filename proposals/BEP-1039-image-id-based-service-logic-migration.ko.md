# Image ID 기반 service 로직 이관

## 이관 로드맵

이미지 관련 ID 기반 이관은 세 단계로 나눈다.

```
┌────────────────────────────────────────────────────────────────────────────┐
│  1. BEP-1039 (this doc)     2. BEP-1038               3. (future)          │
│  Service Logic Migration  → ImageV2 Schema Addition → API Migration        │
│  ───────────────────────    ─────────────────────     ────────────────     │
│  • Add ById Actions         • New GQL schema design   • Client SDK ext.    │
│  • Repository Layer         • gql_relay impl.         • CLI extension      │
│  • Cache Layer              • ID-based Query/Mutation • REST API ext.      │
│  • Keep legacy Actions      • Coexist with legacy API • Deprecation        │
└────────────────────────────────────────────────────────────────────────────┘
```

## 동기

지금 Backend.AI 에서 이미지와 관련된 내부 로직은 대부분 `image_canonical` 을 기준으로 동작한다. `image_canonical` 은 문자열 형태의 이미지 참조이며 `registry/project/image:tag` 처럼 사용한다.
이 방식에는 다음 문제가 있다.

1. **성능 문제**: 문자열 기반 조회는 UUID 기반 조회보다 효율이 낮다
2. **일관성 문제**: 같은 이미지가 서로 다른 canonical 표기를 가질 수 있다 (registry domain 변경, tag 변경 등)
3. **참조 무결성**: 문자열은 foreign key 제약과 함께 사용하기 어렵다
4. **캐시 키 불일치**: legacy 시스템은 canonical 문자열을 캐시 키로 사용하고, 새 시스템은 ImageID 를 사용해서 값이 어긋난다

`image_id`(UUID 기반)로 전환하면 다음을 얻는다.
- 불변인 고유 식별자로 일관성을 보장한다
- database 조회 성능이 좋아진다 (인덱스 효율)
- 타입 안전성 (`NewType("ImageID", UUID)`)

## 현재 설계

### 식별자 체계

| 식별자 | 타입 | 저장 위치 | 용도 |
|------------|------|------------------|---------|
| `image_id` (ImageID) | `UUID` | `ImageRow.id` | 내부 DB primary key |
| `image_canonical` | `str` | `ImageRow.name` | 사용자가 읽기 쉬운 참조 (예: `registry/project/image:tag`) |

### 현재 데이터 흐름

```
API (canonical) → Action (canonical) → Repository (canonical lookup) → Cache (canonical key)
```

### 타입 정의 (현재)

```python
# ai/backend/common/types.py
ImageCanonical = NewType("ImageCanonical", str)
ImageID = NewType("ImageID", UUID)

# ai/backend/manager/data/image/types.py
class ImageIdentifier(NamedTuple):
    """Represent a tuple of image's canonical string and architecture"""
    canonical: str
    architecture: str
```

### GraphQL API (현재)

```graphql
# Query - canonical based
query {
  image(reference: "python:3.11", architecture: "x86_64") {
    id
    name
    ...
  }
}

# Mutation - canonical based
mutation {
  alias_image(target: "cr.backend.ai/stable/python:3.11", alias: "python", architecture: "x86_64") {
    ok
  }
}
```

### 세션 생성 (현재)

```python
# ai/backend/manager/services/session/service.py
image_row = await self._session_repository.resolve_image([
    ImageIdentifier(image, architecture),  # canonical based
    ImageAlias(image),                      # alias based
])
```

### 이미 ID 기반인 코드

일부 코드는 이미 `image_id` 를 기준으로 동작한다.

- `GetImageByIdAction`
- `ForgetImageByIdAction`
- `PurgeImageByIdAction`
- `RemoveAgentFromImagesAction`
- `ValkeyImageClient.add_agent_to_images(image_ids)`
- `ValkeyImageClient.remove_agent_from_images(image_ids)`
- GraphQL: `ForgetImageById`, `PurgeImageById` mutations

남은 Action 은 이 패턴을 따라 ById 버전을 새로 생성한다.

## 제안 설계

### 이 BEP 의 범위: service 로직 이관

이 BEP 는 세 단계 이관 중 **1단계인 내부 service 로직 이관**을 다룬다.

**이 BEP 가 다루는 것:**
- Action 계층: 새 ById Action 을 생성한다 (legacy Action 은 그대로 둔다)
- Repository 계층: image_id 기반 조회 메서드를 추가한다
- 캐시 계층: 새 ById Action 은 image_id 키로 통일한다
- DataLoader: 새 API 용으로 image_id 기반 batch load 를 추가한다
- 새 API(BEP-1038)는 ById Action 을 직접 사용한다

**이 BEP 가 다루지 않는 것:**
- 새 GraphQL schema → BEP-1038
- 클라이언트 SDK, CLI 확장 → 이후 API 이관 BEP

### 목표

1. `image_id` 기반 동작을 위한 새 **ById Action** 을 생성한다 (이 BEP 범위)
2. gql_legacy 와의 하위 호환을 위해 기존 **legacy Action 을 그대로 둔다**
3. 새 ID 기반 API(BEP-1038)는 ById Action 을 직접 사용한다
4. legacy Action 은 3단계에서 deprecated 로 표기한다

### 이관 후 데이터 흐름

**Legacy API (gql_legacy): 변경 없음**
```
Legacy API (canonical)
  → Legacy Action (canonical)
  → Repository (canonical lookup)
  → Cache (canonical key)
```

**New API (gql_relay, BEP-1038): ById Action 사용**
```
New API (image_id)
  → ById Action (image_id)
  → Repository (image_id lookup)
  → Cache (image_id key)
```

두 흐름은 3단계에서 legacy API 가 deprecated 로 표기되기 전까지 함께 동작한다.

### Legacy API: 변경 없음 (gql_legacy)

기존 GraphQL API(gql_legacy)는 **canonical 기반 legacy Action 을 변경 없이 계속 사용한다**.

#### Legacy API 흐름 (변경 없음)

```python
# api/gql_legacy/image.py - AliasImage mutation (NO CHANGES)
class AliasImage(graphene.Mutation):
    async def mutate(cls, info, target: str, alias: str, architecture: str):
        # Continue using legacy canonical-based Action
        await AliasImageAction(
            image_canonical=target,
            architecture=architecture,
            alias=alias,
        ).execute(ctx)
```

**Legacy API 흐름 (변경 없음):**

```
Legacy API Handler (canonical input)
  → Legacy Action (canonical)
  → Repository (canonical lookup)
```

| Legacy API 입력 | Legacy Action 호출 |
|------------------|-------------------|
| `target: str` (canonical) | `AliasImageAction(image_canonical, architecture, alias)` |
| `references: [str]` | `PreloadImageAction(references)` |
| `image_canonical: str` | `ClearImageCustomResourceLimitAction(image_canonical, architecture)` |

### New API: ById Action 사용 (gql_relay, BEP-1038)

새 GraphQL API(gql_relay)는 **새 ById Action 을 직접 사용한다**.

#### New API 의 DataLoader 패턴

다른 도메인의 기존 DataLoader 패턴을 따른다.

```python
# api/gql/data_loader/image/loader.py
async def load_images_by_ids(
    processor: ImageProcessors,
    image_ids: Sequence[uuid.UUID],
) -> list[Optional[ImageData]]:
    """Batch load images by their IDs."""
    if not image_ids:
        return []

    querier = BatchQuerier(
        pagination=OffsetPagination(limit=len(image_ids)),
        conditions=[ImageConditions.by_ids(image_ids)],
    )

    action_result = await processor.search_images.wait_for_complete(
        SearchImagesAction(querier=querier)
    )

    image_map = {image.id: image for image in action_result.data}
    return [image_map.get(image_id) for image_id in image_ids]
```

```python
# api/gql/data_loader/data_loaders.py
class DataLoaders:
    @cached_property
    def image_loader(self) -> DataLoader[uuid.UUID, Optional[ImageData]]:
        return DataLoader(load_fn=partial(load_images_by_ids, self._processors.image))
```

#### New API handler 에서의 사용

```python
# api/gql_relay/image.py - AliasImageById mutation (NEW)
class AliasImageById(relay.Mutation):
    async def mutate(cls, info, image_id: uuid.UUID, alias: str):
        # Directly use ById Action - no conversion needed
        await AliasImageByIdAction(image_id=image_id, alias=alias).execute(ctx)
```

**New API 흐름:**

```
New API Handler (image_id input)
  → ById Action (image_id)
  → Repository (image_id lookup)
  → Cache (image_id key)
```

| New API 입력 | ById Action 호출 |
|---------------|-----------------|
| `image_id: UUID` | `AliasImageByIdAction(image_id, alias)` |
| `image_ids: [UUID]` | `PreloadImageByIdAction(image_ids)` |
| `image_id: UUID` | `ClearImageCustomResourceLimitByIdAction(image_id)` |

### New API (BEP-1038 범위)

ID 기반 새 GraphQL API 는 [BEP-1038](BEP-1038-image-v2-gql-implementation.md)에서 설계한다.
새 API 는 image_id 를 직접 받으므로 Action 을 호출하기 전에 변환이 필요 없다.

### service, Action 계층 이관

**legacy Action 을 그대로 두고 새 `ById` Action 을 생성한다:**

| Legacy Action (유지) | 새 ById Action |
|---------------------|-----------------|
| `AliasImageAction(image_canonical, architecture, alias)` | `AliasImageByIdAction(image_id, alias)` |
| `GetImagesAction(image_canonicals)` | `GetImagesByIdsAction(image_ids)` |
| `ClearImageCustomResourceLimitAction(image_canonical, architecture)` | `ClearImageCustomResourceLimitByIdAction(image_id)` |
| `PreloadImageAction(references)` | `PreloadImageByIdAction(image_ids)` |
| `UnloadImageAction(references)` | `UnloadImageByIdAction(image_ids)` |
| `RescanImagesAction(registry)` | `RescanImagesByIdAction(image_ids)` |
| `SetImageResourceLimitAction(image_canonical, architecture, ...)` | `SetImageResourceLimitByIdAction(image_id, ...)` |

**이관 전략:**

1. **새 ById Action 생성**: canonical 대신 `image_id` 를 받는 Action 을 새로 생성한다
2. **legacy Action 유지**: canonical 기반 기존 Action 은 legacy API 하위 호환을 위해 남긴다
3. **새 API 는 ById Action 사용**: BEP-1038 의 새 GraphQL schema 는 ById Action 을 직접 호출한다
4. **legacy API 는 legacy Action 유지**: gql_legacy handler 는 변경하지 않는다
5. **이후 deprecated 표기**: legacy API 를 제거하는 3단계에서 legacy Action 을 deprecated 로 표기한다

```python
# ai/backend/manager/services/image/actions/alias_image.py

# Legacy Action - unchanged
@dataclass
class AliasImageAction:
    """Legacy: Operates on canonical basis"""
    image_canonical: str
    architecture: str
    alias: str

    async def execute(self, ctx: ImageServiceContext) -> None:
        await ctx.image_repository.create_alias_by_canonical(
            self.image_canonical, self.architecture, self.alias
        )


# New ById Action
@dataclass
class AliasImageByIdAction:
    """New: Operates on image_id basis"""
    image_id: ImageID
    alias: str

    async def execute(self, ctx: ImageServiceContext) -> None:
        await ctx.image_repository.create_alias(self.image_id, self.alias)
```

```python
# ai/backend/manager/services/image/actions/get_images.py

# Legacy Action - unchanged
@dataclass
class GetImagesAction:
    image_canonicals: list[ImageCanonical]
    load_installed_agents: bool = False
    ...


# New ById Action
@dataclass
class GetImagesByIdsAction:
    image_ids: list[ImageID]
    load_installed_agents: bool = False

    async def execute(self, ctx: ImageServiceContext) -> list[ImageWithAgentInstallStatus]:
        return await ctx.image_repository.get_images_by_ids(
            self.image_ids,
            load_installed_agents=self.load_installed_agents,
        )
```

### Repository 계층 확장

```python
# ai/backend/manager/repositories/image/repository.py
class ImageRepository:
    async def get_images_by_ids(
        self,
        image_ids: list[ImageID],
        *,
        load_installed_agents: bool = False,
    ) -> list[ImageWithAgentInstallStatus]:
        ...

# ai/backend/manager/repositories/image/db_source/db_source.py
class ImageDBSource:
    async def query_images_by_ids(
        self,
        image_ids: list[ImageID],
    ) -> dict[ImageID, ImageDataWithDetails]:
        query = sa.select(ImageRow).where(ImageRow.id.in_(image_ids))
        ...
```

### 클라이언트 SDK, CLI (이 BEP 범위 밖)

클라이언트 SDK 와 CLI 확장은 **3단계인 API 이관**에서 다룬다.
이 BEP 는 **서버 내부 로직 이관**만 다룬다.

```
┌───────────────────────────────────────────────────────────────────────┐
│                          Scope Division                               │
├───────────────────────────────────────────────────────────────────────┤
│  BEP-1039 (this doc)    │  BEP-1038             │  Future (Stage 3)   │
│  ─────────────────────  │  ──────────────────   │  ─────────────────  │
│  ✓ Add ById Actions     │  ✓ New GQL schema     │  ✓ Client SDK ext.  │
│  ✓ Repository Layer     │  ✓ gql_relay impl.    │  ✓ CLI extension    │
│  ✓ Cache Layer          │                       │  ✓ REST API ext.    │
│  ✓ DataLoader addition  │                       │  ✓ Legacy deprecate │
└───────────────────────────────────────────────────────────────────────┘
```

## 이관과 호환

### 하위 호환

1. **외부 API 변경 없음**: 기존 GraphQL, REST API 는 모두 같게 동작한다
2. **추가만 한다**: 새 ById Action 을 추가하고 legacy Action 은 그대로 둔다
3. **사용자에게 투명하다**: legacy API 는 변경 없이 계속 동작한다
4. **병행 운영**: 3단계에서 deprecated 로 표기되기 전까지 legacy Action 과 ById Action 이 함께 존재한다

### 캐시 이관

Valkey 캐시 키 전환:

| 항목 | 이전 | 이후 |
|------|--------|-------|
| 캐시 키 | `image:{canonical}` | `image:{image_id}` |
| 읽기 | 둘 다 지원 | ID 키 우선 |
| 쓰기 | - | ID 키만 |

**전환 기간:**
- 새 쓰기는 ID 기반 키만 사용한다
- 기존 canonical 키는 TTL 만료까지 읽기에 지원한다
- 캐시가 자연스럽게 갱신되면서 점진적으로 전환한다

## 구현 계획

이 BEP 는 **service 계층 이관**을 다루고, API 확장은 BEP-1038 에서 진행한다.

### 1단계: Repository 계층

1. **DB source 확장**
   - `ImageDBSource.query_images_by_ids()` 구현
   - `ImageDBSource.query_images_by_canonicals()` 구현 (canonical 과 arch 조합 조회)

2. **Repository 확장**
   - `ImageRepository.get_images_by_ids()` 구현
   - `ImageConditions.by_ids()`, `ImageConditions.by_canonicals()` 조건 추가

3. **캐시 키 통일**
   - `ValkeyImageClient` 의 모든 메서드를 ImageID 키 기준으로 통일한다
   - legacy canonical 키는 읽기 전용으로 남긴다 (이관 기간)

### 2단계: DataLoader 추가 (새 API 용)

1. **ImageDataLoader 구현**
   - `load_images_by_ids()`: 새 API 의 ID 기반 batch load

2. **DataLoaders 등록**
   - `DataLoaders.image_loader` 추가: gql_relay(새 API) 용

3. **SearchImagesAction 구현, 확장**
   - `BatchQuerier` 지원
   - `ImageConditions` 기반 조회

### 3단계: Action 계층에 ById Action 생성

1. **새 ById Action 생성**
   - `AliasImageByIdAction(image_id, alias)` 생성: ID 기반 별칭 생성
   - `GetImagesByIdsAction(image_ids)` 생성: ID 기반 이미지 조회
   - `PreloadImageByIdAction(image_ids)` 생성: ID 기반 이미지 preload
   - `UnloadImageByIdAction(image_ids)` 생성: ID 기반 이미지 unload
   - `ClearImageCustomResourceLimitByIdAction(image_id)` 생성: ID 기반 자원 한도 해제
   - `RescanImagesByIdAction(image_ids)` 생성: ID 기반 이미지 재스캔
   - `SetImageResourceLimitByIdAction(image_id, ...)` 생성: ID 기반 자원 한도 설정

2. **기존 legacy Action 유지**
   - `AliasImageAction`: legacy API 용으로 canonical 기반을 유지한다
   - `GetImagesAction`: legacy API 용으로 canonical 기반을 유지한다
   - `PreloadImageAction`: legacy API 용으로 reference 기반을 유지한다
   - `UnloadImageAction`: legacy API 용으로 reference 기반을 유지한다
   - `ClearImageCustomResourceLimitAction`: legacy API 용으로 canonical 기반을 유지한다
   - `RescanImagesAction`: legacy API 용으로 registry 기반을 유지한다
   - `SetImageResourceLimitAction`: legacy API 용으로 canonical 기반을 유지한다

3. **legacy Action 에 이후 deprecated 표기**
   - legacy Action 에 deprecation 안내를 추가한다
   - ById 버전으로 옮기는 경로를 적는다

### 4단계: API handler 분리

1. **gql_legacy handler: 변경 필요 없음**
   - 기존 legacy Action(canonical 기반)을 계속 사용한다
   - 기존 동작을 변경 없이 유지한다
   - legacy API 에는 DataLoader 변환이 필요 없다

2. **새 gql_relay handler (BEP-1038)**
   - 새 ById Action 을 직접 사용한다
   - 클라이언트에서 image_id 를 받아 ById Action 에 바로 전달한다
   - canonical 에서 image_id 로 변환하는 단계가 필요 없다

3. **세션 생성 로직**
   - legacy 세션 생성 API 는 기존 canonical 기반 흐름을 유지한다
   - 새 세션 생성 API 를 추가하면 ById Action 을 사용한다

### 5단계: 테스트

1. **단위 테스트**
   - DataLoader 테스트
   - ID 기반 Action 테스트
   - Repository 메서드 테스트

2. **통합 테스트**
   - 기존 GraphQL API 가 같게 동작하는지 검증한다
   - 세션 생성 흐름 테스트

3. **하위 호환 테스트**
   - canonical 기반 기존 API 동작을 모두 검증한다

### 6단계: Agent protocol (선택, 이후)

1. **Agent 와 Manager 통신**
   - 이미지 식별에 ID 를 사용한다
   - Agent 는 필요할 때 canonical 로 변환한다 (Docker 동작용)

### 후속 작업 (별도 BEP)

**2단계: BEP-1038 (ImageV2 schema 추가)**
- 새 GraphQL schema 설계 (gql_relay 기반)
- ID 기반 Query, Mutation 구현
- 기존 gql_legacy 와 병행

**3단계: API 이관 (이후 BEP)**
- 클라이언트 SDK 확장
- CLI 확장
- REST API 확장
- canonical 기반 기존 API deprecated 표기

## 관련 BEP 와 의존성

### 3단계 이관 구조

| 단계 | BEP | 제목 | 범위 | 상태 |
|-------|-----|-------|-------|--------|
| 1 | **1039 (이 문서)** | service 로직 이관 | Action, Repository, 캐시 | Draft |
| 2 | 1038 | ImageV2 GQL schema 추가 | 새 GraphQL schema | Draft |
| 3 | (이후) | API 이관 | SDK, CLI, REST, deprecated 표기 | - |

### 의존성

```
BEP-1039 ──────→ BEP-1038 ──────→ (Future API Migration)
Service logic     New schema        Client migration
(internal)        (API addition)    (deprecate legacy API)
```

### 역할 분담

| 항목 | BEP-1039 | BEP-1038 | 이후 |
|------|----------|----------|--------|
| ById Action | ✓ 추가 | - | - |
| Legacy Action | 변경 없이 유지 | - | ✓ deprecated 표기 |
| Repository | ✓ ID 메서드 추가 | - | - |
| 캐시 | ✓ ID 키 추가 | - | - |
| GraphQL schema | - | ✓ 추가 | - |
| 클라이언트 SDK | - | - | ✓ 확장 |
| CLI | - | - | ✓ 확장 |
| Legacy API deprecated 표기 | - | - | ✓ 처리 |

## 참고

- [BEP-1010: New GQL](BEP-1010-new-gql.md)
- [BEP-1038: ImageV2 GQL Implementation](BEP-1038-image-v2-gql-implementation.md) (Stage 2: New schema addition)
