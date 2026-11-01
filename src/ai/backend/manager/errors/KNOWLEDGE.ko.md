# Manager errors: 배경

> 규칙은 같은 디렉터리의 `AGENTS.md` 에 있다.

## 이 패키지가 있는 이유

도메인 에러는 공개 계약이다. manager 밖으로 나가는 모든 실패는 기계가 읽는 code 와 RFC-7807 body 를 가지며, client 는 메시지를 해석하는 대신 code 로 분기한다. 이 패키지는 그 계약을 도메인마다 한 곳에 두는 역할을 맡는다.

## code triple 의 형식 제약은 하나다

- `ErrorCode` 는 `(domain, operation, error_detail)` 이고 `domain_operation_detail` 로 렌더링되며 `_` 로 나누어 파싱한다. **enum 값에 underscore 를 두지 않는다**(복합어는 하이픈으로 잇는다).
- 중앙 code registry 는 없다. 유일성은 어디에서도 강제하지 않으며, 기계가 읽는 유일한 표면은 생성되는 OpenAPI 문서다.
- 새 에러를 정의하기 전에 `manager/errors/` 와 `common/exception.py`(구체 에러 약 40개를 담는다)를 모두 확인한다.

## code 와 HTTP status 는 독립된 축이다

- HTTP status 는 class 기반 aiohttp mixin(`web.HTTPNotFound` -> 404)에서만 온다. code 는 실패를 설명하고 status 를 설명하지 않는다.
- 그래서 구체 예외는 **정의 시점에 status mixin 을 상속해야 한다**. 정의하는 쪽은 그 예외가 언제 외부로 나가는지(HTTP 응답으로) 알 수 없고, mixin 이 없는 예외가 밖으로 나가면 의미 있는 status 대신 일반 500 이 된다.
- 도메인 base 에러(`RepositoryError` 와 나머지 8개)는 의도적으로 mixin 이 없다. base 에 status 를 두면 MRO 에서 서브클래스 자신의 mixin 보다 앞선다. 이들을 직접 raise 하지 않는다.
- GraphQL 은 status 를 버리고 code 문자열만 `extensions.code` 에 담는다. REST 는 `problem+json` 을 렌더링한다.
- `BackendAIError` 가 아닌 예외를 누출하는 handler 는 code 를 잃는다. middleware 가 이를 일반 code 로 강제 변환한다.

## 구체 에러를 상속해 재사용한다

- `ObjectNotFound` 는 `object_name` 으로 title 을 구성한다. row base 보다 먼저 생긴 도메인 not-found 에러는 그 title 을 위해 `EntityError` 나 `FieldError` 옆에 두 번째 base 로 유지한다.
- 한 row 종류를 지정하는 raise 지점은 그 종류의 not-found 에러를 raise 한다. 그런 에러가 없는 종류는 `EntityNotFoundError` / `FieldNotFoundError` 를 상속해 `__init__` 에서 타입을 묶고 `operation` 을 전달하는 에러를 하나 얻는다. `ObjectNotFound` 자체는 없는 대상이 row 가 아닐 때만 raise 한다(아래 표에 모아 두었다).
- 의미가 맞으면 `BackendAIError` 에서 새로 파생하는 대신 기존 구체 에러를 상속한다.

## row 타입이나 action operation 이 없어 `BackendAIError` 에 남는 에러

- 없는 `EntityType` 이나 `FieldType` 을 선언하면 첫 번째 경우가 다시 열린다.
- 두 번째 경우는 다시 열리지 않는다. entity 와 field base 는 `ActionOperationType` 을 받는데 인증은 그 값이 아니고 app 시작도 그 값이 아니다. 둘 다 멤버를 얻지 않는다. permission 과 audit 기록도 그 값을 지정해야 하기 때문이다.

| 에러 | 남는 이유 |
|---|---|
| `RoleAlreadyAssigned`, `RoleNotAssigned` | `user_roles` row 에 `EntityType` 이나 `FieldType` 이 없다 |
| `GroupMembershipNotFoundError` | `entity_memberships` edge 를 읽는데 그 id 는 `data/permission/id.py` 의 평범한 `NewType` 이고 `EntityType` 이 아니다 |
| `ArtifactAssociationDeletionError`, `ArtifactAssociationNotFoundError` | `association_artifacts_storages` row 에 `FieldType` 이 없다 |
| `ContainerRegistryGroupsAssociationNotFound` | `association_container_registries_groups` row 에 `FieldType` 이 없다 |
| `InvalidFieldPermission` | permission 항목과 entity share 모두에 요청된 field scope 를 검증하므로 어느 한 row 종류도 지정하지 않는다 |
| `VirtualEntityNotFound` | `data/entity/virtual_entity.py` 는 id 만 선언하고 `EntityType` 은 없다 |
| `NotEnoughPermission`, `InsufficientPrivilege`, `ContainerRegistryWebhookAuthorizationFailed`, `ImageAccessForbiddenError` | row 가 아니라 호출자에 대한 권한 거부다 |
| `InvalidCredentials`, `InvalidAuthParameters`, `AuthorizationFailed` | 주체가 정해지기 전에 자격 증명을 판정하므로 row 를 지정하지 않는다 |
| `InvalidClientIPConfig` | manager 자신의 client 주소 설정이고 row 가 아니다 |
| `PasswordExpired`, `LoginSessionExpiredError`, `LoginBlockedError`, `TooManyConcurrentLoginSessions` | row 는 지정하지만 실패한 것은 인증이고, `ErrorOperation.AUTH` 에는 대응하는 `ActionOperationType` 이 없다 |
| `DeploymentDefinitionFileReadError` | vfolder 안의 파일이고 어느 row 타입도 선언하지 않는다 |
| `NoUpdatesToApply` | 아무것도 변경하지 않은 modifier 이고, row 는 호출자가 수정하던 row 다 |
| `AppServiceStartFailed` | session 안에서 시작한 app 은 row 가 아니고 `ActionOperationType` 에 `start` 가 없다 |
| `AppProxyConnectionError`, `AppProxyResponseError` | `AGENTS.md` 표에서 App Proxy 는 system 도메인이다 |
| `NotificationProcessingFailure`, `NotificationTemplateRenderingFailure` | notification 을 렌더링해 전달하고 나오는 메시지는 row 가 아니다. 타입이 있는 것은 notification 테이블 둘뿐이다 |
| `InvalidSecretKeyMaterial`, `SecretEncryptionMisconfigured` | 설정된 암호화 key 와 key provider 이고, 저장된 secret 을 읽어 접근하는 값이 아니다 |
| `ExportReportNotFound`, `InvalidExportFieldKeys` | report 는 코드에 선언된 registry 의 `ReportDef` 이고 row 가 아니며, 그 field key 도 마찬가지다 |
| `RetentionCategoryNotSupportedError` | cleanup 이 연결되지 않은 `RetentionCategory` 이고, row 가 아니라 이 build 의 공백이다 |
| `QuotaScopeNotFoundError`, `StorageProxyNotFound` | quota scope 와 storage proxy 는 row 종류를 선언하지 않는다 |
| 네 개의 `Dotfile*` 에러 | dotfile 경로와 엔티티별 limit 이 이 에러를 사용하고, 사용자는 기본 msgpack collection 을 편집하며 domain 과 project 는 msgpack column 을 유지한다 |
| `VFolderBadRequest`, `VFolderOperationFailed`, `VFolderCreationFailure` | row 가 아니라 storage proxy 호출을 보고하고 `generic` operation 아래에 있다 |
| `StorageProxyConnectionError`, `StorageProxyTimeoutError`, `UnexpectedStorageProxyResponseError` | 외부 호출 자체이고, `request` 에는 대응하는 `ActionOperationType` 이 없다 |
| `VFolderPermissionError`, `VFolderInvalidParameter`, `InsufficientStoragePermission` | 호출자에 대한 권한 거부이거나 row 에 이르기 전에 거부한 parameter 다 |
| `ModelCardParseError` | 파싱되지 않는 model-definition 파일이고 model card row 가 생기기 전이다 |
| `VFolderFilterStatusNotAvailable` | status-set alias 가 상수 map 에 항목을 지정하지 않는다. row-status 쪽은 `VFolderFilterStatusFailed` 다 |
| `UnsupportedStorageTypeError`, `ObjectStorageOperationNotSupported` | 요청한 storage 타입이거나, 그런 operation 을 제공하지 않는 설정된 타입이다 |
| `AppNotFound` | session 의 `service_ports` 에 없는 app 이고 row 가 아니라 값이다 |
| `UnresolvableResourceGroup` | 어떤 project 도 해석되지 않아 어느 것도 지정하지 않고 `access` 를 보고한다 |
| `AgentNotAllocated` | 아직 agent 가 배정되지 않은 kernel 이고, `access` 에는 대응하는 `ActionOperationType` 이 없다 |
| `InvalidUserUpdateMode`, `InvalidPresetQuery` | 요청 자체의 mode 값이거나 id 도 name 도 지정하지 않는 query 다 |
| `NoCurrentTaskContext`, `DatabaseConnectionUnavailable`, `ConfigurationLoadFailed`, `DataTransformationFailed`, `DBOperationFailed` | asyncio context, connection, 설정 로드, database 호출 자체다 |
| `BackendAgentError`, `KernelExecutionFailed`, `InvalidStreamMode` | `access` 나 `execute` 를 보고하고, 둘 다 대응하는 `ActionOperationType` 이 없다 |
| `AgentConnectionUnavailable` | agent 에 접근하는 일이고 같은 `access` 아래다 |
| `InvalidSessionId`, `InvalidKernelConfig`, `IncompleteSessionSpec` | row 에 이르기 전에 요청을 거부한다. `IncompleteSessionSpec` 은 `BackendAISchema.build_validation_error` override 셋 중 하나이고 `BackendAIError` 를 반환하도록 선언된 hook 이다 |
| 세 개의 `IdleCheckerAssignment*` 에러 | assignment row 의 id 가 `NewType` 이고 `EntityType` 이 없다 |
| `IdlePolicyNotFound` | idle-policy row 타입이 없고, row 가 아니라 없는 설정 값을 위해 raise 한다 |
| `QuotaExceeded` | resource-policy 한도에 도달한 것이지 한 row 의 상태가 아니다 |
| `ConflictingSessionRescheduleNotSupported` | 구현되지 않은 cleanup policy 이고 agent row 의 상태가 아니다 |
| `InvalidArtifactRegistryTypeError` | raise 지점 넷 중 셋이 event 에서 registry 타입을 읽어 row 를 지정하지 않는다 |
| `ArtifactScanLimitExceededError` | scan 요청의 `limit` 을 row 를 지정하기 전에 제한한다 |
| `ArtifactImportDelegationError` | 반환된 두 목록의 길이가 다르다고 보고한다 |
| `ArtifactDeletionError`, `RemoteReservoirArtifactImportError`, `ReservoirConnectionError`, `RemoteReservoirScanError` | storage proxy 나 remote reservoir 호출이 실패했다고 보고한다 |
| `ObjectNotFound` | row 종류를 `object_name` 문자열로만 지정하므로 대응할 타입이 없다 |
| `clients/container_registry/harbor.py` 에서 raise 하는 `ObjectNotFound` | Harbor quota 이고 registry 자신의 객체다 |
| `services/resource_group/service.py` 에서 raise 하는 `ObjectNotFound` | manager 가 없이 시작된 App Proxy client pool 이다 |
| `services/auth/service.py` 에서 raise 하는 `ObjectNotFound` | "그런 project 가 없거나 멤버가 아니다"를 두 경우에 일부러 같은 응답으로 주므로 row 를 지정하지 않는다 |
| `api/gql_legacy/base.py` `extract_object_uuid` 에서 raise 하는 `ObjectNotFound` | row 종류를 호출자에게서 문자열 인자로 받으므로 helper 자신은 row 를 지정하지 않는다 |
| `URLNotFound`, `MethodNotAllowed`, `ServerFrozen`, `NotImplementedAPI`, `InvalidAPIParameters`, `InvalidGraphQLParameters`, `InvalidCursor` | 경로, method, parameter, cursor 같은 요청이고 row 에 이르기 전에 거부한다 |
| `RateLimitExceeded` | 호출자가 얼마나 자주 요청하는지이고 row 가 아니다 |
| `GenericBadRequest` | 요청 자체(지원하지 않는 API version, 알 수 없는 scheduler operation, 빠뜨린 parameter)이거나 이미 있는 Harbor quota 다 |
| `GenericForbidden` | 모든 지점이 호출자를 거부하고("only authorized requests", "not the account owner") row 가 아니다 |
| `Forbidden` | 모든 지점이 vfolder 에 대한 것이지만 `ErrorOperation.ACCESS` 를 보고하고 여기에는 대응하는 `ActionOperationType` 이 없으며, WebUI 가 `vfolder_access_forbidden` 으로 분기한다 |
| `RejectedByHook` | plugin hook 의 응답이고, `AGENTS.md` 표에서 `plugin` 은 system 도메인이다 |
| `InternalServerError`, `ServerMisconfiguredError`, `ServiceUnavailable` | manager 자신이다 |
| `RepositoryError`, `UpsertEmptyResultError`, `UnsupportedCompositePrimaryKeyError`, `EmptyOperationScopeError`, `AmbiguousEntityKeyError` | 제네릭 ops 가 만나는 schema 나 invariant 결함이다. 유일하지 않은 key, composite primary key, 빈 scope, row 를 반환하지 않은 upsert. row 종류는 조회 시점에 알 수 있지만 실패한 것은 key 다 |
| `RepositoryIntegrityError` 와 그 다섯 SQLSTATE 종류 | `IntegrityErrorCheck` 가 `violation_type` 으로 대응하는 값이고, row 를 향하는 에러는 그 검사의 `error` 다 |
| `InvalidBgtaskId` | `bgtask` 에 `EntityType` 이나 `FieldType` 이 없다. `AGENTS.md` 표에서 system 도메인이다 |

## legacy 이웃은 다른 종류다

- `manager/exceptions.py` 는 HTTP 가 아닌 내부 배관(`AgentError`, `RPCError`, kernel `status_data` TypedDict)이고 도메인 에러가 아니다.
- 이름 충돌을 주의한다. 그 파일의 `ErrorDetail` TypedDict 는 `common/exception.py` 의 `ErrorDetail` enum 과 무관하다.
