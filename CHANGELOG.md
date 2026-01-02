Changes
=======

<!--
    You should *NOT* be adding new change log entries to this file, this
    file is managed by towncrier. You *may* edit previous change logs to
    fix problems like typo corrections or such.

    To add a new change log entry, please refer
    https://pip.pypa.io/en/latest/development/contributing/#news-entries

    We named the news folder "changes".

    WARNING: Don't drop the last line!
-->

<!-- towncrier release notes start -->

## 25.19.0 (2025-12-31)

### Features

#### RBAC System Data Migration
Implemented the service and repository layers for the Role-Based Access Control (RBAC) system and migrated existing entities to the RBAC database. RBAC data migration has been completed for entities including Model Deployment, Artifact Registry, Artifact, App Config, and Notification. (Actual permission enforcement is planned for future releases)

* Implement RBAC service and repository layer ([#7125](https://github.com/lablup/backend.ai/issues/7125))
* Implement RBAC DTOs and custom exceptions including request/response models, path parameters, and error handling ([#7361](https://github.com/lablup/backend.ai/issues/7361))
* Add RBAC API adapters for role management operations ([#7362](https://github.com/lablup/backend.ai/issues/7362))
* Add RBAC REST API endpoints for role management, role assignment, and querying assigned users ([#7363](https://github.com/lablup/backend.ai/issues/7363))
* Migrate Model Deployment data to RBAC database - add MODEL_DEPLOYMENT entity type and associate endpoints with user scopes based on creator ([#7619](https://github.com/lablup/backend.ai/issues/7619))
* Migrate Artifact Registry entities to RBAC database ([#7571](https://github.com/lablup/backend.ai/issues/7571))
* Add ARTIFACT entity type to RBAC system and migrate existing artifact data to RBAC database ([#7574](https://github.com/lablup/backend.ai/issues/7574))
* Migrate App Config entities to RBAC database ([#7583](https://github.com/lablup/backend.ai/issues/7583))
* Migrate Notification entities (channels and rules) to RBAC database ([#7584](https://github.com/lablup/backend.ai/issues/7584))

#### Repository Pattern Standardization
Introduced standardized patterns including Creator, Updater, Purger, and Querier to the repository layer, establishing a foundation for consistent application across all GraphQL APIs. Scheduling history data models were also newly added.

* Add scheduling history data models and ORM tables ([#7260](https://github.com/lablup/backend.ai/issues/7260))
* Add scheduling history repository with db_source layer ([#7265](https://github.com/lablup/backend.ai/issues/7265))
* Add Purger pattern for bulk deletion in repository layer ([#7274](https://github.com/lablup/backend.ai/issues/7274))
* Add Creator, Updater, Upserter patterns to repository layer ([#7279](https://github.com/lablup/backend.ai/issues/7279))
* Add execute_updater and execute_batch_updater functions ([#7280](https://github.com/lablup/backend.ai/issues/7280))
* Split Purger and Querier into single/batch patterns ([#7283](https://github.com/lablup/backend.ai/issues/7283))

#### Model Deployment Data Model Extension
Added database schemas to support version management, auto-scaling, and deployment policies for Model Deployment. (API and feature implementation is planned for future releases)

* Implement DeploymentRevisionRow model and repository ([#7396](https://github.com/lablup/backend.ai/issues/7396))
* Implement DeploymentAutoScalingPolicyRow model and repository ([#7410](https://github.com/lablup/backend.ai/issues/7410))
* Implement DeploymentPolicyRow for deployment strategy management ([#7413](https://github.com/lablup/backend.ai/issues/7413))
* Add DEPLOYING state and revision_history_limit to EndpointRow ([#7414](https://github.com/lablup/backend.ai/issues/7414))
* Add revision and traffic_status to RoutingRow ([#7427](https://github.com/lablup/backend.ai/issues/7427))
* Add DeploymentPolicy GraphQL API ([#7479](https://github.com/lablup/backend.ai/issues/7479))
* Add activateDeploymentRevision GQL mutation ([#7494](https://github.com/lablup/backend.ai/issues/7494))
* Add Route Traffic Control GQL API ([#7546](https://github.com/lablup/backend.ai/issues/7546))
* Add Deployment REST API endpoints with DTOs ([#7547](https://github.com/lablup/backend.ai/issues/7547))
* Add Deployment SDK and CLI ([#7548](https://github.com/lablup/backend.ai/issues/7548))
* Refactor deployment module with Repository pattern and Creator pattern ([#7606](https://github.com/lablup/backend.ai/issues/7606))
* Fix autoscaling issue where deployments in ready state would not scale when their desired replica count differs from the number of routes ([#7254](https://github.com/lablup/backend.ai/issues/7254))

#### GraphQL DataLoader Extension
Added domain-specific GraphQL DataLoader classes and implemented Strawberry GraphQL DataLoaders for entities that previously lacked DataLoader support. Search actions utilizing BatchQuerier from the new repository pattern were also implemented.

* Add `DataLoaders` class for domain-specific GraphQL data loaders ([#7299](https://github.com/lablup/backend.ai/issues/7299))
* Implement `Notification` Strawberry GraphQL DataLoaders ([#7300](https://github.com/lablup/backend.ai/issues/7300))
* Implement `ScalingGroup` Strawberry GraphQL DataLoaders ([#7426](https://github.com/lablup/backend.ai/issues/7426))
* Implement `ObjectStorage` Strawberry GraphQL DataLoaders ([#7429](https://github.com/lablup/backend.ai/issues/7429))
* Implement `StorageNamespace` Strawberry GraphQL DataLoaders ([#7430](https://github.com/lablup/backend.ai/issues/7430))
* Implement `VFSStorage` Strawberry GraphQL DataLoaders ([#7434](https://github.com/lablup/backend.ai/issues/7434))
* Implement `HuggingFaceRegistry` Strawberry GraphQL DataLoaders ([#7437](https://github.com/lablup/backend.ai/issues/7437))
* Implement `ReservoirRegistry` Strawberry GraphQL DataLoaders ([#7439](https://github.com/lablup/backend.ai/issues/7439))
* Implement `ArtifactRegistry` Strawberry GraphQL DataLoaders ([#7440](https://github.com/lablup/backend.ai/issues/7440))
* Implement `Artifact` Strawberry GraphQL DataLoaders ([#7441](https://github.com/lablup/backend.ai/issues/7441))
* Implement `ArtifactRevision` Strawberry GraphQL DataLoaders ([#7443](https://github.com/lablup/backend.ai/issues/7443))
* Implement BatchQuerier-based `SearchAutoScalingRulesAction` for model deployment auto scaling rules ([#7389](https://github.com/lablup/backend.ai/issues/7389))
* Implement BatchQuerier-based `SearchArtifactRegistriesAction` for artifact registry search ([#7394](https://github.com/lablup/backend.ai/issues/7394))
* Implement BatchQuerier-based `SearchReservoirRegistriesAction` for artifact registry search ([#7398](https://github.com/lablup/backend.ai/issues/7398))
* Implement BatchQuerier-based `SearchHuggingFaceRegistriesAction` for artifact registry search ([#7399](https://github.com/lablup/backend.ai/issues/7399))
* Implement BatchQuerier-based `SearchObjectStoragesAction` for artifact storage search ([#7400](https://github.com/lablup/backend.ai/issues/7400))
* Implement BatchQuerier-based `SearchVFSStoragesAction` for artifact storage search ([#7401](https://github.com/lablup/backend.ai/issues/7401))
* Implement BatchQuerier-based `SearchStorageNamespaceAction` for artifact storage search ([#7402](https://github.com/lablup/backend.ai/issues/7402))

#### Storage and Plugins
Hammerspace storage backend integration and open-sourcing of accelerator plugins were completed.

* Add BaseHammerspaceVolume (hammerspace-base) and Hammerspace (hammerspace) integrations as storage volume backend options ([#6155](https://github.com/lablup/backend.ai/issues/6155))
* Open source accelerator plugins ([#6916](https://github.com/lablup/backend.ai/issues/6916))

#### Scaling Group Management
Implemented Scaling Group creation action with the Creator pattern.

* Implement `CreateScalingGroupAction` with the Creator pattern, and repository method ([#7510](https://github.com/lablup/backend.ai/issues/7510))

### Security Fixes
Security vulnerability fixes and hardening were applied.

* **CVE-2025-49652**: Change default signup status to inactive, preventing newly registered accounts from accessing system resources until an administrator explicitly activates them ([#7520](https://github.com/lablup/backend.ai/issues/7520))

### Improvements
Session management logic was separated into dedicated classes to improve code structure, and repository pattern standardization work was conducted. The action-processor pattern was also applied to container registry related APIs.

* Refactor artifact and artifact-revision pagination logic based on `BatchQuerier` ([#7083](https://github.com/lablup/backend.ai/issues/7083))
* Introduce action-processor pattern in container registry modification ([#7163](https://github.com/lablup/backend.ai/issues/7163))
* Explicitly raise error when operation fails in auth repository ([#7177](https://github.com/lablup/backend.ai/issues/7177))
* Optimize CLI startup time by deferring heavy imports ([#7218](https://github.com/lablup/backend.ai/issues/7218))
* Extract provisioning logic to SessionProvisioner ([#7255](https://github.com/lablup/backend.ai/issues/7255))
* Extract prepare/start logic to SessionLauncher ([#7256](https://github.com/lablup/backend.ai/issues/7256))
* Extract terminate logic to SessionTerminator ([#7257](https://github.com/lablup/backend.ai/issues/7257))
* Split repositories/base.py into subpackage ([#7275](https://github.com/lablup/backend.ai/issues/7275))
* Migrate Creator ABC to CreatorSpec pattern ([#7286](https://github.com/lablup/backend.ai/issues/7286))
* Migrate PartialModifier to Updater pattern ([#7314](https://github.com/lablup/backend.ai/issues/7314))
* Refactor RBAC repository, service, and action layers to use the standardized Creator/Updater/Purger pattern ([#7360](https://github.com/lablup/backend.ai/issues/7360))
* Add RBAC types and infrastructure for refactoring ([#7416](https://github.com/lablup/backend.ai/issues/7416))
* Integrate `CreateScalingGroup` action with existing GQL resolver ([#7518](https://github.com/lablup/backend.ai/issues/7518))
* Apply action-processor pattern in container registry deletion API ([#7559](https://github.com/lablup/backend.ai/issues/7559))
* Reorganize deployment GQL module with fetcher/resolver/types pattern ([#7615](https://github.com/lablup/backend.ai/issues/7615))
* Add pre-validation for user modification to prevent raw IntegrityError ([#7632](https://github.com/lablup/backend.ai/issues/7632))

### Fixes
Fixed issues including agent selection strategies not being applied in the scheduler, authentication-related bugs, and various API and data processing errors.

* Replace `redis-py` with `valkey-glide` client in CLI context ([#7164](https://github.com/lablup/backend.ai/issues/7164))
* Fix inconsistent GPU device mask evaluation by mapping device mask target device by its GPU UUID ([#7187](https://github.com/lablup/backend.ai/issues/7187))
* Fix `model-store` vfolder creation failing when requested with `READ_ONLY` permission ([#7397](https://github.com/lablup/backend.ai/issues/7397))
* Increase default time window size when querying container metric vector ranges to ensure RATE function calculations return valid results ([#7420](https://github.com/lablup/backend.ai/issues/7420))
* Allow duplicated session names across users, enforce the session name unique constraint only for active sessions belonging to the same user ([#7462](https://github.com/lablup/backend.ai/issues/7462))
* Include service labels in Prometheus service discovery response ([#7466](https://github.com/lablup/backend.ai/issues/7466))
* Fix misuse of strawberry Dataloader in Model Artifact service ([#7468](https://github.com/lablup/backend.ai/issues/7468))
* Fix artifact mutation not working due to wrong resolver import ([#7493](https://github.com/lablup/backend.ai/issues/7493))
* Fix credential lookup to use keypairs table join instead of user table's `main_access_key` column, resolving authentication failures for non-main keypairs ([#7533](https://github.com/lablup/backend.ai/issues/7533))
* Remove FK relationship rows (session, route, endpoint) when purging scaling group to prevent integrity errors ([#7582](https://github.com/lablup/backend.ai/issues/7582))
* Add detailed log for command execution failures in kernel ([#7591](https://github.com/lablup/backend.ai/issues/7591))
* Replace `getent group` with `getent passwd` to retrieve username from USER_ID in entrypoint.sh ([#7601](https://github.com/lablup/backend.ai/issues/7601))
* Fix agent selection strategies (DISPERSED, CONCENTRATED, ROUNDROBIN, LEGACY) not being applied. Previously, the scheduler always used CONCENTRATED mode regardless of configuration. Now each scaling group's configured strategy works as intended ([#7605](https://github.com/lablup/backend.ai/issues/7605))
* Return None instead of 0 for missing Redis fields in ValkeyScheduleClient ([#7614](https://github.com/lablup/backend.ai/issues/7614))
* Suppress spurious error logs from Valkey monitor during shutdown ([#7630](https://github.com/lablup/backend.ai/issues/7630))
* Fix `unified_config` incorrectly assigned as tuple in `ServiceConfigNode.load` ([#7635](https://github.com/lablup/backend.ai/issues/7635))
* Use 422 error code for scaling group session type rejection ([#7649](https://github.com/lablup/backend.ai/issues/7649))
* Fix `modify_keypair_resource_policy` ignores empty JSON for `total_resource_slots` ([#7658](https://github.com/lablup/backend.ai/issues/7658))

### Documentation Updates
Developer guidelines and security-related documentation were added.

* Add DB ORM Model Design Guidelines to README ([#7357](https://github.com/lablup/backend.ai/issues/7357))
* Add comprehensive network security documentation addressing compute node isolation requirements ([#7587](https://github.com/lablup/backend.ai/issues/7587))

### External Dependency Updates
GPU monitoring tools, container base images, and Redis client library were updated.

* Update all-smi binaries to v0.11.0 ([#6962](https://github.com/lablup/backend.ai/issues/6962))
* Upgrade krunner-extractor container image from Alpine 3.8 to Alpine 3.21 ([#7285](https://github.com/lablup/backend.ai/issues/7285))
* Update `redis-py` version to latest, and refactor `redis_helper` package's utility functions ([#7317](https://github.com/lablup/backend.ai/issues/7317))

### Miscellaneous
Code cleanup and development environment improvements were made.

* Relocate RBAC type definitions for better dependency management ([#7301](https://github.com/lablup/backend.ai/issues/7301))
* Remove deprecated Java kernel directory ([#7325](https://github.com/lablup/backend.ai/issues/7325))
* Add direct test execution to pre-commit hook ([#7327](https://github.com/lablup/backend.ai/issues/7327))
* Remove unused REPL in kernels ([#7358](https://github.com/lablup/backend.ai/issues/7358))

### Test Updates
Test structure improvements and refactoring to mocking-based unit tests were conducted. Test speed and readability were improved by using mocking instead of full app initialization.

* Rewrite `artifact` and `artifact_revision` service unit tests to use mocked repositories and separate DB integration tests to repository layer ([#7328](https://github.com/lablup/backend.ai/issues/7328))
* Refactor `NewUserGracePeriodChecker` test to use mocking instead of full app ([#7390](https://github.com/lablup/backend.ai/issues/7390))
* Refactor `NetworkTimeoutIdleChecker` test to use mocking instead of full app ([#7395](https://github.com/lablup/backend.ai/issues/7395))
* Refactor `SessionLifetimeChecker` test to use mocking instead of full app ([#7403](https://github.com/lablup/backend.ai/issues/7403))
* Refactor `UtilizationIdleChecker` test to use mocking instead of full app ([#7441](https://github.com/lablup/backend.ai/issues/7441))
* Refactor `bgtask` test to use mocking instead of full app ([#7444](https://github.com/lablup/backend.ai/issues/7444))
* Restructure tests into unit/component/integration directories ([#7579](https://github.com/lablup/backend.ai/issues/7579))
* Add unit test for ratelimit middleware ([#7594](https://github.com/lablup/backend.ai/issues/7594))


## 25.18.0 (2025-12-12)

### Features

#### Agent and Kernel Management
Enhanced kernel recovery and presence monitoring with new scratch directory-based storage for kernel data, eliminating the need for pickle files under the var path. Added bidirectional kernel presence synchronization between agents and manager for improved reliability.

* Implement Kernel data loader and writer that saves recovery data to the Kernel scratch directory ([#6975](https://github.com/lablup/backend.ai/issues/6975))
* Add kernel data adapter that migrates pickled Kernel registry to Kernel Scratch, removing the need to save Kernel data to pickled files under `var` path ([#7004](https://github.com/lablup/backend.ai/issues/7004))
* Add Scratch utils and data schema to serialize and validate data stored in scratch directories ([#6997](https://github.com/lablup/backend.ai/issues/6997))
* Add kernel presence status storage to valkey_client ([#6978](https://github.com/lablup/backend.ai/issues/6978))
* Add KernelPresenceObserver to Agent ([#6986](https://github.com/lablup/backend.ai/issues/6986))
* Add SweepStaleKernelsHandler for stale kernel cleanup ([#6988](https://github.com/lablup/backend.ai/issues/6988))
* Add scheduler handler for session and kernel cleanup ([#6994](https://github.com/lablup/backend.ai/issues/6994))
* Add bidirectional kernel presence synchronization ([#7139](https://github.com/lablup/backend.ai/issues/7139))

#### Scheduler and Resource Management
Integrated RecorderContext into the Sokovan scheduler and updated dry-run functionality to use Sokovan scheduler events. Added support for DGX Spark hardware platform.

* Add recorder package and result types for scheduler refactoring ([#6902](https://github.com/lablup/backend.ai/issues/6902))
* Integrate RecorderContext into ScheduleCoordinator ([#6905](https://github.com/lablup/backend.ai/issues/6905))
* Update dry_run to use Sokovan scheduler event ([#7119](https://github.com/lablup/backend.ai/issues/7119))
* Support for DGX Spark ([#6809](https://github.com/lablup/backend.ai/issues/6809))

#### GraphQL API and Pagination
Implemented comprehensive pagination support for scaling groups with proper cursor-based and offset pagination, including PageInfo calculation and default ordering.

* Add `ScalingGroup` layer service logic and implement pagination support ([#6985](https://github.com/lablup/backend.ai/issues/6985))
* Add `ScalingGroup` strawberry-based GQL type ([#6992](https://github.com/lablup/backend.ai/issues/6992))
* Add `project` filtering argument to the `scaling_groups` strawberry GQL resolver ([#6998](https://github.com/lablup/backend.ai/issues/6998))
* Implement proper PageInfo calculation in QueryPagination ([#7099](https://github.com/lablup/backend.ai/issues/7099))
* Implement proper cursor-based pagination in QueryPagination ([#7108](https://github.com/lablup/backend.ai/issues/7108))
* Add default architecture selection from ScalingGroup agents ([#7109](https://github.com/lablup/backend.ai/issues/7109))
* Apply default order for offset pagination when order_by is not provided ([#7137](https://github.com/lablup/backend.ai/issues/7137))
* Move build_querier to BaseGQLAdapter with dataclasses ([#7113](https://github.com/lablup/backend.ai/issues/7113))

#### Storage and Artifact Registry
Added Valkey client for artifact registry configuration sharing between manager and storage-proxy, and implemented artifact cleanup on storage-proxy bootstrap. Enhanced model support with definition override capability and deep merge support.

* Add valkey client for artifact registries configuration sharing between manager and storage-proxy ([#6950](https://github.com/lablup/backend.ai/issues/6950))
* Cleanup artifact files from temporary storages when the storage-proxy bootstraps ([#6914](https://github.com/lablup/backend.ai/issues/6914))
* Add `timeout` configuration argument to `StorageProxyHTTPClient` ([#7120](https://github.com/lablup/backend.ai/issues/7120))
* Introduce configurable client timeout settings for `StorageSessionManager` by request type ([#7168](https://github.com/lablup/backend.ai/issues/7168))
* Add model definition override feature with deep merge support ([#7204](https://github.com/lablup/backend.ai/issues/7204))
* Support OCP (OpenShift Container Platform) Registry ([#6464](https://github.com/lablup/backend.ai/issues/6464))

#### App Proxy and Routing
Replaced GlobalTimer with LeaderCron for improved distributed task scheduling and added route-level initial delay configuration for health checks.

* Add route-level initial delay to app proxy health check ([#6924](https://github.com/lablup/backend.ai/issues/6924))
* Replace GlobalTimer with LeaderCron in App Proxy ([#6927](https://github.com/lablup/backend.ai/issues/6927))
* Add a schema oneshot for the appproxy database ([#6899](https://github.com/lablup/backend.ai/issues/6899))

#### Infrastructure and Configuration
Enhanced Valkey/Redis connectivity with Sentinel master change detection and improved reconnection logic for consecutive exception handling. Added SSH directory auto-creation for connection setup.

* Add need_reconnect method to detect Sentinel master changes ([#7134](https://github.com/lablup/backend.ai/issues/7134))
* Enhance MonitoringValkeyClient reconnection logic for consecutive exception handling ([#6995](https://github.com/lablup/backend.ai/issues/6995))
* Create `~/.ssh` directory if not exist when creating ssh connection ([#7208](https://github.com/lablup/backend.ai/issues/7208))
* Make overlay network's linux interface name consistent (applicable for [Docker 28+](https://github.com/moby/moby/commit/6c3797923dcb082370a09f9381511da10120bd7b) only) ([#7094](https://github.com/lablup/backend.ai/issues/7094))

### Improvements

#### Resource Policy and Data Structure
Introduced source-based structure in resource policies, separating DB source from repository layers for better modularity and maintainability.

* Introduce source-based structure in user resource policy ([#6907](https://github.com/lablup/backend.ai/issues/6907))
* Introduce db source layer in keypair resource policy ([#7097](https://github.com/lablup/backend.ai/issues/7097))
* Since `AgentDataExtended` no longer uses the fields it additionally extended from `AgentData`, replace instances using `AgentDataExtended` with `AgentData` ([#7049](https://github.com/lablup/backend.ai/issues/7049))

#### Kernel Registry Recovery
Refactored Agent's kernel registry recovery by separating loader and writer components, improving maintainability and recovery reliability.

* Refactor Agent's kernel registry recovery by separating loader and writer ([#6958](https://github.com/lablup/backend.ai/issues/6958))
* Add `KernelRegistryType` alias and `KernelRecoveryData` type ([#6971](https://github.com/lablup/backend.ai/issues/6971))

#### Error Handling
Improved error reporting with explicit exceptions for Domain and Group operations.

* Explicitly raise error when Domain operation fails ([#7102](https://github.com/lablup/backend.ai/issues/7102))
* Explicitly raise error when Group operation fails ([#7101](https://github.com/lablup/backend.ai/issues/7101))

### Fixes

#### Session and Resource Management
* Fix `check_presets` API returning inflated remaining resources by excluding non-ALIVE agents from calculation ([#7238](https://github.com/lablup/backend.ai/issues/7238))
* Add missing lock IDs to handlers with short cycle preventing race conditions caused by concurrent execution between short and long cycles ([#7223](https://github.com/lablup/backend.ai/issues/7223))
* Remove unnecessary shmem pre-deduction from Memory cgroup ([#7222](https://github.com/lablup/backend.ai/issues/7222))
* Use asyncio.gather for concurrent session starts ([#7144](https://github.com/lablup/backend.ai/issues/7144))
* Fixed an error when domain admin validated quota scope access by using the `domain_name` key instead of `domain`, preventing errors for both user dictionaries and UserRow ORM objects and avoiding lazy-loading issues outside database sessions ([#7017](https://github.com/lablup/backend.ai/issues/7017))

#### Artifact and Model Management
* Remove the race condition between the `ModelImportDone` and `ModelVerifyDone` events so that the artifact download done notification always includes a valid `verification_result` ([#7077](https://github.com/lablup/backend.ai/issues/7077))
* Fix remote reservoir's `verification_result` is not propagated ([#7111](https://github.com/lablup/backend.ai/issues/7111))
* Include `verification_result` in reservoir registry sync and `ArtifactDownloadCompletedMessage` payload ([#7034](https://github.com/lablup/backend.ai/issues/7034))
* Move the entire directory after artifact import instead of copying files individually, and remove the model directory if it is empty ([#7115](https://github.com/lablup/backend.ai/issues/7115))
* Remove synchronous artifact metadata sync logic ([#6915](https://github.com/lablup/backend.ai/issues/6915))
* Add missing field in model health check ([#7082](https://github.com/lablup/backend.ai/issues/7082))
* Add initial_delay field to model_definition_iv trafaret validator ([#7001](https://github.com/lablup/backend.ai/issues/7001))
* Remove model definition YAML requirement for non-CUSTOM runtimes ([#6936](https://github.com/lablup/backend.ai/issues/6936))
* Fix huggingFace token not applied in `HuggingFaceFileDownloadStreamReader` ([#7227](https://github.com/lablup/backend.ai/issues/7227))
* Add missing `raise_for_status` for huggingface downloader ([#7233](https://github.com/lablup/backend.ai/issues/7233))

#### App Proxy and Routing
* Skip generating route info when kernel service port is none ([#7211](https://github.com/lablup/backend.ai/issues/7211))
* Include DEGRADED status in target statuses for RunningRouteHandler ([#7135](https://github.com/lablup/backend.ai/issues/7135))
* Update prometheus_address construction to exclude metrics path ([#7207](https://github.com/lablup/backend.ai/issues/7207))
* Disable HTML autoescaping in `NotificationCenter` request ([#7191](https://github.com/lablup/backend.ai/issues/7191))

#### Database and GraphQL
* Fixed SQLAlchemy session synchronization errors and foreign key constraint violations in group endpoint deletion by adding proper execution_options and reordering deletions ([#7132](https://github.com/lablup/backend.ai/issues/7132))
* Fix typo in Scaling Group GQL Objects (`ScalingGroupConnection`, `ScalingGroupEdge`) where 'g' was missing ([#6972](https://github.com/lablup/backend.ai/issues/6972))
* Remove useless `fallback_count_table` from the `execute_querier` ([#6976](https://github.com/lablup/backend.ai/issues/6976))
* `is_active` is not applied to `groups` GQL resolver when client role is `USER` ([#7116](https://github.com/lablup/backend.ai/issues/7116))

#### Agent and Kernel Registry
* Ensure agent-level kernel registry is synced with runtime-level global registry after pickle ([#6931](https://github.com/lablup/backend.ai/issues/6931))
* Add fallback for SlotName type conversion to avoid unexpected pydantic validation error caused due to version mismatch between Manager and Agent ([#6923](https://github.com/lablup/backend.ai/issues/6923))
* Read HTTP responses before connection closes in Agent Watcher APIs ([#7165](https://github.com/lablup/backend.ai/issues/7165))

#### Storage and Client
* Fix Pure Storage client to properly handle authentication tokens by correcting token storage that previously used context variables incorrectly, which could cause the client to lose access to authentication credentials ([#6913](https://github.com/lablup/backend.ai/issues/6913))

#### CLI and Utilities
* Fix service list CLI showing null image and missing URL ([#7006](https://github.com/lablup/backend.ai/issues/7006))
* Print a warning log when `ConnectionError` occurs to make it easy to identify the types of errors ([#6910](https://github.com/lablup/backend.ai/issues/6910))

### Security Improvements
Comprehensive security hardening across multiple components with improved exception handling and security best practices.

* Add tarfile.data_filter to prevent path traversal attacks ([#7035](https://github.com/lablup/backend.ai/issues/7035))
* Add security attributes to permit cookie in App Proxy responses ([#7038](https://github.com/lablup/backend.ai/issues/7038))
* Add usedforsecurity=False to hashlib MD5/SHA1 calls ([#7041](https://github.com/lablup/backend.ai/issues/7041))
* Apply try-with-resources pattern to prevent resource leak ([#7039](https://github.com/lablup/backend.ai/issues/7039))
* Replace assert statements with proper exceptions (Phase 1) ([#7043](https://github.com/lablup/backend.ai/issues/7043))
* Replace assert statements with proper exceptions (Phase 2) ([#7044](https://github.com/lablup/backend.ai/issues/7044))
* Replace assert statements with proper exceptions (Phase 3) ([#7056](https://github.com/lablup/backend.ai/issues/7056))
* Replace AgentError with BackendAIError-based exceptions ([#7058](https://github.com/lablup/backend.ai/issues/7058))
* Replace exceptions with BackendAIError-based exceptions in storage proxy ([#7060](https://github.com/lablup/backend.ai/issues/7060))
* Replace assert statements with BackendAIError exceptions in agent ([#7061](https://github.com/lablup/backend.ai/issues/7061))
* Replace assert statements with BackendAIError exceptions in web ([#7062](https://github.com/lablup/backend.ai/issues/7062))
* Replace assert statements with proper exceptions in AppProxy ([#7063](https://github.com/lablup/backend.ai/issues/7063))

### External Dependency Updates
* Fix pycares version to 4.11 because aiohttp does not support pycares 5.0, which introduced breaking changes ([#7231](https://github.com/lablup/backend.ai/issues/7231))

### Miscellaneous
* Bundle bssh as intrinsic binary in Backend.AI runner package ([#6452](https://github.com/lablup/backend.ai/issues/6452))


## 25.17.0 (2025-11-23)

### Features

#### Agent and Multi-Agent Support
Laid the groundwork for running multiple agent instances on a single host. This is an early-stage effort focusing on configuration structure and runtime architecture refactoring. Full resource isolation between agents is planned for future releases.

* Add support for array of tables syntax in config sample generator ([#6311](https://github.com/lablup/backend.ai/issues/6311))
* Add support for multiple agents in agent server config ([#6315](https://github.com/lablup/backend.ai/issues/6315))
* Update Agent server RPC functions to include agent ID for agent runtime with multiple agents ([#6320](https://github.com/lablup/backend.ai/issues/6320))
* Change agent config field names and serialization aliases to use internal-addr naming ([#6697](https://github.com/lablup/backend.ai/issues/6697))
* Add AgentEtcdClientView for clean handling of etcd clients for multi agents ([#6721](https://github.com/lablup/backend.ai/issues/6721))
* Add custom resource allocation in agent server config ([#6724](https://github.com/lablup/backend.ai/issues/6724))
* Extract agent common resources to AgentRuntime ([#6728](https://github.com/lablup/backend.ai/issues/6728))
* Move ownership of resources from agent to a separate component in agent runtime ([#6766](https://github.com/lablup/backend.ai/issues/6766))
* Add resource isolation options for multi-agent setup ([#6770](https://github.com/lablup/backend.ai/issues/6770))
* Store installed images information to Redis in Agent ([#6834](https://github.com/lablup/backend.ai/issues/6834))
* Implement pickle based Kernel registry recovery which can replace existing kernel registry load and save functions ([#6489](https://github.com/lablup/backend.ai/issues/6489))
* Add agent-id label for session Docker containers ([#6870](https://github.com/lablup/backend.ai/issues/6870))

#### Health Check and Dependency Verification
Added health check endpoints and dependency verification CLI commands across all Backend.AI components. Operators can now diagnose connectivity issues with external services (database, Redis, etcd) before and during runtime.

* Implement health check infrastructure for component monitoring ([#6732](https://github.com/lablup/backend.ai/issues/6732))
* Add health checker system for all components ([#6736](https://github.com/lablup/backend.ai/issues/6736))
* Add dependency management system for manager ([#6753](https://github.com/lablup/backend.ai/issues/6753))
* Add dependency verification system for web component ([#6757](https://github.com/lablup/backend.ai/issues/6757))
* Add dependency verification for storage proxy ([#6760](https://github.com/lablup/backend.ai/issues/6760))
* Add dependency verification for App Proxy Coordinator and Worker ([#6767](https://github.com/lablup/backend.ai/issues/6767))
* Add dependency verification CLI in agent ([#6775](https://github.com/lablup/backend.ai/issues/6775))
* Add dependency health checking infrastructure ([#6781](https://github.com/lablup/backend.ai/issues/6781))
* Integrate HealthProbe across all components with real connectivity checks ([#6836](https://github.com/lablup/backend.ai/issues/6836))

#### Artifact and Reservoir Registry
Enhanced artifact management with verification plugins, real-time download progress tracking via Redis, and support for gated HuggingFace models. Also enabled delegation-based imports when artifacts are unavailable in local reservoir registries.

* Implement `artifact_verifier` type plugin in storage-proxy ([#6258](https://github.com/lablup/backend.ai/issues/6258))
* Fix `limit`, `search` parameters not working in reservoir registry's `scan_artifact` API ([#6488](https://github.com/lablup/backend.ai/issues/6488))
* Separate DB source from artifact repository layers ([#6490](https://github.com/lablup/backend.ai/issues/6490))
* Re-import available artifacts only when necessary based on digest ([#6501](https://github.com/lablup/backend.ai/issues/6501))
* Add `extra` column to Artifact model to store gated information for `huggingface` models ([#6620](https://github.com/lablup/backend.ai/issues/6620))
* Collect artifact verification results to `artifact_revisions` table ([#6662](https://github.com/lablup/backend.ai/issues/6662))
* Track Artifact download progress through redis ([#6663](https://github.com/lablup/backend.ai/issues/6663))
* Create artifact download progress query REST API ([#6666](https://github.com/lablup/backend.ai/issues/6666))
* Extend reservoir registry artifact import API to perform import delegation when the artifact is not available in the remote reservoir ([#6672](https://github.com/lablup/backend.ai/issues/6672))
* Track Reservoir registry artifact download progress ([#6673](https://github.com/lablup/backend.ai/issues/6673))
* Add `metadata` field to artifact verifier interface ([#6676](https://github.com/lablup/backend.ai/issues/6676))
* Add missing `id`, `registry_id` fields to `ArtifactRegistry` GQL Node ([#6750](https://github.com/lablup/backend.ai/issues/6750))

#### Notification System
Introduced a notification center that allows administrators to configure webhook channels and define event-based notification rules. Included REST/GraphQL APIs for channel and rule management, along with CLI tools for validation and delivery testing.

* Implement notification system with channels, rules, and event processing ([#6635](https://github.com/lablup/backend.ai/issues/6635))
* Implement notification center with REST/GraphQL APIs for managing channels and rules ([#6653](https://github.com/lablup/backend.ai/issues/6653))
* Add notification validation API and notification CLI ([#6657](https://github.com/lablup/backend.ai/issues/6657))
* Add notification center with webhook channel support ([#6668](https://github.com/lablup/backend.ai/issues/6668))
* Implement notification message type system and validation APIs ([#6677](https://github.com/lablup/backend.ai/issues/6677))

#### Background Task Infrastructure
Began migrating background tasks to a retriable pattern with initial support for image operations and session commits. This is an ongoing effort, and further tasks will be migrated in subsequent releases.

* Add image purge/rescan background tasks and modernize task system ([#6597](https://github.com/lablup/backend.ai/issues/6597))
* Improve bgtask infrastructure with repository pattern and type adapters ([#6606](https://github.com/lablup/backend.ai/issues/6606))
* Migrate commit session to retriable background task pattern ([#6625](https://github.com/lablup/backend.ai/issues/6625))

#### Model Service and Routing
Introduced route health checking with a 3-state model (healthy/unhealthy/degraded) and automatic eviction for unhealthy endpoints. Also added Prometheus integration via service discovery for model service metrics collection.

* Add model service route synchronization to service discovery ([#6832](https://github.com/lablup/backend.ai/issues/6832))
* Add periodic service discovery sync for model service routes ([#6833](https://github.com/lablup/backend.ai/issues/6833))
* Implement 3-state route health check with configurable eviction ([#6839](https://github.com/lablup/backend.ai/issues/6839))
* Add missing and newly introduced fields to service field specifications ([#6714](https://github.com/lablup/backend.ai/issues/6714))

#### Session and Resource Management
Parallelized session termination for improved performance and added automatic cleanup for sessions associated with lost agents. Also introduced an async file deletion API for vfolders.

* Parallelize session termination and add lost agent cleanup ([#6826](https://github.com/lablup/backend.ai/issues/6826))
* Implement async file deletion API in vfolder ([#6861](https://github.com/lablup/backend.ai/issues/6861))

#### Infrastructure and Configuration
Added flexible bind/advertise address configuration for app-proxy components and restructured Valkey client by separating monitor and operation clients for better resource management.

* Add read committed transaction support in `ExtendedAsyncSAEngine`, enabling higher throughput for read-heavy workloads by reducing transaction isolation overhead ([#6665](https://github.com/lablup/backend.ai/issues/6665))
* Replace time() with Redis TIME command in ValkeyScheduleClient ([#6695](https://github.com/lablup/backend.ai/issues/6695))
* Support multiple Apollo Router endpoints with load balancing ([#6703](https://github.com/lablup/backend.ai/issues/6703))
* Support bind, advertised address configuration options for app-proxy coordinator and worker components ([#6631](https://github.com/lablup/backend.ai/issues/6631))
* Separate monitor and operation clients in Valkey client ([#6829](https://github.com/lablup/backend.ai/issues/6829))
* Ensure normal URLs are called even if the protocol is included in the host of `HostPortPair`, preventing network error in app-proxy communication ([#6813](https://github.com/lablup/backend.ai/issues/6813))
* delete-dev.sh now supports interactive confirmation and non-interactive -y/--yes flag ([#6815](https://github.com/lablup/backend.ai/issues/6815))

### Improvements
* Change Action Processor arguments to immutable types and made them contravariant to prevent memory leaks and improve type safety ([#6596](https://github.com/lablup/backend.ai/issues/6596))
* Introduce Source-based structure in `AuthRepository` decoupling database access for easier testing ([#6641](https://github.com/lablup/backend.ai/issues/6641))
* Make `error_code` method in `BackendAIError` as instance method making injection or modification of the error code from outside the class easier, improving flexibility when handling errors ([#6722](https://github.com/lablup/backend.ai/issues/6722))
* Move kernel registry ownership to agent runtime ([#6730](https://github.com/lablup/backend.ai/issues/6730))
* Use resources functions directly in AbstractAgent ([#6763](https://github.com/lablup/backend.ai/issues/6763))

### Fixes

#### Session and Resource Management
Fixed session data loading to prevent SQLAlchemy errors, corrected resource calculation to use kernel-level occupied slots, and added missing cache invalidation for resource presets.

* Eager load kernel when fetch session by its id preventing SQLAlchemy error when attempting to use relationships outside the db session context manager ([#6866](https://github.com/lablup/backend.ai/issues/6866))
* Use the kernel's occupied slots when calculating the agent's resources ([#6817](https://github.com/lablup/backend.ai/issues/6817))
* Add missing cache invalidation for resource preset ([#6852](https://github.com/lablup/backend.ai/issues/6852))

#### Artifact and Reservoir Registry
Resolved blocking behavior in delegation-based imports and improved timeout handling for reservoir download operations.

* Reservoir artifact import API response is blocking when using delegation ([#6683](https://github.com/lablup/backend.ai/issues/6683))
* Adjust reservoir download API client timeout and add proper connection termination handling ([#6627](https://github.com/lablup/backend.ai/issues/6627))
* Remove `DoPullReservoirRegistryEvent`, and the event handler ([#6680](https://github.com/lablup/backend.ai/issues/6680))

#### App Proxy and Routing
Added HTTP client connection pooling to prevent excessive socket creation, fixed redirect URL generation in auth flow, and added missing advertise_address in status responses.

* Apply http client pool in app proxy worker ([#6851](https://github.com/lablup/backend.ai/issues/6851))
* Fix app proxy to properly handle redirect parameter in HTTP protocol auth flow by appending the redirect path to the generated proxy URL ([#6686](https://github.com/lablup/backend.ai/issues/6686))
* Add missing advertise_address info in app proxy status response ([#6772](https://github.com/lablup/backend.ai/issues/6772))

#### Storage and Configuration
Improved error response handling in storage proxy client and corrected VAST cluster cache refresh behavior.

* Fix storage proxy client to handle non-JSON error responses instead of crashing on parse failures ([#6712](https://github.com/lablup/backend.ai/issues/6712))
* Refresh VAST cluster info cache rather than keep the cache alive forever ([#6428](https://github.com/lablup/backend.ai/issues/6428))

#### Model Service
Improved error visibility by returning actual error messages from Model Card resolver instead of generic strings. Also fixed auto-scaling behavior where metrics collection and rule comparison were not working correctly for framework-based scaling rules.

* Model Card resolver now returns the actual error message when it fails, instead of showing a generic "Unknown error" string ([#6702](https://github.com/lablup/backend.ai/issues/6702))
* Support service-definition.toml override with optional fields(image, arch, resource) ([#6751](https://github.com/lablup/backend.ai/issues/6751))
* Disallow dot('.') usage in model service name ([#6800](https://github.com/lablup/backend.ai/issues/6800))
* Fix auto-scaling functionality for inference services when using framework-based scaling rules. Metrics collection and rule comparison logic have been corrected to ensure proper scaling behavior ([#6801](https://github.com/lablup/backend.ai/issues/6801))

#### Agent and Image Management
Fixed Pydantic validation errors in mock plugins and SlotName initialization, and changed image sync to match by canonical name and architecture instead of digest for consistency across container drivers.

* Fix Pydantic validation error from incorrect `slot_type` type in mock plugin ([#6692](https://github.com/lablup/backend.ai/issues/6692))
* Make agent installed image sync to match by canonical name and architecture instead of digest, preventing digest change by container image driver ([#6838](https://github.com/lablup/backend.ai/issues/6838))
* Explicitly wrap slot key with `SlotName()` to prevent validation failure when initializing `AgentInfo` ([#6841](https://github.com/lablup/backend.ai/issues/6841))

#### Permission and Access Control
Corrected permission boundary issues for domain admin users.

* Fix domain admin users seeing vfolder hosts from projects they were not members of. They now only see hosts for projects they belong to ([#6694](https://github.com/lablup/backend.ai/issues/6694))

#### Other Fixes
Updated GPU allocation metrics to include all accelerator types (CUDA devices/shares, MIG, NPUs) and allowed zero values in DecimalType conversion.

* Update `gpu_allocated` legacy metric fields to consider all accelerator devices, including both `cuda.devices` and `cuda.shares`, but also MIG variants and other NPUs as well (Known issue: all resources visible to each user and group MUST use a consistent fraction mode) ([#2404](https://github.com/lablup/backend.ai/issues/2404))
* Allow zero values in DecimalType conversion ([#6783](https://github.com/lablup/backend.ai/issues/6783))

### Documentation Updates
* Add Entry Point, Event, and Background Task architecture documentation ([#6594](https://github.com/lablup/backend.ai/issues/6594))
* Document adapter and Querier patterns in API/GraphQL/Repository READMEs ([#6656](https://github.com/lablup/backend.ai/issues/6656))
* Document deployment revision generator in deployment README.md ([#6872](https://github.com/lablup/backend.ai/issues/6872))

### Miscellaneous
* Move `EndpointLifecycle` enum to a shared common package for improved reusability ([#6637](https://github.com/lablup/backend.ai/issues/6637))
* Add debug log when app proxy worker got server disconnected error making tracing and diagnosing unexpected disconnections easier ([#6735](https://github.com/lablup/backend.ai/issues/6735))


## 25.16.0 (2025-11-01)

### Features

#### Resilience Framework
* Add resilience framework with Policy interface and Resilience executor for composable fault-tolerance patterns ([#6203](https://github.com/lablup/backend.ai/issues/6203))
* Applied resilience framework to all Valkey clients with ContextVar-based operation tracking, replacing legacy decorators with composable policies ([#6205](https://github.com/lablup/backend.ai/issues/6205))
* Apply resilience framework (MetricPolicy + RetryPolicy with exponential backoff) to all manager repositories for improved observability and fault tolerance ([#6210](https://github.com/lablup/backend.ai/issues/6210))
* Apply Resilience framework to agent client with exponential backoff retry policy for improved reliability in agent RPC communications ([#6211](https://github.com/lablup/backend.ai/issues/6211))
* Apply Resilience framework to appproxy (wsproxy) client with exponential backoff retry policy for improved reliability in app proxy communications ([#6213](https://github.com/lablup/backend.ai/issues/6213))
* Apply Resilience framework to storage proxy client with exponential backoff retry policy for improved reliability in storage proxy communications ([#6214](https://github.com/lablup/backend.ai/issues/6214))

#### Artifact and Reservoir Registry
* Implement `delegate_import` GQL mutation to trigger remote reservoir registry import ([#6221](https://github.com/lablup/backend.ai/issues/6221))
* Implement periodic polling and synchronization for remote reservoir ([#6222](https://github.com/lablup/backend.ai/issues/6222))
* Introduce artifact import pipeline to enable customizable storage configuration for each stage ([#6223](https://github.com/lablup/backend.ai/issues/6223))
* Add `vfs_storages` DB table, and GQL model and mutations ([#6229](https://github.com/lablup/backend.ai/issues/6229))
* Support artifact download from the reservoir registry's `vfs_storage` ([#6236](https://github.com/lablup/backend.ai/issues/6236))

#### GraphQL and Real-time Updates
* Replace Apollo Router with Hive Router (MIT License) to enable GQL Subscription support in federated environments without licensing fees, and add GQL Subscription support in webserver and backend for real-time updates ([#6234](https://github.com/lablup/backend.ai/issues/6234))
* Add GraphQL subscription `schedulingEventsBySession` for real-time session scheduling events ([#6239](https://github.com/lablup/backend.ai/issues/6239))
* Add GraphQL subscription `backgroundTaskEvents` for real-time background task events ([#6243](https://github.com/lablup/backend.ai/issues/6243))
* Support project name filter when resolving user nodes ([#6298](https://github.com/lablup/backend.ai/issues/6298))

#### RBAC and Access Control
* Add Global scope to simplify access control management for superadmin and monitor users ([#6004](https://github.com/lablup/backend.ai/issues/6004))
* Add superadmin and monitor role fixtures and migrate existing admin and monitor data to RBAC DB ([#6006](https://github.com/lablup/backend.ai/issues/6006))

#### Session Scheduling
* Implement scaling group filtering with injectable rules for session scheduling. The new ScalingGroupFilter applies configurable filter rules (public/private access, session type support) to determine eligible scaling groups before session creation, replacing the previous validation-only approach. This enables more flexible and extensible scaling group selection logic. ([#6424](https://github.com/lablup/backend.ai/issues/6424))
* Remove redundant agent count validation for multi-node cluster sessions ([#6276](https://github.com/lablup/backend.ai/issues/6276))

#### Model Service and Runtime
* Add support for Modular MAX and SGLang runtime variants ([#6237](https://github.com/lablup/backend.ai/issues/6237))
* Implement API layer for model deployment with pagination and filtering support ([#6394](https://github.com/lablup/backend.ai/issues/6394))

#### Authentication
* Implement JWT authentication module for GraphQL Federation ([#6410](https://github.com/lablup/backend.ai/issues/6410))
* Apply JWT authentication to webserver and manager ([#6421](https://github.com/lablup/backend.ai/issues/6421))

#### Configuration Management
* Add domain-level app configuration GraphQL API ([#6295](https://github.com/lablup/backend.ai/issues/6295))
* Add domain-level app configuration support for frontend ([#6401](https://github.com/lablup/backend.ai/issues/6401))
* Add `allow-auto-quota-scope-creation` configuration option to control whether virtual folders can be created in quota scopes that don't yet exist. Administrators can now prevent automatic quota scope creation by disabling this option, requiring quota scopes to be explicitly created before use. ([#6263](https://github.com/lablup/backend.ai/issues/6263))
* Container commit timeout can now be customized through configuration settings ([#6346](https://github.com/lablup/backend.ai/issues/6346))

#### Web and Proxy
* Implement WebSocket connectionParams to HTTP headers conversion ([#6379](https://github.com/lablup/backend.ai/issues/6379))
* Add connection error handling to storage proxy client ([#6319](https://github.com/lablup/backend.ai/issues/6319))

#### Metrics and Monitoring
* Add error code labels to layer operation metrics ([#6322](https://github.com/lablup/backend.ai/issues/6322))

### Improvements
* Integrate Pydantic validators with Agent server configuration ([#6172](https://github.com/lablup/backend.ai/issues/6172))
* Introduce Service, Repository layer pattern in `Image` GQL Object resolvers ([#6238](https://github.com/lablup/backend.ai/issues/6238))
* Set Image ID as Redis key instead of Canonical when storing installed agents per image ([#6249](https://github.com/lablup/backend.ai/issues/6249))
* Introduce action-processor pattern to `Image` batch load resolvers for decoupling Redis and DB access in GQL API layer ([#6269](https://github.com/lablup/backend.ai/issues/6269))
* Remove unused agent life cycle event handler as it is replaced by `handle_agent_terminated` and `handle_agent_started` in `AgentEventHandler` ([#6299](https://github.com/lablup/backend.ai/issues/6299))
* Replace the use of the `raw_labels` field in the Image GQL object with the existing `labels` field ([#6309](https://github.com/lablup/backend.ai/issues/6309))
* Introduced separate DTOs for permission groups(`PermissionGroupExtendedData`, `PermissionGroupData`) to conditionally load relationship data and prevent lazy loading errors ([#6451](https://github.com/lablup/backend.ai/issues/6451))
* Add Kernel registry recovery abstract class for refactor Agent by detaching kernel registry load and save logic ([#6482](https://github.com/lablup/backend.ai/issues/6482))

### Fixes

#### Session Management
* Raise correct exception in `SessionTransitionData.main_kernel` ([#6202](https://github.com/lablup/backend.ai/issues/6202))
* Improve the performance of VFolder queries by optimizing group lookups, resulting in faster VFolder detail panel popups and quicker session creation page loading ([#6300](https://github.com/lablup/backend.ai/issues/6300))
* Session commits now fail immediately with a clear error when attempting to exceed quota limits. This improves user experience by providing faster feedback instead of attempting a commit that would ultimately fail ([#6304](https://github.com/lablup/backend.ai/issues/6304))
* Prevent re-terminating sessions already in terminal states ([#6353](https://github.com/lablup/backend.ai/issues/6353))
* Session type validation is now properly enforced when creating sessions within scaling groups ([#6354](https://github.com/lablup/backend.ai/issues/6354))
* Add missing `PRE_ENQUEUE_HOOK` and `POST_ENQUEUE_HOOK` call in Sokovan scheduler ([#6584](https://github.com/lablup/backend.ai/issues/6584))

#### Agent and Resource Management
* Align `occupied_slots` values between Agent summary and Agent type queries ([#6257](https://github.com/lablup/backend.ai/issues/6257))
* Decoupled agent batch loading resolvers that previously depended on the `from_row` function. ([#6280](https://github.com/lablup/backend.ai/issues/6280))
* Fix GQL agent_summary_list resolver ([#6389](https://github.com/lablup/backend.ai/issues/6389))

#### Storage and Configuration
* Fix logging directory not auto-generated ([#6225](https://github.com/lablup/backend.ai/issues/6225))
* Clients can now correctly fetch null quota scopes when a scope does not exist, instead of encountering an error ([#6227](https://github.com/lablup/backend.ai/issues/6227))
* Fix a permission issue where Storage Proxy would fail to access its glide socket after changing process uid/gid. Users running Storage Proxy with non-root credentials will no longer encounter "Permission Denied" errors during startup. ([#6284](https://github.com/lablup/backend.ai/issues/6284))
* Fix an issue where the Storage Proxy would unnecessarily attempt to create an XFS backend lockfile at `/tmp/backendai-xfs-file-lock` even when XFS storage was not configured. This could cause permission errors if the Storage Proxy lacked access to the `/tmp` directory, preventing the service from starting properly. ([#6285](https://github.com/lablup/backend.ai/issues/6285))
* Prevent artifact deletion when download and archive storage are identical ([#6330](https://github.com/lablup/backend.ai/issues/6330))
* Fixed a timing issue in vfolder deletion by ensuring the DELETE-ONGOING status is set before sending the storage deletion request ([#6486](https://github.com/lablup/backend.ai/issues/6486))

#### Artifact and Reservoir Registry
* Cleanup previous stages' files in artifact import pipeline ([#6251](https://github.com/lablup/backend.ai/issues/6251))
* `ReservoirDownloadStep` fails with connection reset error when artifact size is too large in `vfs_storage` type remote reservoir registry ([#6254](https://github.com/lablup/backend.ai/issues/6254))
* Artifact revision not found error caused by `get_artifact_revision_readme` ([#6485](https://github.com/lablup/backend.ai/issues/6485))

#### App Proxy and Routing
* Add AppProxy setup and initialization workflow to the TUI installer (replacing WSProxy) ([#6228](https://github.com/lablup/backend.ai/issues/6228))
* Add timestamp tracking for route health status to enable staleness detection. Route health checks now store both status and check timestamp, automatically marking health data older than 5 minutes as unhealthy. This prevents routing traffic to routes with stale health information and improves overall system reliability. ([#6423](https://github.com/lablup/backend.ai/issues/6423))
* Fix typo in apollo router config serialization alias (`sapollo-router` -> `apollo-router`) ([#6266](https://github.com/lablup/backend.ai/issues/6266))

#### Model Service
* Fix model service extra mounts in client SDK to omit unset mount `type` fields, ensuring compatibility with the manager API ([#6347](https://github.com/lablup/backend.ai/issues/6347))

#### User and Permission Management
* Change keypair query to include keypairs of users with no group membership ([#6455](https://github.com/lablup/backend.ai/issues/6455))
* Raise error when trying to purge domain with active user, group or kernel instead of returning 204 success response ([#6590](https://github.com/lablup/backend.ai/issues/6590))

#### Image Management
* Resolve deadlock occurring due to incorrect use of semaphore in specific image rescan scenarios ([#6469](https://github.com/lablup/backend.ai/issues/6469))

#### Other Fixes
* Upgrade aiotools (1.9.2 -> 2.2.3) for improved structured concurrency and refactor server initialization and shutdown procedures to avoid excessive exception stack traces but display only the exact error cleanly ([#6250](https://github.com/lablup/backend.ai/issues/6250))
* Fix race conditions in test container port allocation by using dynamic port assignment ([#6207](https://github.com/lablup/backend.ai/issues/6207))
* fix `VFolderAlreadyExists` HTTP status code from 400 Bad Request to 409 Conflict to match semantic meaning of resource conflicts ([#6465](https://github.com/lablup/backend.ai/issues/6465))
* Remove useless README not found warning log ([#6473](https://github.com/lablup/backend.ai/issues/6473))

### Documentation Updates
* Add `Artifact` API descriptions ([#6104](https://github.com/lablup/backend.ai/issues/6104))
* Add `Artifact` concept documentation ([#6105](https://github.com/lablup/backend.ai/issues/6105))
* Add English documentation for Sokovan orchestration layer covering session scheduling, deployment management, and routing architecture. ([#6446](https://github.com/lablup/backend.ai/issues/6446))
* Add comprehensive README documentation for Actions, Services, and Repositories layers in the manager, covering architecture patterns, design principles, resilience patterns with Prometheus metrics, and best practices for each layer. ([#6449](https://github.com/lablup/backend.ai/issues/6449))
* Add comprehensive architecture and component documentation ([#6466](https://github.com/lablup/backend.ai/issues/6466))
* Expand CONTRIBUTING.md with comprehensive pull request guidelines including workflow, sizing best practices, and review process. ([#6481](https://github.com/lablup/backend.ai/issues/6481))
* Update documentation for metrics, session management ([#6586](https://github.com/lablup/backend.ai/issues/6586))
* Improve README documentation structure and execution guide ([#6588](https://github.com/lablup/backend.ai/issues/6588))
* Migrate code quality checks to hook-based system ([#6591](https://github.com/lablup/backend.ai/issues/6591))

### Miscellaneous
* Add warning logs in storage implementations when used or limit bytes are under 0 ([#6359](https://github.com/lablup/backend.ai/issues/6359))
* Expose `SESSION_PRIORITY_*` constants from the manager package to the common package for consistent priority handling across components ([#6459](https://github.com/lablup/backend.ai/issues/6459))


## 25.15.0 (2025-10-02)

### Features

#### Action Processors and RBAC
* Add Action Processors to handle various types of actions ([#5744](https://github.com/lablup/backend.ai/issues/5744))
* Add RBAC validators for Action Processors ([#5758](https://github.com/lablup/backend.ai/issues/5758))
* Add vfolder RBAC validation ([#5759](https://github.com/lablup/backend.ai/issues/5759))

#### Artifact and Reservoir Registry
* Abstract artifact registry storage types in `storage-proxy` ([#5750](https://github.com/lablup/backend.ai/issues/5750))
* Add VFS Storage for Artifact Registry ([#5887](https://github.com/lablup/backend.ai/issues/5887))
* Add `scan`, `import` trigger API schemas on remote reservoir registry ([#6027](https://github.com/lablup/backend.ai/issues/6027))
* Implement `delegate_scan` GQL mutation on remote reservoir registry ([#6053](https://github.com/lablup/backend.ai/issues/6053))
* Add the `enable_reservoir` webserver option to enable reservoir-related features in the webui ([#6055](https://github.com/lablup/backend.ai/issues/6055))

#### Background Tasks
* Implement flexible execution modes (single/batch/parallel) for background task system ([#6058](https://github.com/lablup/backend.ai/issues/6058))

#### Session and Agent Management
* Prevent the kernel runner (and the user container) being accidentally terminated by user's `pkill -f python` command ([#6085](https://github.com/lablup/backend.ai/issues/6085))
* Implement node resolver(`get_node`) in `ComputeSessionNode` enabling clients to query nodes via global ID ([#6108](https://github.com/lablup/backend.ai/issues/6108))
* Implement node resolver(`get_node`) in `AgentNode` enabling clients to query nodes via global ID ([#6109](https://github.com/lablup/backend.ai/issues/6109))
* Add `AgentStats` GQL type and resolver to get agents' total and used resource slots ([#6116](https://github.com/lablup/backend.ai/issues/6116))
* Implements periodic monitoring of container host ports to automatically release unused ports back to the port pool, preventing port exhaustion in long-running agents ([#6125](https://github.com/lablup/backend.ai/issues/6125))

#### User Management
* Add keypairs field to User GQL type and return the created keypairs when creating users ([#6040](https://github.com/lablup/backend.ai/issues/6040))

#### Health Check and Monitoring
* Implement simple health check endpoints returning component status, version, and name ([#6124](https://github.com/lablup/backend.ai/issues/6124))

### Improvements
* Introduce Service, Repository layer pattern when handling Agent Heartbeat ([#5794](https://github.com/lablup/backend.ai/issues/5794))
* Introduce Service, Repository layer pattern in Agent Image remove event handler ([#5898](https://github.com/lablup/backend.ai/issues/5898))
* Introduce service, repository layer when handling agent status change event ([#5921](https://github.com/lablup/backend.ai/issues/5921))
* Remove duplicated exception handling in ResourcePresetCacheSource ([#5976](https://github.com/lablup/backend.ai/issues/5976))
* Refactor GQL Agent resolver functions by applying repository pattern ([#6079](https://github.com/lablup/backend.ai/issues/6079))
* Raise `AgentNotFound` error explicitly when agent not found by id instead of returning none ([#6103](https://github.com/lablup/backend.ai/issues/6103))

### Fixes

#### Storage and Configuration
* Rename `object_storage_namespace` table, and GQL schema to `storage_namespace` ([#6001](https://github.com/lablup/backend.ai/issues/6001))
* Fix `storage-proxy` unified config not pretty printed at bootstrap ([#6008](https://github.com/lablup/backend.ai/issues/6008))
* Fix silent config validation failure of `storage-proxy` ([#6009](https://github.com/lablup/backend.ai/issues/6009))
* Introduce `BaseConfigSchema` to the webserver to easily manage common parts of all configuration objects ([#6078](https://github.com/lablup/backend.ai/issues/6078))
* Introduce `BaseConfigSchema` to the manager to easily manage common parts of all configuration objects ([#6096](https://github.com/lablup/backend.ai/issues/6096))
* Introduce `BaseConfigSchema` to the agent to easily manage common parts of all configuration objects ([#6097](https://github.com/lablup/backend.ai/issues/6097))
* Introduce `BaseConfigSchema` to the storage-proxy to easily manage common parts of all configuration objects ([#6098](https://github.com/lablup/backend.ai/issues/6098))

#### Session Management
* Fix mount permission check during session creation ([#6021](https://github.com/lablup/backend.ai/issues/6021))
* Add missing `kernel_host` field in `KernelCreationInfo` ([#6050](https://github.com/lablup/backend.ai/issues/6050))
* Add missing resolver of GQL Compute session node `resource_opts` field ([#6081](https://github.com/lablup/backend.ai/issues/6081))
* Explicitly load kernel `resource_opts` data in `ComputeSessionNode` using dataloader instead of accessing `self.resource_opts` directly ([#6156](https://github.com/lablup/backend.ai/issues/6156))
* Restore the wildcard subscription functionality of the session events ([#6111](https://github.com/lablup/backend.ai/issues/6111))

#### Agent and Resource Management
* Update GQL Agent type `occupied_slots` field resolver ([#6061](https://github.com/lablup/backend.ai/issues/6061))
* Remove obsolete max slot limit validation from resource calculator ([#6034](https://github.com/lablup/backend.ai/issues/6034))
* Invalidate resource preset cache properly ([#6161](https://github.com/lablup/backend.ai/issues/6161))

#### App Proxy
* Improve error handling in the traefik frontend of App Proxy worker ([#6091](https://github.com/lablup/backend.ai/issues/6091))
* Temporarily revert traefik configuration update delta calculation logic ([#6094](https://github.com/lablup/backend.ai/issues/6094))
* Fix worker and all related entities removed from database when leaving the AppProxy cluster ([#6095](https://github.com/lablup/backend.ai/issues/6095))

#### RBAC and Permissions
* Change unique constraint index of `association_scopes_entities` table and handle unique constraint violation in repository layer ([#6014](https://github.com/lablup/backend.ai/issues/6014))

#### Container Registry
* Validate container registry input in `create`, `update` mutations ([#6160](https://github.com/lablup/backend.ai/issues/6160))
* Add Harbor registry creation argument validation ([#6128](https://github.com/lablup/backend.ai/issues/6128))

#### Metrics and Monitoring
* Fix an issue where utilization metrics for destroyed kernels were not properly cleared from Prometheus, preventing users from seeing accumulated metrics from kernels that no longer exist ([#6139](https://github.com/lablup/backend.ai/issues/6139))
* Add missing null check for batch operation result in `ValkeyStatClient.get_image_distro()` ([#6028](https://github.com/lablup/backend.ai/issues/6028))

#### Scaling Groups
* Handle scaling group deletion errors by logging details and raising proper exceptions ([#6122](https://github.com/lablup/backend.ai/issues/6122))

#### Other Fixes
* Wrong error code of `mgr fixture populate` command ([#6049](https://github.com/lablup/backend.ai/issues/6049))
* Change the installation path to the current location for the installer to operate in development mode ([#6127](https://github.com/lablup/backend.ai/issues/6127))

### External Dependency Updates
* Added Rover CLI installation to install-dev script for supergraph generation in dev environment ([#5664](https://github.com/lablup/backend.ai/issues/5664))
* Build missing agent watcher wheel ([#6115](https://github.com/lablup/backend.ai/issues/6115))

### Miscellaneous
* Add warning log when adding new user with no groups ([#6159](https://github.com/lablup/backend.ai/issues/6159))


## 25.14.5 (2025-09-22)

### Features
* Remove agent count validation for single-node multi-designated sessions ([#5961](https://github.com/lablup/backend.ai/issues/5961))

### External Dependency Updates
* Revert addition of types-networkx dependency because it depends on numpy ([#5978](https://github.com/lablup/backend.ai/issues/5978))


## 25.14.4 (2025-09-19)

### Features
* Add model definition generators for VLLM, TGI, NIM, and CMD runtime variants to support model service deployments ([#5958](https://github.com/lablup/backend.ai/issues/5958))

### Improvements
* Introduce ModelDefinitionGenerator pattern to support multiple runtime variant in model service ([#5924](https://github.com/lablup/backend.ai/issues/5924))

### Fixes
* Change object permission bulk insert to use ORM functions ([#5893](https://github.com/lablup/backend.ai/issues/5893))
* Add missing RBAC function call in update-shared-vfolder action handler ([#5919](https://github.com/lablup/backend.ai/issues/5919))
* Read creation configs using correct key ([#5954](https://github.com/lablup/backend.ai/issues/5954))
* Handle Undefined group IDs when modifying user ([#5955](https://github.com/lablup/backend.ai/issues/5955))
* Aggregate kernel resources instead of using `AgentNode.occupied_slots` in GQL API ([#5957](https://github.com/lablup/backend.ai/issues/5957))
* Scheduler tries destroying kernels that have no container ([#5962](https://github.com/lablup/backend.ai/issues/5962))
* `entrypoint.sh` explicitly runs addgroup to prevent the container's gid setting from being ignored ([#5963](https://github.com/lablup/backend.ai/issues/5963))


## 25.14.3 (2025-09-17)

### Features
* Introduce soft-deletion to `Artifact` model ([#5808](https://github.com/lablup/backend.ai/issues/5808))
* Add artifact presigned download, upload configs in the `storage-proxy.toml` ([#5870](https://github.com/lablup/backend.ai/issues/5870))

### Improvements
* Refactor Message queue architecture by decoupling dispatcher components ([#5805](https://github.com/lablup/backend.ai/issues/5805))

### Fixes
* Fixed missing scaling group filter condition in AgentRow queries that was causing agents to not be properly filtered by scaling group names ([#5894](https://github.com/lablup/backend.ai/issues/5894))
* Fixed missing kernel_image_config references in ImageRef creation where registry name and is_local parameters were using hardcoded values instead of proper config settings. ([#5895](https://github.com/lablup/backend.ai/issues/5895))
* Revert format of Resource preset shared-memory value ([#5896](https://github.com/lablup/backend.ai/issues/5896))
* Fix serialization of Resource preset cache ([#5899](https://github.com/lablup/backend.ai/issues/5899))
* Modify pending session resource limit validation logic ([#5901](https://github.com/lablup/backend.ai/issues/5901))
* Set kernel status to terminated when the kernel is missing ([#5903](https://github.com/lablup/backend.ai/issues/5903))
* Fix Endpoint mutation by querying endpoint records with image objects ([#5905](https://github.com/lablup/backend.ai/issues/5905))

### External Dependency Updates
* Update aiohttp and its dependencies including multidict ([#5786](https://github.com/lablup/backend.ai/issues/5786))

### Miscellaneous
* Replace hardcoded resource slot states with `ResourceSlotState` enum ([#5665](https://github.com/lablup/backend.ai/issues/5665))


## 25.14.2 (2025-09-15)

### Features
* Add GQL Viewer type ([#5728](https://github.com/lablup/backend.ai/issues/5728))


## 25.14.1 (2025-09-15)

### Fixes
* Handle empty `supported_accelerators` list correctly in Image, ImageNode ([#5878](https://github.com/lablup/backend.ai/issues/5878))


## 25.14.0 (2025-09-15)

### Breaking Changes
* Implement password hashing system with multiple algorithms including PBKDF2-SHA3-256 ([#5753](https://github.com/lablup/backend.ai/issues/5753), [#5785](https://github.com/lablup/backend.ai/issues/5785))

### Features

#### RBAC Enhancements
* Add data migration scripts from VFolder to RBAC tables ([#5340](https://github.com/lablup/backend.ai/issues/5340))
* Migrate existing user/project records to RBAC data ([#5417](https://github.com/lablup/backend.ai/issues/5417))
* Expand RBAC tables with `permission_groups` table to group permissions with the same target ([#5465](https://github.com/lablup/backend.ai/issues/5465))
* Add RBAC repository functions to manage scopes and entity DB records ([#5699](https://github.com/lablup/backend.ai/issues/5699))

#### Artifact Management
* Add `reservoir_registries` DB table, service, and CRUD GQL mutations ([#5644](https://github.com/lablup/backend.ai/issues/5644))
* Add `artifact_registries` DB table to store common information of various artifact registries ([#5656](https://github.com/lablup/backend.ai/issues/5656))
* Implement Reservoir registry and Sync APIs between Managers ([#5660](https://github.com/lablup/backend.ai/issues/5660))
* Add `defaultArtifactRegistry` GQL resolver to fetch default artifact registry information ([#5739](https://github.com/lablup/backend.ai/issues/5739))
* Add `Artifact`, `ArtifactRegistry` REST API ([#5747](https://github.com/lablup/backend.ai/issues/5747))

#### Background Tasks
* Add VFolder delete background task ([#5778](https://github.com/lablup/backend.ai/issues/5778))
* Set expiry to set records of Bgtask metadata IDs ([#5736](https://github.com/lablup/backend.ai/issues/5736))

#### Performance and Resource Management
* Apply cache layer for resource presets ([#5781](https://github.com/lablup/backend.ai/issues/5781))
* Align reported agent memory size for consistency in large clusters, preventing inadvertent resource allocation failures ([#5729](https://github.com/lablup/backend.ai/issues/5729))

#### Other Features
* Allow `__typename` type query for advanced GraphQL features (GQL Federation, `@connection` directive) by introducing custom introspection rule ([#5705](https://github.com/lablup/backend.ai/issues/5705))
* Add config for GPFS fileset name prefix ([#5684](https://github.com/lablup/backend.ai/issues/5684))
* Add session mode (Client, Proxy) based error handling in FetchContextManager ([#5774](https://github.com/lablup/backend.ai/issues/5774))
* Remove obsolete max slot limit validation during session creation ([#5807](https://github.com/lablup/backend.ai/issues/5807))
* Implement health check functionality for route management ([#5811](https://github.com/lablup/backend.ai/issues/5811))
* Introduce error code to storage-proxy exceptions ([#5813](https://github.com/lablup/backend.ai/issues/5813))
* Add config to disable artifact approval process ([#5830](https://github.com/lablup/backend.ai/issues/5830))

### Improvements
* Migrate legacy redis clients to valkey clients in App Proxy ([#5741](https://github.com/lablup/backend.ai/issues/5741))

### Fixes

#### Session Management
* Add missing session live stat update ([#5762](https://github.com/lablup/backend.ai/issues/5762))
* Ensure worker object refresh after DB flush in update_worker ([#5674](https://github.com/lablup/backend.ai/issues/5674))
* Handle empty `supported_accelerators` list in `Image`, `ImageNode` ([#5869](https://github.com/lablup/backend.ai/issues/5869))
* Reset pending queue when there are no sessions with scheduling failures ([#5865](https://github.com/lablup/backend.ai/issues/5865))

#### Network and Docker
* Make overlay network creation idempotent to prevent infinite retry loops ([#5765](https://github.com/lablup/backend.ai/issues/5765))
* Clean up dangling docker networks ([#5770](https://github.com/lablup/backend.ai/issues/5770))
* Add missing `restart: unless-stopped` policy to docker compose services ([#5694](https://github.com/lablup/backend.ai/issues/5694))

#### API and Permissions
* Fix `modify_user` GQL mutation's `project` update due to incorrect condition ([#5850](https://github.com/lablup/backend.ai/issues/5850))
* Fix wrong syntax in object permission record adder function ([#5849](https://github.com/lablup/backend.ai/issues/5849))
* Check if vfolder is mounted to any session before deleting ([#5855](https://github.com/lablup/backend.ai/issues/5855))
* Restrict `limit` parameter in `scan_artifacts` API ([#5801](https://github.com/lablup/backend.ai/issues/5801))

#### Proxy and Health Check
* Fix JSON parsing error when wsproxy returns HTML error responses ([#5829](https://github.com/lablup/backend.ai/issues/5829))
* Update kernel host references to current kernel host in proxy and health check logic ([#5834](https://github.com/lablup/backend.ai/issues/5834))
* Add missing update when app proxy registers endpoint ([#5783](https://github.com/lablup/backend.ai/issues/5783))

#### Other Fixes
* Fix import paths for `ai.backend.errors.*` in migration script ([#5828](https://github.com/lablup/backend.ai/issues/5828))
* Mark hint for immediate model-service update ([#5845](https://github.com/lablup/backend.ai/issues/5845))
* Initialize ResourceSlot with known_slots in resource occupancy calculation ([#5860](https://github.com/lablup/backend.ai/issues/5860))
* Ensure model service token expiration times are handled consistently in UTC ([#5872](https://github.com/lablup/backend.ai/issues/5872))
* Update client SDK to reflect UUID-only restriction in session dependencies ([#5809](https://github.com/lablup/backend.ai/issues/5809))

### Miscellaneous
* Refactor scheduler handlers: Split into individual files and create a base handler class ([#5766](https://github.com/lablup/backend.ai/issues/5766))


## 25.13.4 (2025-09-03)

### Fixes
* Add missing scheduler options to AllowedScalingGroup and update related components ([#5730](https://github.com/lablup/backend.ai/issues/5730))


## 25.13.3 (2025-09-03)

### Fixes
* Improve HTTP request proxying in the webserver to be transparent with content-encoding ([#5709](https://github.com/lablup/backend.ai/issues/5709))
* Add null-user check in resource usage query ([#5712](https://github.com/lablup/backend.ai/issues/5712))
* Ensure id parameter of chown function is an int ([#5713](https://github.com/lablup/backend.ai/issues/5713))
* Refresh agent fields in kernel when rescheduling ([#5717](https://github.com/lablup/backend.ai/issues/5717))
* Fix issue where App-Proxy failed to query worker circuits due to incorrect variable reference ([#5718](https://github.com/lablup/backend.ai/issues/5718))
* Add missing network cleanup when creating overlay network ([#5721](https://github.com/lablup/backend.ai/issues/5721))


## 25.13.2 (2025-09-02)

### Features
* The mouse-selected or copy-mode selected texts in the intrinsic ttyd app with tmux are now directly copied to the user-side clipboard, without needing to `set mouse=off` in the tmux session ([#5688](https://github.com/lablup/backend.ai/issues/5688))
* feat: Improvement redis keys command to scan_iter for manager cli ([#5704](https://github.com/lablup/backend.ai/issues/5704))

### Fixes
* Add missing all-smi manpage file in the wheel packages ([#5685](https://github.com/lablup/backend.ai/issues/5685))
* Updated RedisProfileTarget to handle cases where 'addr' is missing or None in the input data, preventing errors during address parsing. ([#5695](https://github.com/lablup/backend.ai/issues/5695))
* fixes a duplicate joins issue during serialization when using pydantic by removing the join filter from the TOMLStringListField's _transform method. ([#5700](https://github.com/lablup/backend.ai/issues/5700))
* Fix coordinator not performing health check for all endpoints ([#5702](https://github.com/lablup/backend.ai/issues/5702))
* Fix session creation failing with `not allowed scaling group` error ([#5706](https://github.com/lablup/backend.ai/issues/5706))
* Enhance endpoint creation logic to update existing records and handle circuits ([#5707](https://github.com/lablup/backend.ai/issues/5707))


## 25.13.1 (2025-08-29)

### Fixes
* Fix session ordering in session_pending_queue query resolver ([#5682](https://github.com/lablup/backend.ai/issues/5682))
* fix: Ensure redis address is nullable ([#5683](https://github.com/lablup/backend.ai/issues/5683))


## 25.13.0 (2025-08-29)

### Features
* Introduce `strawberry`, and strawberry-based `ArtifactRegistry` GQL types ([#5232](https://github.com/lablup/backend.ai/issues/5232))
* Add `ModelDeployment`, `ModelRevision` strawberry GQL types migrated from existing federated graphene schema ([#5249](https://github.com/lablup/backend.ai/issues/5249))
* Open-source and integrate Backend.AI App Proxy into the main codebase ([#5275](https://github.com/lablup/backend.ai/issues/5275))
* Add `storages` API to storage proxy ([#5286](https://github.com/lablup/backend.ai/issues/5286))
* Add OpenTelemetry and service discovery configuration to appproxy ([#5296](https://github.com/lablup/backend.ai/issues/5296))
* Implement connection monitoring and reconnection logic in ValkeyStandaloneClient ([#5298](https://github.com/lablup/backend.ai/issues/5298))
* Implement Sokovan orchestrator architecture ([#5361](https://github.com/lablup/backend.ai/issues/5361))
* Add `HuggingFace` scanner, and API to storage proxy ([#5362](https://github.com/lablup/backend.ai/issues/5362))
* Split out container log processing to a more concrete `ValkeyContainerLogClient` (based on `ValkeyClient` with default behavior) and use a separate Redis instance dedicated for log streaming ([#5375](https://github.com/lablup/backend.ai/issues/5375))
* Implement scheduling prioritizers ([#5378](https://github.com/lablup/backend.ai/issues/5378))
* Add validators for scheduling ([#5380](https://github.com/lablup/backend.ai/issues/5380))
* Ship [`all-smi`](https://github.com/inureyes/all-smi) so that users can execute it inside any session container ([#5381](https://github.com/lablup/backend.ai/issues/5381))
* Implement sokovan scheduler agent selectors ([#5383](https://github.com/lablup/backend.ai/issues/5383))
* Integrate Agent selector with allocator in sokovan orchestrator ([#5393](https://github.com/lablup/backend.ai/issues/5393))
* Add `UserNode` as a field of `ComputeSessionNode` ([#5403](https://github.com/lablup/backend.ai/issues/5403))
* Enhance Scheduler allocation logic and add comprehensive tests ([#5404](https://github.com/lablup/backend.ai/issues/5404))
* Add allocation methods in scheduler repository ([#5406](https://github.com/lablup/backend.ai/issues/5406))
* Add TTL support to Redis key operations in AppProxy ([#5416](https://github.com/lablup/backend.ai/issues/5416))
* Unify separate GraphQL subgraph endpoints into single Apollo Router supergraph with web-server proxy integration to enable single endpoint access for clients ([#5419](https://github.com/lablup/backend.ai/issues/5419))
* Integrate sokovan orchestrator in manager ([#5421](https://github.com/lablup/backend.ai/issues/5421))
* Add `source` field to roles table to distinguish system-defined roles from custom-defined roles, enabling automatic permission grants for system roles when new entity types or operations are introduced ([#5440](https://github.com/lablup/backend.ai/issues/5440))
* Add phase tracking in scheduling ([#5441](https://github.com/lablup/backend.ai/issues/5441))
* Implement scheduler coordinator in sokovan orchestrator ([#5455](https://github.com/lablup/backend.ai/issues/5455))
* Changed the behavior to terminate "terminating session" in batch processing ([#5467](https://github.com/lablup/backend.ai/issues/5467))
* Implement session sweeping functionality and related handlers ([#5485](https://github.com/lablup/backend.ai/issues/5485))
* Inject `storages` config to storage-proxy ([#5491](https://github.com/lablup/backend.ai/issues/5491))
* Add `object_storages` table to DB ([#5498](https://github.com/lablup/backend.ai/issues/5498))
* Add request_timeout configuration for Redis clients ([#5502](https://github.com/lablup/backend.ai/issues/5502))
* Add decrement_keypair_concurrencies method and update session termination logic ([#5504](https://github.com/lablup/backend.ai/issues/5504))
* Add `hugging_registries` DB table, and GQL schema ([#5508](https://github.com/lablup/backend.ai/issues/5508))
* Replace the existing `ArtifactGroup` model with `Artifact`, and replace `Artifact` with `ArtifactRevision` ([#5510](https://github.com/lablup/backend.ai/issues/5510))
* Integrate `Artifact` service to Manager ([#5514](https://github.com/lablup/backend.ai/issues/5514))
* Add Valkey client for Background Task Manager ([#5519](https://github.com/lablup/backend.ai/issues/5519))
* Improve `logging.BraceStyleAdapter` to support user-defined kwargs and access to `extra` data including contextual fields. ([#5523](https://github.com/lablup/backend.ai/issues/5523))
* Add Background Task heartbeat loop to refresh TTL ([#5531](https://github.com/lablup/backend.ai/issues/5531))
* Modify value reading to avoid cache-based scheduling ([#5533](https://github.com/lablup/backend.ai/issues/5533))
* Implement scheduling controller ([#5547](https://github.com/lablup/backend.ai/issues/5547))
* Implement kernel state engine ([#5551](https://github.com/lablup/backend.ai/issues/5551))
* Add Background Task retry loop ([#5555](https://github.com/lablup/backend.ai/issues/5555))
* Allow specifying multiple endpoint addresses in the etcd config ([#5564](https://github.com/lablup/backend.ai/issues/5564))
* Update session limits to allow None and 0 as indicators for unlimited concurrent sessions ([#5567](https://github.com/lablup/backend.ai/issues/5567))
* Add configuration option for Sokovan orchestrator usage ([#5568](https://github.com/lablup/backend.ai/issues/5568))
* Implement health monitoring for scheduling operations ([#5569](https://github.com/lablup/backend.ai/issues/5569))
* Enhance session management by adding checks for truly stuck pulling and creating sessions ([#5570](https://github.com/lablup/backend.ai/issues/5570))
* Add Valkey Client TLS configuration ([#5573](https://github.com/lablup/backend.ai/issues/5573))
* Implement Generalized pagination on Strawberry GQL API ([#5575](https://github.com/lablup/backend.ai/issues/5575))
* Implement session transition hooks for various session types ([#5579](https://github.com/lablup/backend.ai/issues/5579))
* Implement deployment management with Sokovan integration ([#5580](https://github.com/lablup/backend.ai/issues/5580))
* Implement batch scheduling events and event propagation through Event Hub ([#5589](https://github.com/lablup/backend.ai/issues/5589))
* Apply centralized distributed locking for Sokovan scheduling operations ([#5592](https://github.com/lablup/backend.ai/issues/5592))
* Implement cache-through pattern for keypair concurrency management in SchedulerRepository ([#5594](https://github.com/lablup/backend.ai/issues/5594))
* Apply READ COMMITTED isolation level for scheduler operations ([#5600](https://github.com/lablup/backend.ai/issues/5600))
* Add Volume Pool field to `RootContext` of Storage-Proxy ([#5603](https://github.com/lablup/backend.ai/issues/5603))
* Add Bgtask handler Registry ([#5606](https://github.com/lablup/backend.ai/issues/5606))
* Implement Valkey-based leader election in manager ([#5607](https://github.com/lablup/backend.ai/issues/5607))
* Apply retry feature to VFolder clone bgtask ([#5611](https://github.com/lablup/backend.ai/issues/5611))
* Add `object_storage_meta` DB table for managing buckets ([#5617](https://github.com/lablup/backend.ai/issues/5617))
* Add operation metrics observer for session termination tracking ([#5623](https://github.com/lablup/backend.ai/issues/5623))
* Implement EventPropagatorMetricObserver for tracking event propagator metrics ([#5630](https://github.com/lablup/backend.ai/issues/5630))
* Apply cache propagator when broadcasting scheduling event ([#5638](https://github.com/lablup/backend.ai/issues/5638))
* Implement deployment controller and integrate with sokovan orchestrator ([#5639](https://github.com/lablup/backend.ai/issues/5639))
* Added automated GraphQL supergraph generation using rover CLI to CI pipeline for improved schema management ([#5645](https://github.com/lablup/backend.ai/issues/5645))
* Add `--wait` option to `backend.ai events` command for easier scripting and automation ([#5650](https://github.com/lablup/backend.ai/issues/5650))
* Implement session wait logic in AgentRegistry for improved scheduling handling ([#5659](https://github.com/lablup/backend.ai/issues/5659))
* Manage object storage buckets using `storage_namespace` ([#5667](https://github.com/lablup/backend.ai/issues/5667))
* Add scheduling detail info for pending sessions ([#5676](https://github.com/lablup/backend.ai/issues/5676))

### Fixes
* Correct the asyncio connection sharing pattern in alembic `env.py` so that we could use `alembic-rebase.py` script and other alembic-based automation seamlessly. ([#5151](https://github.com/lablup/backend.ai/issues/5151))
* Use persistent `aiohttp.ClientSession` instances per route in App Proxy circuits to benefit from keep-alive connections and resource reuse ([#5287](https://github.com/lablup/backend.ai/issues/5287))
* Add missing resolver of VFolder permissions field in Compute session node ([#5322](https://github.com/lablup/backend.ai/issues/5322))
* Let insepct.signature handle stringified types generated by `__future__` annotations by setting the `eval_str` option to True ([#5325](https://github.com/lablup/backend.ai/issues/5325))
* Handle None user when request context setup in auth middleware ([#5327](https://github.com/lablup/backend.ai/issues/5327))
* Add missing database transaction retry logic when setting network ID of new sessions ([#5329](https://github.com/lablup/backend.ai/issues/5329))
* Apply memoization to the scheduler plugin loaders to reduce runtime overheads when running the scheduler loop ([#5342](https://github.com/lablup/backend.ai/issues/5342))
* Broken Agent, Webserver in HA development environment ([#5343](https://github.com/lablup/backend.ai/issues/5343))
* Add missing components in HA development environment ([#5345](https://github.com/lablup/backend.ai/issues/5345))
* Make `--log-level` and `--debug` flag behavior and description consistent across all `start-server` commands ([#5366](https://github.com/lablup/backend.ai/issues/5366))
* Defer imports in the CLI and server entrypoints to reduce CLI startup times and avoid unnecessary cross-component imports ([#5372](https://github.com/lablup/backend.ai/issues/5372))
* Fix and improve optimization to glob-based BUILD file scanning when loading CLI entrypoints, improving the CLI command initialization latency for about 15% (e.g., 3.5 sec -> 3.0 sec) ([#5377](https://github.com/lablup/backend.ai/issues/5377))
* Fix missing `event_logs` table creation when populating the database schema with `mgr schema oneshot`, which may have caused issues in fresh installations ([#5391](https://github.com/lablup/backend.ai/issues/5391))
* Add Docker image rescan exception handling logic when the image config is `None` ([#5394](https://github.com/lablup/backend.ai/issues/5394))
* Serialize `ResourceSlot` type values in GQL resolvers ([#5433](https://github.com/lablup/backend.ai/issues/5433))
* Remove wrong `ImageRef` stringification when push image ([#5434](https://github.com/lablup/backend.ai/issues/5434))
* Fix wrong image type search logic used in `ImageNode` instance creation ([#5435](https://github.com/lablup/backend.ai/issues/5435))
* Wrong error handling of `User` CRUD mutations ([#5446](https://github.com/lablup/backend.ai/issues/5446))
* Fix App Proxy health-check done against sub-kernels due to misgeneration of route information for cluster sessions, which had wrongly included sub-kernel service ports ([#5447](https://github.com/lablup/backend.ai/issues/5447))
* Change `Circuit` query logic in AppProxy for `Circuit` object's serializability ([#5448](https://github.com/lablup/backend.ai/issues/5448))
* Wrong request header validation error handling of Webserver ([#5449](https://github.com/lablup/backend.ai/issues/5449))
* Fix NUMA-aware affinity allocation to find the larged connected component with the most remaining resource capacity when grouping devices per NUMA node ([#5454](https://github.com/lablup/backend.ai/issues/5454))
* Prevent the Agent from producing error events in the heartbeat loop to avoid loop termination due to Redis connection failures ([#5469](https://github.com/lablup/backend.ai/issues/5469))
* Fixed session being incorrectly set on failed login attempts and ensured `X-BackendAI-SessionID` header is always included when login succeeds ([#5473](https://github.com/lablup/backend.ai/issues/5473))
* Respect the inherited ulimits when setting ulimits of new containers ([#5489](https://github.com/lablup/backend.ai/issues/5489))
* Handle clone tasks through events to avoid clone status hanging caused by potential termination of clone-tracking tasks ([#5493](https://github.com/lablup/backend.ai/issues/5493))
* Document the internal logic of affinity-aware device allocation and improve error messages ([#5521](https://github.com/lablup/backend.ai/issues/5521))
* Update all import occurrences of `BraceStyleAdapter` in App Proxy to use the core `ai.backend.logging` package so that the App Proxy codebase is compatible with #5523 ([#5550](https://github.com/lablup/backend.ai/issues/5550))
* Fix manager.wsproxy's HTTP requests to use relative URLs as the default factory sets `base_url` of `aiohttp.ClientSession` instances ([#5576](https://github.com/lablup/backend.ai/issues/5576))
* Improve agent idempotency when provisioning kernel resources to better support the new Sokovan scheduler's retry mechanisms ([#5584](https://github.com/lablup/backend.ai/issues/5584))
* Fix NUMA node alignment of subsequent device allocation ([#5587](https://github.com/lablup/backend.ai/issues/5587))
* Fix regression of agent's per-package log-level configurations ([#5614](https://github.com/lablup/backend.ai/issues/5614))
* Enhance kernel status handling for resource occupancy tracking ([#5619](https://github.com/lablup/backend.ai/issues/5619))
* Fix hanging kernel creation in the new Sokovan scheduler when the host account's UID/GID is not 1000 ([#5626](https://github.com/lablup/backend.ai/issues/5626))
* Rename `object_storage_meta` table to `object_storage_namespace` ([#5666](https://github.com/lablup/backend.ai/issues/5666))

### External Dependency Updates
* Upgrade the base CPython version from 3.13.3 to 3.13.7 ([#5536](https://github.com/lablup/backend.ai/issues/5536))
* Update all-smi binaries to v0.8.0 ([#5588](https://github.com/lablup/backend.ai/issues/5588))
* Update all-smi binaries to v0.9.0 ([#5677](https://github.com/lablup/backend.ai/issues/5677))

### Miscellaneous
* Refactor the import structure for `RepositoryArgs` by moving it to a dedicated `ai.backend.manager.repositories.types` module ([#5409](https://github.com/lablup/backend.ai/issues/5409))
* Upgrade the CI toolchain such as Pantsbuild (2.23.1 -> 2.27.0), Ruff (0.8.5 -> 0.12.9), and Mypy (1.15.0 -> 1.17.1) with merging BUILD files for faster dependency resolution to reduce human mistakes on managing them and cleaning up various lint warnings ([#5529](https://github.com/lablup/backend.ai/issues/5529))
* Add Strawberry GraphQL mypy plugin to fix mypy compatibility issues with cutom types from Strawberrt GraphQL ([#5574](https://github.com/lablup/backend.ai/issues/5574))

### Test Updates
* Add Backgroundtask unit tests ([#5625](https://github.com/lablup/backend.ai/issues/5625))


## 25.12.1 (2025-07-25)

### Features
* Agent heartbeat handler queries Kernel ids instead of Agent id ([#4766](https://github.com/lablup/backend.ai/issues/4766))
* Implement ActionValidator ([#5244](https://github.com/lablup/backend.ai/issues/5244))
* Implement reconnection logic in ValkeySentinelClient ([#5276](https://github.com/lablup/backend.ai/issues/5276))

### Improvements
* Apply simple model query pattern for readability ([#4767](https://github.com/lablup/backend.ai/issues/4767))

### Fixes
* Fix model service creation failure when `service-definition.toml` is missing ([#5264](https://github.com/lablup/backend.ai/issues/5264))
* Fix model service deletion failure for non super-admin users ([#5266](https://github.com/lablup/backend.ai/issues/5266))
* Broken VFolder `Clone` service ([#5269](https://github.com/lablup/backend.ai/issues/5269))
* Fixed a problem with deserializing dataclass ([#5271](https://github.com/lablup/backend.ai/issues/5271))
* Fix broken VFolder `GetTaskLogs` service ([#5272](https://github.com/lablup/backend.ai/issues/5272))
* Add missing TRACE log-level option in ai.backend.logging package ([#5274](https://github.com/lablup/backend.ai/issues/5274))
* `status_data` not initialized properly when creating multi node session ([#5280](https://github.com/lablup/backend.ai/issues/5280))
* Apply a workaround to avoid segfault upon fast termination of `mgr etcd` CLI commands that queries and updates etcd configurations ([#5283](https://github.com/lablup/backend.ai/issues/5283))


## 25.12.0 (2025-07-23)

### Breaking Changes
* - Health check capability temporarily broken on OSS AppProxy due to architectural changes
  - Users must disable health check feature in `model-definition.yaml` to use model services on Open Source Backend.AI
  - OSS AppProxy support will be restored in future releases ([#5134](https://github.com/lablup/backend.ai/issues/5134))

### Features
* Add VFolder share test verifying shared project vfolder has override permission to shared user ([#4971](https://github.com/lablup/backend.ai/issues/4971))
* Add metadata support to event handling and message payloads ([#4992](https://github.com/lablup/backend.ai/issues/4992))
* Add tests for both successful and failed purge group operations ([#5006](https://github.com/lablup/backend.ai/issues/5006))
* Add RBAC DB schema ([#5025](https://github.com/lablup/backend.ai/issues/5025))
* Apply valkey client for redis_image ([#5031](https://github.com/lablup/backend.ai/issues/5031))
* Implement ValkeyLiveClient for Redis interactions and add related tests ([#5032](https://github.com/lablup/backend.ai/issues/5032))
* Apply ValkeyStatClient ([#5035](https://github.com/lablup/backend.ai/issues/5035))
* Implement ValkeyRateLimitClient ([#5036](https://github.com/lablup/backend.ai/issues/5036))
* Add ValkeyStreamLockClient ([#5039](https://github.com/lablup/backend.ai/issues/5039))
* Unify valkey client codes ([#5053](https://github.com/lablup/backend.ai/issues/5053))
* Support OTEL to storage-proxy and webserver components ([#5054](https://github.com/lablup/backend.ai/issues/5054))
* Add TRACE Level for log ([#5092](https://github.com/lablup/backend.ai/issues/5092))
* Implement configuration management CLI for agent, storage, and webserver ([#5103](https://github.com/lablup/backend.ai/issues/5103))
* Implement ValkeySessionClient for session management using Valkey-Glide ([#5114](https://github.com/lablup/backend.ai/issues/5114))
* Add `triggered_by` to `AuditLog` table ([#5115](https://github.com/lablup/backend.ai/issues/5115))
* - Offload model service health check architecture to AppProxy with Redis-based route management for improved scalability and real-time endpoint monitoring ([#5134](https://github.com/lablup/backend.ai/issues/5134))
* Impl Role management Service ([#5159](https://github.com/lablup/backend.ai/issues/5159))
* Add layer-aware repository decorators to various layers ([#5161](https://github.com/lablup/backend.ai/issues/5161))
* Add `type` field to `ImageNode` ([#5207](https://github.com/lablup/backend.ai/issues/5207))
* Add chown feature to Agent to allow change owner of mount path ([#5213](https://github.com/lablup/backend.ai/issues/5213))
* Apply client pool in web component ([#5223](https://github.com/lablup/backend.ai/issues/5223))
* Sync model service's health information real-time with AppProxy ([#5230](https://github.com/lablup/backend.ai/issues/5230))
* Add `mount_ids`, `mount_id_map` fields to session creation config ([#5237](https://github.com/lablup/backend.ai/issues/5237))
* Apply client pool to wsproxy client ([#5253](https://github.com/lablup/backend.ai/issues/5253))
* Add retry metrics for layer observer ([#5255](https://github.com/lablup/backend.ai/issues/5255))

### Improvements
* Apply provisioner pattern to Agent kernel lifecycle "mount" stage ([#4979](https://github.com/lablup/backend.ai/issues/4979))
* Apply provisioner pattern to Agent kernel lifecycle "image" stage ([#4981](https://github.com/lablup/backend.ai/issues/4981))
* Apply provisioner pattern to Agent kernel lifecycle "network" stage ([#4982](https://github.com/lablup/backend.ai/issues/4982))
* Apply provisioner pattern to Agent kernel lifecycle "resource" stage ([#4983](https://github.com/lablup/backend.ai/issues/4983))
* Apply provisioner pattern to Agent kernel lifecycle "scratch" stage ([#4984](https://github.com/lablup/backend.ai/issues/4984))
* Apply provisioner pattern to Agent kernel lifecycle "ssh" stage ([#4985](https://github.com/lablup/backend.ai/issues/4985))
* Apply provisioner pattern to Agent kernel lifecycle "environ" stage ([#4986](https://github.com/lablup/backend.ai/issues/4986))
* Apply pydantic config in storage-proxy ([#5062](https://github.com/lablup/backend.ai/issues/5062))
* Apply pydantic config in webserver ([#5064](https://github.com/lablup/backend.ai/issues/5064))
* Apply pydantic config in agent ([#5068](https://github.com/lablup/backend.ai/issues/5068))
* Separate repository layer from auth service ([#5071](https://github.com/lablup/backend.ai/issues/5071))
* Separate repository layer from model serving service ([#5072](https://github.com/lablup/backend.ai/issues/5072))
* Separate repository layer from image service ([#5074](https://github.com/lablup/backend.ai/issues/5074))
* Separate repository layer from user service ([#5076](https://github.com/lablup/backend.ai/issues/5076))
* Separate repository layer from container registry service ([#5095](https://github.com/lablup/backend.ai/issues/5095))
* Add repository and inject repositories dependency ([#5097](https://github.com/lablup/backend.ai/issues/5097))
* Separate repository layer from domain service ([#5099](https://github.com/lablup/backend.ai/issues/5099))
* Separate repository layer from scheduler ([#5101](https://github.com/lablup/backend.ai/issues/5101))
* Separate repository layer from group service ([#5107](https://github.com/lablup/backend.ai/issues/5107))
* Refactor endpoint status resolution to use `EndpointStatus` enum instead of string literals ([#5109](https://github.com/lablup/backend.ai/issues/5109))
* Separate repository layer from session service ([#5110](https://github.com/lablup/backend.ai/issues/5110))
* Separate repository layer from vfolder service ([#5111](https://github.com/lablup/backend.ai/issues/5111))
* Separate repository layer from agent service ([#5128](https://github.com/lablup/backend.ai/issues/5128))
* Separate repository layer from resource preset service ([#5130](https://github.com/lablup/backend.ai/issues/5130))
* Separate agent client layer ([#5157](https://github.com/lablup/backend.ai/issues/5157))
* Separate exceptions file ([#5164](https://github.com/lablup/backend.ai/issues/5164))
* Separate wsproxy client ([#5165](https://github.com/lablup/backend.ai/issues/5165))
* Implement Storage Proxy client layer ([#5224](https://github.com/lablup/backend.ai/issues/5224))

### Fixes
* Wrong `service ports` field name of Session creation response ([#5047](https://github.com/lablup/backend.ai/issues/5047))
* Fix GraphQL resolver for compute session to return only a unique set of vfolder mount names ([#5056](https://github.com/lablup/backend.ai/issues/5056))
* Fix unbound `vfolder_id` when model-type folder is used in service `extra_mounts` ([#5059](https://github.com/lablup/backend.ai/issues/5059))
* Manager correctly handles already-deleted VFolders ([#5080](https://github.com/lablup/backend.ai/issues/5080))
* Fix cloud provider detection working on Azure and future-compatible by using versioned metadata URLs instead of hacky sysfs DMI vendor information checks ([#5086](https://github.com/lablup/backend.ai/issues/5086))
* Enable continuous code execution tasks to work properly in Agent ([#5112](https://github.com/lablup/backend.ai/issues/5112))
* Enable Agent starts if scratch already cleaned before destroy container ([#5118](https://github.com/lablup/backend.ai/issues/5118))
* Handle empty consumer handlers in EventDispatcher to avoid retry ([#5136](https://github.com/lablup/backend.ai/issues/5136))
* Relax Decimal serialization of Agent stats ([#5142](https://github.com/lablup/backend.ai/issues/5142))
* Fix webserver 404 not found issue ([#5170](https://github.com/lablup/backend.ai/issues/5170))
* Fix auth action to pass stoken param ([#5211](https://github.com/lablup/backend.ai/issues/5211))
* `status_data` not initialized properly when creating single node session ([#5217](https://github.com/lablup/backend.ai/issues/5217))
* Fix potential consumer loop hang by handling `glide.TimeoutError` from Valkey-glide `xreadgroup` ([#5222](https://github.com/lablup/backend.ai/issues/5222))
* Fix Grafana configuration for halfstack ([#5248](https://github.com/lablup/backend.ai/issues/5248))

### Miscellaneous
* Add `[tool.pyright]` section to `pyproject.toml` so that IDEs using Pyright as the default LSP works out of the box by detecting Pants-specific configurations ([#5088](https://github.com/lablup/backend.ai/issues/5088))

### Test Updates
* Add session service unit test ([#4265](https://github.com/lablup/backend.ai/issues/4265))
* Add unit test for Project Resource Policy service & repository ([#5192](https://github.com/lablup/backend.ai/issues/5192))
* Add test code for container utilization metric service ([#5194](https://github.com/lablup/backend.ai/issues/5194))
* Add test code for resource preset service ([#5195](https://github.com/lablup/backend.ai/issues/5195))
* Add `Domain` service unit test ([#5196](https://github.com/lablup/backend.ai/issues/5196))
* Add test code for user service ([#5197](https://github.com/lablup/backend.ai/issues/5197))
* Add test code for user resource policy service ([#5198](https://github.com/lablup/backend.ai/issues/5198))
* Add `KeypairResourcePolicy` service unit test ([#5203](https://github.com/lablup/backend.ai/issues/5203))
* Add service layer, repository layer unit test for `Model Service` ([#5214](https://github.com/lablup/backend.ai/issues/5214))
* Add unit(service, repository layer), integration test for `Auth` ([#5234](https://github.com/lablup/backend.ai/issues/5234))
* Add unit(service, repository layer), integration test for `Container Registry` ([#5258](https://github.com/lablup/backend.ai/issues/5258))


## 25.11.0 (2025-07-09)

### Features
* Add Model Service Endpoint Health check, and Authentication test ([#4774](https://github.com/lablup/backend.ai/issues/4774))
* Add Model Service Replicas Scale success, fail test ([#4777](https://github.com/lablup/backend.ai/issues/4777))
* Implement `UserResourcePolicy` CRUD SDK functions ([#4782](https://github.com/lablup/backend.ai/issues/4782))
* Implement ValkeyStreamClient for managing Valkey Streams ([#4792](https://github.com/lablup/backend.ai/issues/4792))
* Add more filterspecs to `ImageNode` ([#4803](https://github.com/lablup/backend.ai/issues/4803))
* Add `environ` to `service-definition.toml` schema ([#4826](https://github.com/lablup/backend.ai/issues/4826))
* Print warning message when `bootstrap.sh` exists, but is not executable ([#4829](https://github.com/lablup/backend.ai/issues/4829))
* Add a new webserver configuration option `default_file_browser_image` to specify a default file browser image. ([#4836](https://github.com/lablup/backend.ai/issues/4836))
* Implement the `VFolder.get_id` SDK function to query a vfolder's ID by its name. ([#4856](https://github.com/lablup/backend.ai/issues/4856))
* Add VFolder soft-delete, restore, and purge tests ([#4873](https://github.com/lablup/backend.ai/issues/4873))
* Add VFolder upload, and download file tests ([#4877](https://github.com/lablup/backend.ai/issues/4877))
* Add VFolder file list, rename, move, deletion tests ([#4884](https://github.com/lablup/backend.ai/issues/4884))
* Add VFolder clone test ([#4885](https://github.com/lablup/backend.ai/issues/4885))
* Add VFolder invitation test ([#4903](https://github.com/lablup/backend.ai/issues/4903))
* Make Endpoint GQL Query filterable by endpoint owner's UUID ([#4907](https://github.com/lablup/backend.ai/issues/4907))
* Reduce dangling kernel logging in Agent ([#4912](https://github.com/lablup/backend.ai/issues/4912))
* Add `exclude_tags` to tester.toml to exclude tests requiring extra config from default runs, improving the accessibility of the Tester package ([#4914](https://github.com/lablup/backend.ai/issues/4914))
* Observe count of trigger and result Agent stat collection task ([#4926](https://github.com/lablup/backend.ai/issues/4926))
* Add expiration time to login history Redis keys to reduce Redis memory usage. ([#4939](https://github.com/lablup/backend.ai/issues/4939))
* Add aliases to Agent `announce-addr`, `service-addr` configurations ([#4940](https://github.com/lablup/backend.ai/issues/4940))
* Add Agent stat stage metric ([#4944](https://github.com/lablup/backend.ai/issues/4944))
* Built-in WSProxy exposes advertised address ([#4975](https://github.com/lablup/backend.ai/issues/4975))
* Implement ValkeySentinelClient with connection management and master monitoring ([#4987](https://github.com/lablup/backend.ai/issues/4987))
* Add JSON log formatter for OTEL ([#4991](https://github.com/lablup/backend.ai/issues/4991))
* Add configuration management CLI commands and sample generator ([#5019](https://github.com/lablup/backend.ai/issues/5019))

### Fixes
* Fix GQL endpoint list resolver sorting by lifecycle_stage ([#4776](https://github.com/lablup/backend.ai/issues/4776))
* Improve logging for inspecting missing containers ([#4784](https://github.com/lablup/backend.ai/issues/4784))
* Allow None type of session id in `RouteInfo` preventing pydantic type error when querying `ModelService.get_info` right after creating model service ([#4786](https://github.com/lablup/backend.ai/issues/4786))
* Status code is missing when the `Accept` header is not set to `application/json` in the wsproxy exception middleware ([#4788](https://github.com/lablup/backend.ai/issues/4788))
* Fix Agent Memory plugin to handle multiple IO device stat ([#4789](https://github.com/lablup/backend.ai/issues/4789))
* Fix invalid state error when setting kernel termination future ([#4791](https://github.com/lablup/backend.ai/issues/4791))
* Fix wrong exit code when `BaseRunner.query()` fails ([#4798](https://github.com/lablup/backend.ai/issues/4798))
* Fix model service creation failing due to parameter validation by excluding None values in model service create SDK request ([#4799](https://github.com/lablup/backend.ai/issues/4799))
* Name session test using `test_id` in failure cases ([#4831](https://github.com/lablup/backend.ai/issues/4831))
* Fix incorrect query filter definition in GQL image node ([#4843](https://github.com/lablup/backend.ai/issues/4843))
* Fix compute plugin's `cleanup()` method not being called upon agent shutdown ([#4851](https://github.com/lablup/backend.ai/issues/4851))
* Prevent model service creation with project type vfolder ([#4852](https://github.com/lablup/backend.ai/issues/4852))
* Fixed auto scaling rule processing to skip deleted model services, preventing unnecessary operations ([#4875](https://github.com/lablup/backend.ai/issues/4875))
* Allow GQL modify_user mutation to update users `main_access_key` ([#4879](https://github.com/lablup/backend.ai/issues/4879))
* Skip logging agent status heartbeat to event logs ([#4895](https://github.com/lablup/backend.ai/issues/4895))
* Fix wrong error message when vfolder invitation row not found ([#4906](https://github.com/lablup/backend.ai/issues/4906))
* Return null for empty `unmanaged_path` field in vfolder GQL type ([#4913](https://github.com/lablup/backend.ai/issues/4913))
* Ensure endpoints are properly cleaned up during group purge operations ([#4917](https://github.com/lablup/backend.ai/issues/4917))
* Handle `NoSuchProcess` properly when gather process memory stat ([#4922](https://github.com/lablup/backend.ai/issues/4922))
* Skip kernel destroy when agent shutdown ([#4923](https://github.com/lablup/backend.ai/issues/4923))
* Check if Agent is daemon process before query docker netstat ([#4929](https://github.com/lablup/backend.ai/issues/4929))
* Handle invalid moving statistics value ([#4934](https://github.com/lablup/backend.ai/issues/4934))
* Skip exporter containers when detecting postgres container in dbshell command ([#4935](https://github.com/lablup/backend.ai/issues/4935))
* Wrong indent in Agent container stat function ([#4946](https://github.com/lablup/backend.ai/issues/4946))
* Fix broken tester's `PlainTextFilesUploader` in macOS ([#4953](https://github.com/lablup/backend.ai/issues/4953))
* Remove `session`, `kernel`'s foreign key constraints with `users`, `keypairs`, and fix `PurgeUser` GQL mutation not working when active compute session exist ([#4954](https://github.com/lablup/backend.ai/issues/4954))
* Change to use json.dumps in Agent to properly serialize yarl types ([#4957](https://github.com/lablup/backend.ai/issues/4957))
* Fixed cache read failure in Message Queue ([#4968](https://github.com/lablup/backend.ai/issues/4968))
* Handle unexpected errors in EventDispatcher consume and subscribe loops ([#5009](https://github.com/lablup/backend.ai/issues/5009))
* Fix incorrect filetype check of `PureStorage` VFolder ([#5018](https://github.com/lablup/backend.ai/issues/5018))

### Documentation Updates
* Add extra documentation to `tester` package's `README.md` ([#4845](https://github.com/lablup/backend.ai/issues/4845))

### External Dependency Updates
* Fix aiodns version to 3.2.0 ([#4950](https://github.com/lablup/backend.ai/issues/4950))

### Miscellaneous
* Consolidate halfstack compose files to main config ([#4839](https://github.com/lablup/backend.ai/issues/4839))
* Add `metric` to sample Etcd config ([#4886](https://github.com/lablup/backend.ai/issues/4886))


## 25.10.1 (2025-06-25)

### Features
* Configure the logging module's config file to use Pydantic ([#2834](https://github.com/lablup/backend.ai/issues/2834))
* Add installed field to GQL image node query schema ([#4757](https://github.com/lablup/backend.ai/issues/4757))

### Fixes
* Fixed optional field handling in `AutoScalingRule` modify action by replacing `None` with `Undefined` ([#1636](https://github.com/lablup/backend.ai/issues/1636))
* Cool down Redis error logs `AttributeError: 'NoneType' object has no attribute 'get'` ([#4795](https://github.com/lablup/backend.ai/issues/4795))
* Fix wrong `Accept` Header on `HarborRegistryV2._process_oci_index()` ([#4807](https://github.com/lablup/backend.ai/issues/4807))


## 25.10.0 (2025-06-23)

### Features
* Add `image purge` CLI command for hard deleting `ImageRow`. ([#3951](https://github.com/lablup/backend.ai/issues/3951))
* Add `service-definition.toml` handling logic in the ModelServing creation service ([#4220](https://github.com/lablup/backend.ai/issues/4220))
* Implement test specification management and execution framework ([#4614](https://github.com/lablup/backend.ai/issues/4614))
* Add creation wrappers for each session type and test cases for session creation ([#4654](https://github.com/lablup/backend.ai/issues/4654))
* Add Tester configuration, and template for config injection ([#4661](https://github.com/lablup/backend.ai/issues/4661))
* Add `ComputeSessionNode` query method in compute session sdk to offer detail info about session ([#4669](https://github.com/lablup/backend.ai/issues/4669))
* Replace hardcoded bgtask status event codes with `BgtaskStatus` enum values ([#4671](https://github.com/lablup/backend.ai/issues/4671))
* Agent sends container status through heartbeat ([#4677](https://github.com/lablup/backend.ai/issues/4677))
* Add session rename test verifying success renaming and prevent duplicate renaming ([#4680](https://github.com/lablup/backend.ai/issues/4680))
* Add parametrize functionality in tester spec ([#4692](https://github.com/lablup/backend.ai/issues/4692))
* Add session status history retrieval test validating history not empty and contains valid statuses ([#4697](https://github.com/lablup/backend.ai/issues/4697))
* Add session dependency graph retrieval test validating dependency graphs between sessions ([#4698](https://github.com/lablup/backend.ai/issues/4698))
* Improve Exporter to easily check error information when an error occurs ([#4701](https://github.com/lablup/backend.ai/issues/4701))
* Add metric for sync container lifecycle task ([#4704](https://github.com/lablup/backend.ai/issues/4704))
* Add python code execution tests to Tester ([#4709](https://github.com/lablup/backend.ai/issues/4709))
* Add Container purge RPC to agent ([#4710](https://github.com/lablup/backend.ai/issues/4710))
* Add session imagify, commit test to Tester ([#4713](https://github.com/lablup/backend.ai/issues/4713))
* Manager purges kernels and containers with mismatched status between DB and agent heartbeat ([#4717](https://github.com/lablup/backend.ai/issues/4717))
* Add session creation test using various options ([#4729](https://github.com/lablup/backend.ai/issues/4729))
* Add vfolder mounted session tests verifying file upload and downloads ([#4732](https://github.com/lablup/backend.ai/issues/4732))
* Add additional logging to kernel creation and termination ([#4737](https://github.com/lablup/backend.ai/issues/4737))
* Add `EndpointTemplate` for testing Model Service ([#4744](https://github.com/lablup/backend.ai/issues/4744))
* Add `runtime_variant` parameter to Service creation SDK function and CLI command ([#4749](https://github.com/lablup/backend.ai/issues/4749))
* Agent heartbeat handler queries Kernel ids instead of Agent id ([#4766](https://github.com/lablup/backend.ai/issues/4766))

### Improvements
* Refactor event dispatchers registration of idle checkers ([#4516](https://github.com/lablup/backend.ai/issues/4516))
* Differenciate consume and subscribe events ([#4620](https://github.com/lablup/backend.ai/issues/4620))

### Fixes
* Add missing event handler for SessionCheckingPrecondEvent ([#4619](https://github.com/lablup/backend.ai/issues/4619))
* Fix manager config models being validated only by alias ([#4624](https://github.com/lablup/backend.ai/issues/4624))
* Support more Accept headers in `BaseContainerRegistry.scan_tag` ([#4627](https://github.com/lablup/backend.ai/issues/4627))
* Resolve broken image rescanning on macOS due to `aiotools` upstream issue ([#4628](https://github.com/lablup/backend.ai/issues/4628))
* Fix container utilization metric service config reload not working ([#4640](https://github.com/lablup/backend.ai/issues/4640))
* Update container ports validation to catch omitted or empty list cases, preventing potential `IndexError` ([#4656](https://github.com/lablup/backend.ai/issues/4656))
* Prevent remount NFS path ([#4663](https://github.com/lablup/backend.ai/issues/4663))
* Agent skips failure of code runner initialization ([#4679](https://github.com/lablup/backend.ai/issues/4679))
* Fix Session Rename API to block duplicate session names for the same user ([#4690](https://github.com/lablup/backend.ai/issues/4690))
* Update `endpoints.destroyed_at` column when serving is terminated ([#4696](https://github.com/lablup/backend.ai/issues/4696))
* Fix license config not included in PluginConfig after Pydantic migration ([#4718](https://github.com/lablup/backend.ai/issues/4718))
* Fix broken `untag_image_from_registry` SDK method ([#4720](https://github.com/lablup/backend.ai/issues/4720))
* Include `image_id` to `message` field of `imagify` REST API's bgtask response ([#4723](https://github.com/lablup/backend.ai/issues/4723))
* Close code runner of agent gracefully ([#4740](https://github.com/lablup/backend.ai/issues/4740))
* Allow `ComputeSession` SDK methods to identify sessions by id ([#4750](https://github.com/lablup/backend.ai/issues/4750))
* Skip gathering metrics of non-existent processes ([#4753](https://github.com/lablup/backend.ai/issues/4753))
* Fix kernel runner and agent rpc server return code completion result ([#4754](https://github.com/lablup/backend.ai/issues/4754))
* Use correct attribute `routings` instead of `routes` for endpoints ([#4756](https://github.com/lablup/backend.ai/issues/4756))

### Miscellaneous
* Remove `enable2FA` config from webserver ([#4653](https://github.com/lablup/backend.ai/issues/4653))
* Ensure the `Vite` build tool, required by the `backend.ai-ui` package, is installed before building the WebUI ([#4725](https://github.com/lablup/backend.ai/issues/4725))


## 25.9.1 (2025-06-05)

### Features
* Prevent batch kernel termination when an agent shutdown ([#4587](https://github.com/lablup/backend.ai/issues/4587))
* Add Redis-based Service Discovery ([#4609](https://github.com/lablup/backend.ai/issues/4609))

### Fixes
* Fix `ModelServingService.delete_route()` to query the `RouteRow` with `load_endpoint=True`, ensuring the `endpoint` relationship is eagerly loaded ([#4590](https://github.com/lablup/backend.ai/issues/4590))
* Replace assert statements in `load_model_definition` with raising exception ([#4599](https://github.com/lablup/backend.ai/issues/4599))
* Resolve `generate-rpc-keypair` CLI command failure due to `rpc_auth_manager_keypair` not found error ([#4612](https://github.com/lablup/backend.ai/issues/4612))

### Documentation Updates
* Added clarifying comments to prevent `Auth` SDK config confusion ([#4607](https://github.com/lablup/backend.ai/issues/4607))

### Miscellaneous
* Add Etcd, Redis, and PostgreSQL exporters/scrapers in local development environment configuration. ([#4606](https://github.com/lablup/backend.ai/issues/4606))


## 25.9.0 (2025-06-02)

### Features
* Add Action Tests for `Image`. ([#4048](https://github.com/lablup/backend.ai/issues/4048))
* Enable TOTP registration for anonymous users ([#4354](https://github.com/lablup/backend.ai/issues/4354))
* Refactor event dispatcher and handlers directory structure ([#4497](https://github.com/lablup/backend.ai/issues/4497))
* Add `EventDomain.WORKFLOW` enum value to support workflow-related event categorization ([#4499](https://github.com/lablup/backend.ai/issues/4499))
* Create new manager CLI command `backend.ai mgr scheduler last-execution-time` to let administrators fetch each manager scheduler's last execution time ([#4507](https://github.com/lablup/backend.ai/issues/4507))
* Add stage package to support deterministic step-by-step execution ([#4509](https://github.com/lablup/backend.ai/issues/4509))
* Make resource fragmentation configurable ([#4533](https://github.com/lablup/backend.ai/issues/4533))
* Add missing `GET /status_history` endpoint to the session REST API ([#4543](https://github.com/lablup/backend.ai/issues/4543))

### Improvements
* Refactor `keypair_preparation` from a classmethod of the Graphene class to a utility function to decouple logic from GraphQL ([#4510](https://github.com/lablup/backend.ai/issues/4510))
* Introduce service layer in `auth` APIs to apply audit logs for user login APIs ([#4535](https://github.com/lablup/backend.ai/issues/4535))
* Improve logging for error handling in various modules ([#4540](https://github.com/lablup/backend.ai/issues/4540))
* Initialize device env vars with/without restart to make session restart successfully ([#4585](https://github.com/lablup/backend.ai/issues/4585))

### Fixes
* heartbeat register service when service is dead ([#4492](https://github.com/lablup/backend.ai/issues/4492))
* Fix missing log output of GraphQL top-level query fields by improving graphene's resolver info object usage ([#4505](https://github.com/lablup/backend.ai/issues/4505))
* Fix Backend.AI agent equipped with mock accelerator refusing to allocate mock accelerator to session after agent restart ([#4532](https://github.com/lablup/backend.ai/issues/4532))
* Fix broken `list_presets` API, SDK ([#4541](https://github.com/lablup/backend.ai/issues/4541))
* Fix broken `usage_per_month` method in Resource SDK ([#4546](https://github.com/lablup/backend.ai/issues/4546))
* Fix broken `Keypair` SDK methods (`activate`, `deactivate`) ([#4547](https://github.com/lablup/backend.ai/issues/4547))
* Broken `stream_pty` method in Session SDK ([#4548](https://github.com/lablup/backend.ai/issues/4548))
* Fix missing entity id in processor ([#4550](https://github.com/lablup/backend.ai/issues/4550))
* Fix wrong idle checker init arguments ([#4557](https://github.com/lablup/backend.ai/issues/4557))
* Fix broken `Network` SDK implementations to work properly ([#4558](https://github.com/lablup/backend.ai/issues/4558))
* Skip processing messages with None data in RedisQueue ([#4559](https://github.com/lablup/backend.ai/issues/4559))
* Add missing `message` field to `BgTaskFailedEvent` to provide information about the occurred error ([#4563](https://github.com/lablup/backend.ai/issues/4563))
* Fix `AgentWatcher.get_status` SDK API to use query parameter instead of using body ([#4569](https://github.com/lablup/backend.ai/issues/4569))
* Correct the worker process ID and names in the server log outputs, which had been unintentionally overriden as the main process information ([#4572](https://github.com/lablup/backend.ai/issues/4572))
* Resolve session creation failure due to incorrect resource label loading ([#4573](https://github.com/lablup/backend.ai/issues/4573))
* Remove duplicated error logging in Session service ([#4574](https://github.com/lablup/backend.ai/issues/4574))
* Fix Backend.AI agent to gracefully handle missing `Config.Labels` field in Docker image inspection ([#4576](https://github.com/lablup/backend.ai/issues/4576))
* Do null-check of kernel service-ports when query direct access info of a compute session ([#4581](https://github.com/lablup/backend.ai/issues/4581))

### Miscellaneous
* Remove outdated Image SDK methods (`get_image_import_form`, `build`) ([#4537](https://github.com/lablup/backend.ai/issues/4537))
* Remove useless print in `ScalingGroup.list_available` ([#4538](https://github.com/lablup/backend.ai/issues/4538))


## 25.8.1 (2025-05-23)

### Fixes
* Fixed client SDK method `Service.create()` signature to comply with `NewServiceRequestModel` schema ([#4449](https://github.com/lablup/backend.ai/issues/4449))


## 25.8.0 (2025-05-23)

### Features
* Add Manager config implementations based on Pydantic. ([#3994](https://github.com/lablup/backend.ai/issues/3994))
* Add Action Test Code for `Group` ([#4051](https://github.com/lablup/backend.ai/issues/4051))
* Add Action Test Code for `User` ([#4059](https://github.com/lablup/backend.ai/issues/4059))
* Add model service & processors ([#4109](https://github.com/lablup/backend.ai/issues/4109))
* Apply error code in BackendError ([#4245](https://github.com/lablup/backend.ai/issues/4245))
* Migrate manager config to Pydantic. ([#4317](https://github.com/lablup/backend.ai/issues/4317))
* Introduce `LabelName` enum to avoid hardcoded image/container labels ([#4328](https://github.com/lablup/backend.ai/issues/4328))
* Add error code to API exception message ([#4336](https://github.com/lablup/backend.ai/issues/4336))
* Add error code to metric ([#4337](https://github.com/lablup/backend.ai/issues/4337))
* Add etcd service discovery ([#4343](https://github.com/lablup/backend.ai/issues/4343))
* Introduce ConfigLoaders, UnifiedConfig, and refactor existing config logic. ([#4351](https://github.com/lablup/backend.ai/issues/4351))
* Add VFolder force-delete API to Python client SDK ([#4353](https://github.com/lablup/backend.ai/issues/4353))
* Refactor event propagation ([#4358](https://github.com/lablup/backend.ai/issues/4358))
* Integrate of `ManagerLocalConfig` with `ManagerSharedConfig`, and Make all manager configs to share the same Chain Config Loader. ([#4370](https://github.com/lablup/backend.ai/issues/4370))
* Add GQL APIs for querying and updating the current config status. ([#4376](https://github.com/lablup/backend.ai/issues/4376))
* Introduce ProcessorPackage for list up each action types that can be processed by ActionProcessor. ([#4379](https://github.com/lablup/backend.ai/issues/4379))
* Add kernel last-seen event and handler ([#4386](https://github.com/lablup/backend.ai/issues/4386))
* Add event logger for consumer handlers ([#4387](https://github.com/lablup/backend.ai/issues/4387))
* Introduce `ActionSpec`. ([#4393](https://github.com/lablup/backend.ai/issues/4393))
* Support relative path for `AutoDirectoryPath`. ([#4413](https://github.com/lablup/backend.ai/issues/4413))
* Register service discovery and add http service discovery for prometheus ([#4438](https://github.com/lablup/backend.ai/issues/4438))
* Add OpenTelemetry dependencies for enhanced observability ([#4479](https://github.com/lablup/backend.ai/issues/4479))

### Improvements
* Refactor the `alias` of `ManagerSharedConfig` into `validation_alias` and `serialization_alias`. ([#4365](https://github.com/lablup/backend.ai/issues/4365))

### Fixes
* Resolve `BgTaskFailedError` is not propagated to the client. ([#4272](https://github.com/lablup/backend.ai/issues/4272))
* Fix invalid msg_id type in hiredis message queue ([#4309](https://github.com/lablup/backend.ai/issues/4309))
* Prevent invalid resource slot creation, and mutation in `ResourcePresetService`. ([#4314](https://github.com/lablup/backend.ai/issues/4314))
* Agent retries retrieving kernel service info if it fails during the kernel creation step ([#4321](https://github.com/lablup/backend.ai/issues/4321))
* Add TypeError handling in redis_helper ([#4339](https://github.com/lablup/backend.ai/issues/4339))
* Add default value of task_info value ([#4340](https://github.com/lablup/backend.ai/issues/4340))
* Use label's items for making resource info ([#4341](https://github.com/lablup/backend.ai/issues/4341))
* Add missing `KernelStatus.ERROR` to dead kernel status set ([#4371](https://github.com/lablup/backend.ai/issues/4371))
* Make BaseAction's `entity_type()`, `operation_type()` classmethod. ([#4377](https://github.com/lablup/backend.ai/issues/4377))
* Revert addition of `SessionStatus.ERROR` and `KernelStatus.ERROR` to dead status sets ([#4384](https://github.com/lablup/backend.ai/issues/4384))
* Fix event handling observer to report success or failure after handling completes ([#4392](https://github.com/lablup/backend.ai/issues/4392))
* Revert sane default config update. ([#4395](https://github.com/lablup/backend.ai/issues/4395))
* Add missing `UserBgtaskEvent` implementation. ([#4404](https://github.com/lablup/backend.ai/issues/4404))
* Change pyzmq version on python-kernel, compatible with python 3.13 ([#4405](https://github.com/lablup/backend.ai/issues/4405))
* Fix `vfolder ls` CLI command which referred deprecated response schema fields. ([#4425](https://github.com/lablup/backend.ai/issues/4425))
* Fix `backend.ai admin resource usage-per-period` CLI command. ([#4429](https://github.com/lablup/backend.ai/issues/4429))
* Add import statement of `KernelLifecycleEventReason` to load legacy kernels in agents ([#4436](https://github.com/lablup/backend.ai/issues/4436))
* Increase blocking timeout for message retrieval in redis message queue ([#4441](https://github.com/lablup/backend.ai/issues/4441))
* Add UUID serialization support in ExtendedJSONEncoder ([#4442](https://github.com/lablup/backend.ai/issues/4442))
* Improve error handling for token generation in ModelServingService ([#4443](https://github.com/lablup/backend.ai/issues/4443))
* Fix issue preventing admins from leaving invited vfolders ([#4446](https://github.com/lablup/backend.ai/issues/4446))
* Fixed session environment variable init during route creation when `endpoint.environ` is `None` ([#4447](https://github.com/lablup/backend.ai/issues/4447))
* Check unregistered email and update error code when vfolder invitation conflicts & Enhance error handling with detailed debug responses in exception middleware ([#4448](https://github.com/lablup/backend.ai/issues/4448))
* Fixed `Service.create()` in client SDK to truncate the default generated session name to the maximum allowed length ([#4450](https://github.com/lablup/backend.ai/issues/4450))
* Add missing defaults to BootstrapConfig. ([#4453](https://github.com/lablup/backend.ai/issues/4453))
* Fix issue preventing users from uploading files to compute sessions ([#4457](https://github.com/lablup/backend.ai/issues/4457))
* Calculate correct VFolder permissions when admins query ([#4459](https://github.com/lablup/backend.ai/issues/4459))
* Fix incorrect handling of disallowed permissions in GQL middleware. ([#4463](https://github.com/lablup/backend.ai/issues/4463))
* Handle `NoItems` exception correctly in CLI framework. ([#4465](https://github.com/lablup/backend.ai/issues/4465))
* Fix wrong method name in rpc call metric ([#4475](https://github.com/lablup/backend.ai/issues/4475))

### Documentation Updates
* Update Python Version Compatibility in README ([#4306](https://github.com/lablup/backend.ai/issues/4306))
* Update towncrier command documentation ([#4364](https://github.com/lablup/backend.ai/issues/4364))

### Miscellaneous
* Add build wheel script ([#4313](https://github.com/lablup/backend.ai/issues/4313))
* Add release script ([#4316](https://github.com/lablup/backend.ai/issues/4316))
* Renamed `RedisConfig` to `RedisTarget` to avoid name conflicts with the existing `config`. ([#4363](https://github.com/lablup/backend.ai/issues/4363))
* Remove subscribed_actions config, and change AuditLogReporter to AuditLogMonitor. ([#4400](https://github.com/lablup/backend.ai/issues/4400))


## 25.7.0 (2025-04-28)
No significant changes.


## 25.6.3 (2025-04-28)
No significant changes.


## 25.6.2 (2025-04-28)

### Fixes
* Fix `Images.supported_accelerators` GQL field not containing every accelerators that image supports ([#4230](https://github.com/lablup/backend.ai/issues/4230))
* Resolve `ImageAliasData` type not found issue in `ImageAliasData.to_dataclass()`. ([#4232](https://github.com/lablup/backend.ai/issues/4232))
* Filter out duplicate vFolder mounts when enqueueing sessions ([#4247](https://github.com/lablup/backend.ai/issues/4247))
* Fix invalid logging format by replacing percent-style (`%s`) with brace-style (`{}`) for compatibility with `BraceStyleAdapter` ([#4256](https://github.com/lablup/backend.ai/issues/4256))
* Added missing `version` field to the `project` section in pyproject.toml to resolve build failures when installing the package via pip from a Git repository ([#4259](https://github.com/lablup/backend.ai/issues/4259))
* Add missing parser to `AuditLogNode`'s `status`, `duration` fields in queryfilter. ([#4260](https://github.com/lablup/backend.ai/issues/4260))
* Fix kernel cleanup by ensuring kernels and their containers are properly destroyed during initialization failures ([#4264](https://github.com/lablup/backend.ai/issues/4264))
* Fix wrong fieldspec in `User` ([#4268](https://github.com/lablup/backend.ai/issues/4268))
* Make enable reading both Enum name and Enum value ([#4269](https://github.com/lablup/backend.ai/issues/4269))
* Improve duplicate vfolder mount detection by checking both folder ID and subpath, allowing multiple mounts from the same folder with different subpaths ([#4274](https://github.com/lablup/backend.ai/issues/4274))
* Fix wrong value of Session download-single file API result ([#4276](https://github.com/lablup/backend.ai/issues/4276))
* Upgrade pyjwt version due to security vulnerability ([#4287](https://github.com/lablup/backend.ai/issues/4287))


## 25.6.1 (2025-04-21)

### Features
* Add more filterspec to `EndPoint` GQL. ([#4210](https://github.com/lablup/backend.ai/issues/4210))

### Fixes
* Fix wrong types in `ResourcePolicy` GQL modifier. ([#4154](https://github.com/lablup/backend.ai/issues/4154))
* Fix VFolder clone by correcting access to user info ([#4214](https://github.com/lablup/backend.ai/issues/4214))
* Skip destroying session's network if session does not have any network ([#4215](https://github.com/lablup/backend.ai/issues/4215))
* Calculate RBAC admin role in project correctly ([#4218](https://github.com/lablup/backend.ai/issues/4218))
* Fix extra mounts of model services ([#4224](https://github.com/lablup/backend.ai/issues/4224))
* Add missing `dtparse` for `created_at` in queryfilter ([#4225](https://github.com/lablup/backend.ai/issues/4225))
* Revert response schema of vfolder mkdir API ([#4227](https://github.com/lablup/backend.ai/issues/4227))


## 25.6.0 (2025-04-17)

### Breaking Changes
* Add `force`, `noprune` options to `PurgeImages` GQL API, and allow `PurgeImages` to be performed on multiple agents (breaking change). ([#3987](https://github.com/lablup/backend.ai/issues/3987))

### Features
* Add `enable_model_folders` option to control the visibility of the Models tab and MODEL usage mode on the Data page in the Backend.AI Web UI. ([#3503](https://github.com/lablup/backend.ai/issues/3503))
* Add `project_node` field of type GroupConnection to GQL `UserNode` type ([#3529](https://github.com/lablup/backend.ai/issues/3529))
* Make `images` table's `resource` column to contain only admin-customized values (Not updated when rescanning the image), and make custom resource limits non-volatile. ([#3986](https://github.com/lablup/backend.ai/issues/3986))
* Add `AuditLog` GQL interface. ([#4001](https://github.com/lablup/backend.ai/issues/4001))
* Add vfolder services and processes ([#4002](https://github.com/lablup/backend.ai/issues/4002))
* Add `domain` service & processors. ([#4012](https://github.com/lablup/backend.ai/issues/4012))
* Add `group` service and processors ([#4026](https://github.com/lablup/backend.ai/issues/4026))
* Add GQL query for user utilization metrics ([#4027](https://github.com/lablup/backend.ai/issues/4027))
* Add Action Test Code for `Domain` ([#4030](https://github.com/lablup/backend.ai/issues/4030))
* Add `User` Service & Processors ([#4058](https://github.com/lablup/backend.ai/issues/4058))
* Refactor Redis message queue to follow ABC pattern ([#4064](https://github.com/lablup/backend.ai/issues/4064))
* Use `http.HTTPStatus` enum for HTTP status codes ([#4069](https://github.com/lablup/backend.ai/issues/4069))
* Add `AuditLog` ActionMonitor and Reporter. ([#4087](https://github.com/lablup/backend.ai/issues/4087))
*  ([#4091](https://github.com/lablup/backend.ai/issues/4091))
* Add new metrics reporters that report raw utilization values without hook modifications ([#4099](https://github.com/lablup/backend.ai/issues/4099))
* Align action architecture code ([#4103](https://github.com/lablup/backend.ai/issues/4103))
* Add RequestID context & middleware ([#4104](https://github.com/lablup/backend.ai/issues/4104))
* Add available min/max resource slot fields to Resource group GQL types ([#4108](https://github.com/lablup/backend.ai/issues/4108))
* Add `SMTP` ActionMonitor and Reporter. ([#4118](https://github.com/lablup/backend.ai/issues/4118))
* Update parser to process model definition YAML according to YAML 1.2 spec ([#4124](https://github.com/lablup/backend.ai/issues/4124))
* Add `action_id` in ActionProcessor for tracking Action. ([#4131](https://github.com/lablup/backend.ai/issues/4131))
* Make a reporter hub for configurable monitoring ([#4165](https://github.com/lablup/backend.ai/issues/4165))
* Add prometheus monitor ([#4167](https://github.com/lablup/backend.ai/issues/4167))
* Add sample configuration for `audit_log`, `smtp` reporter. ([#4170](https://github.com/lablup/backend.ai/issues/4170))
* Validate SSH keypairs when upload them ([#4176](https://github.com/lablup/backend.ai/issues/4176))
* Customize SMTP mail template. ([#4207](https://github.com/lablup/backend.ai/issues/4207))

### Fixes
* Remove `private` value in kernel-feature label before commiting images to list committed images on the session launcher ([#3641](https://github.com/lablup/backend.ai/issues/3641))
* Unload the removed docker images from Redis cache. ([#3923](https://github.com/lablup/backend.ai/issues/3923))
* Fix customized image visibility issue. ([#3939](https://github.com/lablup/backend.ai/issues/3939))
* Add `Image` service & processors. ([#3997](https://github.com/lablup/backend.ai/issues/3997))
* Add `Resource` service & processors. ([#4016](https://github.com/lablup/backend.ai/issues/4016))
* Add missing newline at end of customized dotfiles. ([#4047](https://github.com/lablup/backend.ai/issues/4047))
* Add `Session` service & processors. ([#4061](https://github.com/lablup/backend.ai/issues/4061))
* Remove wrong `Accept` header from Image rescanning logic. ([#4066](https://github.com/lablup/backend.ai/issues/4066))
* Setup source at producer creation ([#4068](https://github.com/lablup/backend.ai/issues/4068))
* Add missing `AuditLog` module import to ensure AuditLog table created at initial installation. ([#4079](https://github.com/lablup/backend.ai/issues/4079))
* Change default value of `domain` table columns ([#4081](https://github.com/lablup/backend.ai/issues/4081))
* Avoid kernel DB full scan when resolving GQL Agent queries ([#4086](https://github.com/lablup/backend.ai/issues/4086))
* Filter Compute Session list query by project when project id scope is specified ([#4089](https://github.com/lablup/backend.ai/issues/4089))
* Fix pydantic validation error from wrong type aliasing. ([#4094](https://github.com/lablup/backend.ai/issues/4094))
* Replace aiodataloader-ng (a fork based on 0.2.1) with the managed upstream aiodataloader package (0.4.2) ([#4098](https://github.com/lablup/backend.ai/issues/4098))
* Fix wrong name of quota scope type fields ([#4123](https://github.com/lablup/backend.ai/issues/4123))
* Fix wrong project-id parsing when creating project vfolders ([#4144](https://github.com/lablup/backend.ai/issues/4144))
* Fix broken model service creation logic due to field name change. ([#4159](https://github.com/lablup/backend.ai/issues/4159))
* Fix broken single image rescan on `HarborRegistryV2`. ([#4161](https://github.com/lablup/backend.ai/issues/4161))
* Fix Broken `UntagImageFromRegistry` GQL mutation. ([#4177](https://github.com/lablup/backend.ai/issues/4177))
* Replace `aiosmtplib` with `smtplib` in SMTP reporter. ([#4179](https://github.com/lablup/backend.ai/issues/4179))
* Fix wrong custom image owner check logic. ([#4181](https://github.com/lablup/backend.ai/issues/4181))
* Add missing `application/vnd.oci.image.manifest.v1` type handling on HarborRegistryV2's single image rescan. ([#4188](https://github.com/lablup/backend.ai/issues/4188))
* Fix the representation that shows invited VFolder users having VFolder deletion permissions ([#4190](https://github.com/lablup/backend.ai/issues/4190))
* Fix wrong `Accept` header handling in image rescanning. ([#4191](https://github.com/lablup/backend.ai/issues/4191))
* Fix VFolder permission update mutation not working. ([#4194](https://github.com/lablup/backend.ai/issues/4194))
* Fix `chunk too big` error of admin image rescan command. ([#4198](https://github.com/lablup/backend.ai/issues/4198))
* Unify BaseAction's `operation_type` convention. ([#4200](https://github.com/lablup/backend.ai/issues/4200))

### External Dependency Updates
* Update most native dependencies to make them compatible with Python 3.13, and downgrade multidict to avoid memory leak in the upstream ([#4122](https://github.com/lablup/backend.ai/issues/4122))
* Retire etcetra in favor of etcd-client-py ([#4152](https://github.com/lablup/backend.ai/issues/4152))
* Upgrade the base CPython from 3.12.8 to 3.13.3, which will bring huge performance improvements with asyncio ([#4153](https://github.com/lablup/backend.ai/issues/4153))


## 25.5.2 (2025-03-31)

### Features
* Split `hanging_session_scanner_ctx` into separate stale session and kernel sweepers to more robustly handle orphaned kernels, caused by session status update mismatches ([#3992](https://github.com/lablup/backend.ai/issues/3992))
* Fix typo in keypair resource policy affecting `max_concurrent_sftp_sessions` ([#4050](https://github.com/lablup/backend.ai/issues/4050))
* Add raise exception in action processor ([#4056](https://github.com/lablup/backend.ai/issues/4056))

### Fixes
* Fix image rescanning wrong exception handling logic. ([#4057](https://github.com/lablup/backend.ai/issues/4057))
* Fix docker network not created when bootstraping multi-container session ([#4062](https://github.com/lablup/backend.ai/issues/4062))


## 25.5.1 (2025-03-27)

### Fixes
* Fix exceeding amount of sessions removed when scaling down model service ([#4037](https://github.com/lablup/backend.ai/issues/4037))
* Add missing migration revision history file ([#4039](https://github.com/lablup/backend.ai/issues/4039))
* Missing `watcher` arg in storage volume init methods ([#4041](https://github.com/lablup/backend.ai/issues/4041))
* Do not check storage host permission in VFolder RBAC function ([#4045](https://github.com/lablup/backend.ai/issues/4045))


## 25.5.0 (2025-03-25)

### Features
* Add GQL schema to query total resource slots of compute sessions in scopes or specified conditions. ([#2849](https://github.com/lablup/backend.ai/issues/2849))
* Add `AuditLog` table. ([#3712](https://github.com/lablup/backend.ai/issues/3712))
* Improve performance of vfolder `list_host()` API handler through task parallel execution. ([#3935](https://github.com/lablup/backend.ai/issues/3935))
* Add accelerator quantum size field to GQL scaling group ([#3940](https://github.com/lablup/backend.ai/issues/3940))
* Add container labels to simplify metric queries ([#3980](https://github.com/lablup/backend.ai/issues/3980))
* Separate internal api port ([#3989](https://github.com/lablup/backend.ai/issues/3989))
* Make action processor work with async functions ([#3999](https://github.com/lablup/backend.ai/issues/3999))
* Enhance session status transition management ([#4029](https://github.com/lablup/backend.ai/issues/4029))

### Fixes
* Properly handle zero-value unknown resource limits when creating session. ([#3925](https://github.com/lablup/backend.ai/issues/3925))
* Fix `PurgeImageById` mutation not working when `image_aliass` are present. ([#3972](https://github.com/lablup/backend.ai/issues/3972))
* Fix wrong error message logging when `model_path` does not exist. ([#3990](https://github.com/lablup/backend.ai/issues/3990))
* Allow superadmins to query all GQL agent nodes ([#3996](https://github.com/lablup/backend.ai/issues/3996))
* Fix wrong JSON serialization for response of list presets API handler ([#4006](https://github.com/lablup/backend.ai/issues/4006))
* Fix a potential race condition error in the kernel runner's OOM logger ([#4008](https://github.com/lablup/backend.ai/issues/4008))
* Fix initialization of Storage proxy event dispatcher ([#4010](https://github.com/lablup/backend.ai/issues/4010))
* Update common structure. (Remove `request_id` from `BaseAction`, add `processors_ctx`). ([#4022](https://github.com/lablup/backend.ai/issues/4022))
* Fix wrong parse of auto-mount vfolders inputs ([#4025](https://github.com/lablup/backend.ai/issues/4025))
* Fix `modify_compute_session` GQL mutation error caused by missing kernel loading option. ([#4032](https://github.com/lablup/backend.ai/issues/4032))


## 25.4.0 (2025-03-12)

### Features
* Implement GQL API for scanning GPU allocation map ([#2273](https://github.com/lablup/backend.ai/issues/2273))
* Add image_node and vfolder_node fields to ComputeSession schema ([#2987](https://github.com/lablup/backend.ai/issues/2987))
* Cache `gpu_alloc_map` in Redis, and Add `RescanGPUAllocMaps` mutation for update the `gpu_alloc_map`s. ([#3293](https://github.com/lablup/backend.ai/issues/3293))
* Collect metrics for the RPC server ([#3555](https://github.com/lablup/backend.ai/issues/3555))
* Add `status` Column to the `Image` table, and `ImageRow` unique constraint. ([#3619](https://github.com/lablup/backend.ai/issues/3619))
* Add `status` to `Image`, `ImageNode` GQL Fields. ([#3620](https://github.com/lablup/backend.ai/issues/3620))
* Update `ForgetImage`, `ForgetImageById`, `ClearImages` to perform soft delete and add `PurgeImageById` API for hard delete. ([#3628](https://github.com/lablup/backend.ai/issues/3628))
* Implement noop storage backend ([#3629](https://github.com/lablup/backend.ai/issues/3629))
* Assign the noop storage host to unmanaged vfolders ([#3630](https://github.com/lablup/backend.ai/issues/3630))
* Update vfolder CLI cmd to support unmanaged vfolders ([#3631](https://github.com/lablup/backend.ai/issues/3631))
* Implement `Image` status filtering logics. (e.g. adding an optional argument to the `Image`, `ImageNode` GQL resolvers to enable querying deleted images as well.) ([#3647](https://github.com/lablup/backend.ai/issues/3647))
* Add `enforce_spreading_endpoint_replica` scheduling option to the `ConcentratedAgentSelector`, which prioritizes availability over available resource slots when selecting an agent for inference sessions. ([#3693](https://github.com/lablup/backend.ai/issues/3693))
* Implement `PurgeImages` API for securing storage space on a specific agent. ([#3704](https://github.com/lablup/backend.ai/issues/3704))
* Add sum of resource slots field to scaling group schema ([#3707](https://github.com/lablup/backend.ai/issues/3707))
* Add `scaling_group_name` column to `resource_presets` table. ([#3718](https://github.com/lablup/backend.ai/issues/3718))
* Update resource preset APIs to support mapping a resource group ([#3719](https://github.com/lablup/backend.ai/issues/3719))
* Split redis config for each connection pool ([#3725](https://github.com/lablup/backend.ai/issues/3725))
* Register v2 volume handler to router in storage-proxy ([#3785](https://github.com/lablup/backend.ai/issues/3785))
* Support `application/vnd.oci.image.manifest.v1+json` type images. ([#3814](https://github.com/lablup/backend.ai/issues/3814))
* Add `enable_interactive_login_account_switch` webserver option to control the visibility of the "Sign in with a different account" button on the interactive login page ([#3835](https://github.com/lablup/backend.ai/issues/3835))
* Add centralized action processor design ([#3859](https://github.com/lablup/backend.ai/issues/3859))
* Export utilization metrics to Prometheus ([#3878](https://github.com/lablup/backend.ai/issues/3878))
* Add kernel bootstrap timeout config ([#3880](https://github.com/lablup/backend.ai/issues/3880))
* Add GQL exception and metric middleware ([#3891](https://github.com/lablup/backend.ai/issues/3891))
* Allow delegation of service ownership when purge user ([#3898](https://github.com/lablup/backend.ai/issues/3898))
* Add filter/order argument to GQL `resource_presets` query ([#3916](https://github.com/lablup/backend.ai/issues/3916))

### Fixes
* Fix failure of the whole image rescanning task when there is a misconfigured container registry. ([#3652](https://github.com/lablup/backend.ai/issues/3652))
* Insert default `domain_name` value to vfolders ([#3767](https://github.com/lablup/backend.ai/issues/3767))
* Let Auth API handler check all keypairs owned by user ([#3780](https://github.com/lablup/backend.ai/issues/3780))
* Fix `description` field in user update CLI command, ensuring it is properly omitted when not provided ([#3831](https://github.com/lablup/backend.ai/issues/3831))
* Add missing vfolder mount permission mapping in new RBAC implementation ([#3851](https://github.com/lablup/backend.ai/issues/3851))
* Aggregate multi-kernel session utilization in idle checker ([#3861](https://github.com/lablup/backend.ai/issues/3861))
* Fix rescan only the latest tag in `HarborRegistryV2`. ([#3871](https://github.com/lablup/backend.ai/issues/3871))
* Retry zmq socket connections from kernel ([#3880](https://github.com/lablup/backend.ai/issues/3880))
* Fix intermittent image rescan DB serialization error due to parallel DB access of `rescan_single_registry()` calls. ([#3883](https://github.com/lablup/backend.ai/issues/3883))
* GQL `vfolder_node` query does not resolve `permissions` field ([#3900](https://github.com/lablup/backend.ai/issues/3900))
* Fix GQL Agent `live_stat` resolver to properly parse UUID keys in JSON data as strings ([#3928](https://github.com/lablup/backend.ai/issues/3928))


## 25.3.3 (2025-02-27)

### Features
* Let endpoints with `PROVISIONING` routes deleted without manual session removal ([#3842](https://github.com/lablup/backend.ai/issues/3842))

### Fixes
* Fix `CreateNetwork` GQL mutation not working ([#3843](https://github.com/lablup/backend.ai/issues/3843))
* Fix `EndpointAutoScalingRuleNode` GQL query not working ([#3845](https://github.com/lablup/backend.ai/issues/3845))


## 25.3.2 (2025-02-26)

### Fixes
* Add `service_ports` field resolver to GQL ComputeSessionNode type ([#3782](https://github.com/lablup/backend.ai/issues/3782))
* Fix the GQL VirtualFolderNode resolver to accept a filter argument ([#3799](https://github.com/lablup/backend.ai/issues/3799))
* Fix wrong Python interpreter embedded in the installer scie builds ([#3810](https://github.com/lablup/backend.ai/issues/3810))
* Fix a DB migration script that fails when the system has a default domain with a name other than 'default' ([#3816](https://github.com/lablup/backend.ai/issues/3816))
* Use correct lock ID for schedulers and event producers ([#3817](https://github.com/lablup/backend.ai/issues/3817))
* Broken image rescanning on `HarborRegistry_v1` due to type error of credential value. ([#3821](https://github.com/lablup/backend.ai/issues/3821))
* Ensure that the scie build of install.config also includes the files in the folder and the yaml file. ([#3824](https://github.com/lablup/backend.ai/issues/3824))
* Fix wrong alembic migration scripts ([#3829](https://github.com/lablup/backend.ai/issues/3829))


## 25.3.1 (2025-02-21)

### Features
* Add New API Logging Aligned with Pydantic ([#3731](https://github.com/lablup/backend.ai/issues/3731))
* Configurable global lock lifetime ([#3774](https://github.com/lablup/backend.ai/issues/3774))
* Let metric observers catch base exceptions in event handlers ([#3779](https://github.com/lablup/backend.ai/issues/3779))

### Fixes
* Fix missing argument in Redis event dispatcher initializer ([#3773](https://github.com/lablup/backend.ai/issues/3773))
* Fix wrong Python interpreter versions included in the scie builds ([#3793](https://github.com/lablup/backend.ai/issues/3793))


## 25.3.0 (2025-02-19)

### Features
* Add project scope implementation to Image RBAC. ([#3035](https://github.com/lablup/backend.ai/issues/3035))
* Implement `ImageNode` GQL resolver based on RBAC. ([#3036](https://github.com/lablup/backend.ai/issues/3036))
* Implement `AssociationContainerRegistriesGroups` as m2m table of `container_registries`, and `groups`. ([#3065](https://github.com/lablup/backend.ai/issues/3065))
* Implement CRUD API for managing Harbor per-project Quota. ([#3090](https://github.com/lablup/backend.ai/issues/3090))
* Implement Image Rescanning using Harbor Webhook API. ([#3116](https://github.com/lablup/backend.ai/issues/3116))
* Create KVS Interface ([#3645](https://github.com/lablup/backend.ai/issues/3645))
* Add configurable setup for kernel initialization polling ([#3657](https://github.com/lablup/backend.ai/issues/3657))
* Add a `show_kernel_list` config to webserver to show/hide kernel list in the session detail panel.

  Add configs not specified in sample.toml ([#3671](https://github.com/lablup/backend.ai/issues/3671))
* Make security policy configurable ([#3680](https://github.com/lablup/backend.ai/issues/3680))
* Make CSP configurable ([#3682](https://github.com/lablup/backend.ai/issues/3682))
* Sort vfolder list fields in compute session GQL objects ([#3751](https://github.com/lablup/backend.ai/issues/3751))

### Improvements
* Add the skeleton interface of vfolder CRUD handlers in storage-proxy ([#3516](https://github.com/lablup/backend.ai/issues/3516))
* Apply pydantic handling decorator to VFolder APIs in storage-proxy ([#3565](https://github.com/lablup/backend.ai/issues/3565))
* Move abc.py and storage system modules to volumes package ([#3567](https://github.com/lablup/backend.ai/issues/3567))
* Extract list_volumes and get_volume into pool.py ([#3569](https://github.com/lablup/backend.ai/issues/3569))
* Add Service Layer to Avoid Direct Volume and Vfolder Operations in Storage-Proxy Handler ([#3588](https://github.com/lablup/backend.ai/issues/3588))
* Change Absolute Imports to Relative Imports in Storage-Proxy ([#3685](https://github.com/lablup/backend.ai/issues/3685))

### Fixes
* Revamp `ContainerRegistryNode` API. ([#3424](https://github.com/lablup/backend.ai/issues/3424))
* Change port numbers using ephemeral ports ([#3614](https://github.com/lablup/backend.ai/issues/3614))
* Handle cancel and timeout when creating kernels ([#3648](https://github.com/lablup/backend.ai/issues/3648))
* Correct the number of concurrent SFTP sessions queried from DB ([#3654](https://github.com/lablup/backend.ai/issues/3654))
* Increase Backend.AI Kernel's app startup timeout ([#3679](https://github.com/lablup/backend.ai/issues/3679))
* Fix ContainerRegistry per-project API misc bugs. ([#3701](https://github.com/lablup/backend.ai/issues/3701))
* Fix model service not removed when auto scaling rules are set ([#3711](https://github.com/lablup/backend.ai/issues/3711))
* Validate duplicate session names during compute session modification ([#3715](https://github.com/lablup/backend.ai/issues/3715))
* Revert tmux version upgrade from 3.4 to 3.5a due to compatibility issues on aarch64 architecture ([#3740](https://github.com/lablup/backend.ai/issues/3740))
* Fix compute session rename API handler to query DB correctly ([#3746](https://github.com/lablup/backend.ai/issues/3746))
* Suppress `SELECT statement has a cartesian product between FROM element(s) "endpoints" and FROM element "endpoint_auto_scaling_rules"` log ([#3747](https://github.com/lablup/backend.ai/issues/3747))


## 25.2.0 (2025-02-07)

### Features
* Update tmux version from 3.4 to 3.5a ([#3000](https://github.com/lablup/backend.ai/issues/3000))
* Enable per-user UID/GID set for containers via user creation and update GraphQL APIs ([#3352](https://github.com/lablup/backend.ai/issues/3352))
* Update SDK and CLI to support per-user UID/GID configuration ([#3361](https://github.com/lablup/backend.ai/issues/3361))
* Add timeout configuration for Docker image push ([#3412](https://github.com/lablup/backend.ai/issues/3412))
* Add configurable directory permission for vfolders to support mount vfolders on customized UID/GID containers ([#3510](https://github.com/lablup/backend.ai/issues/3510))
* Add new Pydantic handling api decorator for Request/Response validation ([#3511](https://github.com/lablup/backend.ai/issues/3511))
* Add force delete API for VFolder that bypasses the trash bin ([#3546](https://github.com/lablup/backend.ai/issues/3546))
* Add storage-watcher API to delete VFolders with elevated permissions ([#3548](https://github.com/lablup/backend.ai/issues/3548))

### Improvements
* Add skeleton vFolder handler Interface of manager ([#3493](https://github.com/lablup/backend.ai/issues/3493))

### Fixes
* Add reject middleware for web security ([#2937](https://github.com/lablup/backend.ai/issues/2937))
* Optimize the route selection in App Proxy using `random.choices()` based on the native C implementation in CPython ([#3199](https://github.com/lablup/backend.ai/issues/3199))
* Fix GQL `vfolder_mounts` field resolver of `compute_session` type ([#3461](https://github.com/lablup/backend.ai/issues/3461))
* Fix empty tag image scan error in docker registry. ([#3513](https://github.com/lablup/backend.ai/issues/3513))
* Fixed "permission denied" error by creating the `grafana-data` directory with 757 permissions ([#3570](https://github.com/lablup/backend.ai/issues/3570))
* Fix Broken CSS by allowing `unsafe-inline` content security policy. ([#3572](https://github.com/lablup/backend.ai/issues/3572))
* Updated route pattern to allow any path ending with "login/" for POST requests to `/pipeline/{path:.*login/$}` ([#3574](https://github.com/lablup/backend.ai/issues/3574))
* Fix vfolder delete SDK function to call 'delete by id' API rather than 'delete by name' API ([#3581](https://github.com/lablup/backend.ai/issues/3581))
* Check intrinsic time files exist before mount ([#3583](https://github.com/lablup/backend.ai/issues/3583))
* Fixed to ensure unique values in the mount list of the compute session ([#3593](https://github.com/lablup/backend.ai/issues/3593))
* The installer changes from downloading the checksum files for each package separately to receiving a consolidated checksum file and using them separately. ([#3597](https://github.com/lablup/backend.ai/issues/3597))
* Remove foreign key constraint from `EndpointRow.image` column. ([#3599](https://github.com/lablup/backend.ai/issues/3599))


## 25.1.1 (2025-01-20)
No significant changes.


## 25.1.0 (2025-01-20)

### Features
* Implement fine-grained seccomp profile managed by Backend.AI Agent. ([#3019](https://github.com/lablup/backend.ai/issues/3019))
* Enable image rescanning by project. ([#3237](https://github.com/lablup/backend.ai/issues/3237))
* Support auto-scaling of model services by observing proxy and app-specific metrics as configured by autoscaling rules bound to each endpoint ([#3277](https://github.com/lablup/backend.ai/issues/3277))
* Deprecate the JWT-based `X-BackendAI-SSO` header to reduce complexity in authentication process for the pipeline service ([#3353](https://github.com/lablup/backend.ai/issues/3353))
* Add Grafana and Prometheus to Docker Compose ([#3458](https://github.com/lablup/backend.ai/issues/3458))
* Integrate Pyroscope with Backend.AI ([#3459](https://github.com/lablup/backend.ai/issues/3459))
* Update SDK to retrieve and use IDs for VFolder API operations instead of names ([#3471](https://github.com/lablup/backend.ai/issues/3471))

### Fixes
* Refactor container registries' projects traversal logic of the image rescanning. ([#2979](https://github.com/lablup/backend.ai/issues/2979))
* Fix regression of outdated `vfolder` GQL resolver. ([#3047](https://github.com/lablup/backend.ai/issues/3047))
* Fix image without metadata label not working ([#3341](https://github.com/lablup/backend.ai/issues/3341))
* Enforce VFolder name length restriction through the API schema, not by the DB column constraint ([#3363](https://github.com/lablup/backend.ai/issues/3363))
* Fix password based SSH login not working on sessions based on certain images ([#3387](https://github.com/lablup/backend.ai/issues/3387))
* Fix purge API to allow deletion of owner-deleted VFolders by directly retrieving VFolders using the folder ID ([#3388](https://github.com/lablup/backend.ai/issues/3388))
* Fix certain customized images not being pushed to registry properly ([#3391](https://github.com/lablup/backend.ai/issues/3391))
* Fix formatting errors when logging exceptions raised from the current local process that did not pass our custom serialization step ([#3410](https://github.com/lablup/backend.ai/issues/3410))
* Fix scanning and loading container images with no labels at all (`null` in the image manifests) ([#3411](https://github.com/lablup/backend.ai/issues/3411))
* Fix missing CPU architecture name lookup in `LocalRegistry` to directly scan and load container images from the local Docker daemon in dev setups ([#3420](https://github.com/lablup/backend.ai/issues/3420))
* Utilization idle checker computes kernel resource usages correctly ([#3442](https://github.com/lablup/backend.ai/issues/3442))
* Filter vfolders by status before initiating a vfolder deletion task ([#3446](https://github.com/lablup/backend.ai/issues/3446))
* Fix a mis-implementation that has prevented using UUIDs to indicate an exact vfolder when invoking the vfolder REST API ([#3451](https://github.com/lablup/backend.ai/issues/3451))
* Fix the required state output logic in the openopi reference documentation correctly ([#3460](https://github.com/lablup/backend.ai/issues/3460))
* Raise exception if multiple VFolders exist in decorator ([#3465](https://github.com/lablup/backend.ai/issues/3465))

### Documentation Updates
* Deprecate non relay container registry GQL explicitly. ([#3231](https://github.com/lablup/backend.ai/issues/3231))

### Miscellaneous
* Upgrade pantsbuild from 2.21 to 2.23, replacing the scie plugin with the intrinsic pex's scie build support ([#3377](https://github.com/lablup/backend.ai/issues/3377))


## 24.12.1 (2025-01-04)

### Fixes
* Fix broken session CLI commands due to invalid initialization of `ComputeSession`. ([#3222](https://github.com/lablup/backend.ai/issues/3222))
* Fix a regression that modifying a model service endpoint's replica count always sets it to 1 regardless of the user input ([#3337](https://github.com/lablup/backend.ai/issues/3337))

### Miscellaneous
* Fix the commit message format when assigning the PR number to an anonymous news fragment ([#3309](https://github.com/lablup/backend.ai/issues/3309))


## 24.12.0 (2025-12-30)

### Breaking Changes
* Add `PREPARED` status for compute sessions and kernels to indicate completion of pre-creation tasks such as image pull ([#2647](https://github.com/lablup/backend.ai/issues/2647))
* Add new `CREATING` session status to represent container creation phase, and redefine `PREPARING` status to specifically indicate pre-container preparation phases ([#3114](https://github.com/lablup/backend.ai/issues/3114))

### Features
* Migrate container registry config storage from `Etcd` to `PostgreSQL` ([#1917](https://github.com/lablup/backend.ai/issues/1917))
* Add background task that reports manager DB status. ([#2566](https://github.com/lablup/backend.ai/issues/2566))
* Add manager DB stat API compatible with Prometheus. ([#2567](https://github.com/lablup/backend.ai/issues/2567))
* Allow regular users to assign agent manually if `hide-agent` configuration is disabled ([#2614](https://github.com/lablup/backend.ai/issues/2614))
* Implement ID-based client workflow to ContainerRegistry API. ([#2615](https://github.com/lablup/backend.ai/issues/2615))
* Rafactor Base ContainerRegistry's `scan_tag` and implement `MEDIA_TYPE_DOCKER_MANIFEST` type handling. ([#2620](https://github.com/lablup/backend.ai/issues/2620))
* Support GitHub Container Registry. ([#2621](https://github.com/lablup/backend.ai/issues/2621))
* Support GitLab Container Registry. ([#2622](https://github.com/lablup/backend.ai/issues/2622))
* Support AWS ECR Public Container Registry. ([#2623](https://github.com/lablup/backend.ai/issues/2623))
* Support AWS ECR Private Container Registry. ([#2624](https://github.com/lablup/backend.ai/issues/2624))
* Replace rescan command's `--local` flag with local container registry record. ([#2665](https://github.com/lablup/backend.ai/issues/2665))
* Add public API webapp to allow externel services to query insensitive metrics ([#2695](https://github.com/lablup/backend.ai/issues/2695))
* Add `project` column to the images table and refactoring `ImageRef` logic. ([#2707](https://github.com/lablup/backend.ai/issues/2707))
* Check if agent has the required image before creating compute kernels ([#2721](https://github.com/lablup/backend.ai/issues/2721))
* Introduce network feature ([#2726](https://github.com/lablup/backend.ai/issues/2726))
* Support docker image manifest v2 schema1. ([#2815](https://github.com/lablup/backend.ai/issues/2815))
* Support setting health check interval for model service. ([#2825](https://github.com/lablup/backend.ai/issues/2825))
* Add session status checker GQL mutation. ([#2836](https://github.com/lablup/backend.ai/issues/2836))
* Add `filter` and `order` parameters to Group GQL Relay API. ([#2863](https://github.com/lablup/backend.ai/issues/2863))
* Add GQL `agent` type and resolver ([#2873](https://github.com/lablup/backend.ai/issues/2873))
* Add `vast_use_auth_token` config to utilize VASTData API token optionally. ([#2901](https://github.com/lablup/backend.ai/issues/2901))
* Use a valid value for the `id` field in the GQL schema query resolver for `ContainerRegistry`. ([#2908](https://github.com/lablup/backend.ai/issues/2908))
* Add GQL Relay domain query schema and resolver ([#2934](https://github.com/lablup/backend.ai/issues/2934))
* Add `namespace`, `base_image_name`, `tags` and `version` fields to GQL image schema ([#2939](https://github.com/lablup/backend.ai/issues/2939))
* Allow container user to join extra Linux groups. ([#2944](https://github.com/lablup/backend.ai/issues/2944))
* Add filtering and ordering by `open_to_public` field in endpoint queries ([#2954](https://github.com/lablup/backend.ai/issues/2954))
* Hide FastTrack (`pipeline`) menu by default on installation by `install-dev.sh` script. ([#3010](https://github.com/lablup/backend.ai/issues/3010))
* Support batch session timeout. ([#3066](https://github.com/lablup/backend.ai/issues/3066))
* Add an `show_non_installed_images` option to show all images regardless of installation on environment select section in session/service launcher page. ([#3124](https://github.com/lablup/backend.ai/issues/3124))
* Allow destroying sessions in `PULLING` status for all users ([#3128](https://github.com/lablup/backend.ai/issues/3128))
* Show live stats from inference framework when supported ([#3133](https://github.com/lablup/backend.ai/issues/3133))
* Allow specifying a full shell script string in `start_command` of `model-definition.yaml` while preserving shell variable expansions to allow access to environment variables in service definitions ([#3248](https://github.com/lablup/backend.ai/issues/3248))
* Rename `endpoint.desired_session_count` to `endpoint.replicas` ([#3257](https://github.com/lablup/backend.ai/issues/3257))
* Add several commonly used GPU configuration environment variables defined in containers by default: `GPU_TYPE`, `GPU_COUNT`, `GPU_CONFIG`, `GPU_MODEL_NAME` and `TF_GPU_MEMORY_ALLOC` ([#3275](https://github.com/lablup/backend.ai/issues/3275))
* Populate `BACKEND_MODEL_NAME` environment variable automatically on inference session ([#3281](https://github.com/lablup/backend.ai/issues/3281))
* Fix container cleanup process failing with error `AttributeError: 'DockerKernel' object has no attribute 'network_driver'` ([#3286](https://github.com/lablup/backend.ai/issues/3286))

### Improvements
* Convert VFolder deletion from blocking response to event-driven pattern ([#3063](https://github.com/lablup/backend.ai/issues/3063))

### Fixes
* Explicitly wait for readiness of the Docker daemon and the compose stack before pouring database fixtures in `install-dev.sh` for when installing at the provisioning stage of Codespaces and integration tests in CI. ([#2378](https://github.com/lablup/backend.ai/issues/2378))
* Fix silent failure of `DockerAgent.push_image()`, `DockerAgent.pull_image()`. ([#2572](https://github.com/lablup/backend.ai/issues/2572))
* Fix missing notification of cancellation or failure of background tasks when shutting down the server ([#2579](https://github.com/lablup/backend.ai/issues/2579))
* Add missing implementation of wsproxy and manager CLI's log-level customization options ([#2698](https://github.com/lablup/backend.ai/issues/2698))
* Add missing batch execution call after session starts ([#2884](https://github.com/lablup/backend.ai/issues/2884))
* Fix a regression of the unicode-aware slug update that prevented creation of dot-prefixed (automount) vfolders ([#2892](https://github.com/lablup/backend.ai/issues/2892))
* Fix invalid image format log spam in Agent ([#2894](https://github.com/lablup/backend.ai/issues/2894))
* Fix wrong creation of `raw_configs` in `_create_kernels_in_one_agent` ([#2896](https://github.com/lablup/backend.ai/issues/2896))
* Disallow `None` id encoding in `AsyncNode.to_global_id()`. ([#2898](https://github.com/lablup/backend.ai/issues/2898))
* Assign valid value to `id` field in `ContainerRegistryNode` GQL schema query resolver. ([#2899](https://github.com/lablup/backend.ai/issues/2899))
* Update vast quota rather than raise error when quota exists. ([#2900](https://github.com/lablup/backend.ai/issues/2900))
* Calculate correct expiration time of VAST auth token and add `vast_force_login` config to enable login before every REST API call ([#2911](https://github.com/lablup/backend.ai/issues/2911))
* Update Dellemc OneFS storage backend to correctly initialize volume object and wrong http request arguments ([#2918](https://github.com/lablup/backend.ai/issues/2918))
* Fix `modify_endpoint()` mutation to handle empty `JSONString` properly for environment variables ([#2922](https://github.com/lablup/backend.ai/issues/2922))
* Fix `order` GQL query argument parser of `group_nodes` ([#2927](https://github.com/lablup/backend.ai/issues/2927))
* Set the `postgres_readonly` flag to `false` when begin generic sessions ([#2946](https://github.com/lablup/backend.ai/issues/2946))
* Fix wrong container registry migration script. ([#2949](https://github.com/lablup/backend.ai/issues/2949))
* Let GPFS client keep polling when GPFS job is running ([#2961](https://github.com/lablup/backend.ai/issues/2961))
* Handle `IndexError` when parse string to `BinarySize` ([#2962](https://github.com/lablup/backend.ai/issues/2962))
* Handle error when convert `shmem` string value into `BinarySize` ([#2972](https://github.com/lablup/backend.ai/issues/2972))
* Make image, container_registry table's `project` column nullable and improve container registry storage config migration script. ([#2978](https://github.com/lablup/backend.ai/issues/2978))
* Fix a wrong parameter when call 'recalc_agent_resource_occupancy()' ([#2982](https://github.com/lablup/backend.ai/issues/2982))
* Allow the `modify_compute_session` mutation works without `priority` field in input argument and let the mutation validates `name` value ([#2985](https://github.com/lablup/backend.ai/issues/2985))
* Fix wrong password limit in container registry migration script. ([#2986](https://github.com/lablup/backend.ai/issues/2986))
* Fix `architecture` condition not applied when query `images` rows ([#2989](https://github.com/lablup/backend.ai/issues/2989))
* Deprecate `project_id` GQL argument and add nullable `scope_id` GQL argument ([#2991](https://github.com/lablup/backend.ai/issues/2991))
* Strengthen join condition between kernels and images to prevent incorrect matches ([#2993](https://github.com/lablup/backend.ai/issues/2993))
* Enable session commit to different registry, project. ([#2997](https://github.com/lablup/backend.ai/issues/2997))
* Wrong field reference in `ImageNode` resolver ([#3002](https://github.com/lablup/backend.ai/issues/3002))
* Fix obsolete logic of `untag()` of `HarborRegistry_v2`. ([#3004](https://github.com/lablup/backend.ai/issues/3004))
* Fix `Agent.compute_containers` GraphQL field by adding missing resolver ([#3011](https://github.com/lablup/backend.ai/issues/3011))
* Fix `Agent` GQL Regression error. ([#3013](https://github.com/lablup/backend.ai/issues/3013))
* Fix `backend.ai apps` command's faulty argument handling logic. ([#3015](https://github.com/lablup/backend.ai/issues/3015))
* Check Vast data quota with a given name exists before creating quota and change default value of `force_login` config to true ([#3023](https://github.com/lablup/backend.ai/issues/3023))
* Fix model service traffics not distributed equally to every sessions when there are 10 or more replicas ([#3027](https://github.com/lablup/backend.ai/issues/3027))
* Fix the TUI installer to make the install path always visible ([#3029](https://github.com/lablup/backend.ai/issues/3029))
* Prevent redis password from being logged. ([#3031](https://github.com/lablup/backend.ai/issues/3031))
* Fix `get_logs_from_agent()` to raise `InstanceNotFound` exception for kernels not assigned to agents ([#3032](https://github.com/lablup/backend.ai/issues/3032))
* Fix regression of `ComputeContainer` GraphQL queries due to newly introduced relationship fields ([#3042](https://github.com/lablup/backend.ai/issues/3042))
* Fix regression of the `AgentSummary` resolver caused by an incorrect `batch_load_func` assignment. ([#3045](https://github.com/lablup/backend.ai/issues/3045))
* Fix regression of `LegacyComputeSession` GraphQL queries. ([#3046](https://github.com/lablup/backend.ai/issues/3046))
* Include missing legacy logging module in the pex. ([#3054](https://github.com/lablup/backend.ai/issues/3054))
* Change the name of deleted vfolders with a timestamp suffix when sending them to DELETE_ONGOING status to allow reuse of the vfolder name, for cases when actual deletion takes a long time ([#3061](https://github.com/lablup/backend.ai/issues/3061))
* Fix model service not routing traffics based on traffic ratio ([#3075](https://github.com/lablup/backend.ai/issues/3075))
* Fix the broken `ComputeContainer.batch_load_detail` due to the misuse of `selectinload` as follow-up to #3042 ([#3078](https://github.com/lablup/backend.ai/issues/3078))
* Fix session `status_info` not being updated correctly when batch executions fail, ensuring failed batch execution states are properly reflected in the sessions table ([#3085](https://github.com/lablup/backend.ai/issues/3085))
* agent not loading `krunner-extractor` image when Docker instance does not support loading XZ compressed images ([#3101](https://github.com/lablup/backend.ai/issues/3101))
* Fix outdated image string join logic in `ImageRow.image_ref`. ([#3125](https://github.com/lablup/backend.ai/issues/3125))
* Allow admins to delete other users' vfolders by enabling vfolder fetching for precondition checks ([#3137](https://github.com/lablup/backend.ai/issues/3137))
* Fix Libc version not detected on unlabeled images when image has custom entrypoint set ([#3173](https://github.com/lablup/backend.ai/issues/3173))
* Fix service not started when `[logging].rotation-size` config is set ([#3174](https://github.com/lablup/backend.ai/issues/3174))
* Allow purging vfolders by enabling name-based queries of deleted VFolders ([#3176](https://github.com/lablup/backend.ai/issues/3176))
* Fix the issue where the value of occupying slots abnormally multiplies when creating a compute session ([#3186](https://github.com/lablup/backend.ai/issues/3186))
* Add missing `extra` field to `ContainerRegistryNode` GQL query, mutations. ([#3208](https://github.com/lablup/backend.ai/issues/3208))
* Fix purge functionality that deletes VFolder records by allowing admins to query other users' VFolders ([#3223](https://github.com/lablup/backend.ai/issues/3223))
* Fix CLI test failures caused by `yarl.URL._val` type change. ([#3235](https://github.com/lablup/backend.ai/issues/3235))
* Prevent vfolder `request-download` API from accessing host filesystem. ([#3241](https://github.com/lablup/backend.ai/issues/3241))
* Fix `1d42c726d8a3` revision execution failing ([#3254](https://github.com/lablup/backend.ai/issues/3254))
* Ensure the string formatting of BinarySize values containing subtle fractions to be floating point numbers (instead of scientific notations) always ([#3272](https://github.com/lablup/backend.ai/issues/3272))
* Fix invalid API version checks in the session creation API of Manager. ([#3291](https://github.com/lablup/backend.ai/issues/3291))

### Documentation Updates
* Update the package installation documentation to include instructions on adding the manager's RPC key pair. ([#2052](https://github.com/lablup/backend.ai/issues/2052))

### Miscellaneous
* Upgrade the base CPython version from 3.12.6 to 3.12.8 ([#3302](https://github.com/lablup/backend.ai/issues/3302))


## 24.09.0b1 (2024-09-30)

### Features
* Add support for optional payload encryption in the client SDK and CLI as a follow-up to #484 ([#493](https://github.com/lablup/backend.ai/issues/493))
* Allow unicode characters in project(user group) name and domain name. ([#1663](https://github.com/lablup/backend.ai/issues/1663))
* Improve exception logging stability by pre-formatting exception objects instead of pickling/unpickling them ([#1759](https://github.com/lablup/backend.ai/issues/1759))
* Add new API to create new image from live session ([#1973](https://github.com/lablup/backend.ai/issues/1973))
* Clear `error_logs` records in the `clear-history` command ([#1989](https://github.com/lablup/backend.ai/issues/1989))
* Introduce `mgr schema dump-history` and `mgr schema apply-missing-revisions` command to ease the major upgrade involving deviation of database migration histories ([#2002](https://github.com/lablup/backend.ai/issues/2002))
* Update `image forget` CLI command to untag image from registry before forgetting it from the database ([#2010](https://github.com/lablup/backend.ai/issues/2010))
* Update `etcd-client-py` to 0.3.0 ([#2014](https://github.com/lablup/backend.ai/issues/2014))
* Allow self-ssh in single-node single-container compute sessions. ([#2032](https://github.com/lablup/backend.ai/issues/2032))
* Prevent deleting mounted folders. ([#2036](https://github.com/lablup/backend.ai/issues/2036))
* Allow agent to report its internal registry snapshot via UNIX domain socket server ([#2038](https://github.com/lablup/backend.ai/issues/2038))
* New redis client (experimental) ([#2041](https://github.com/lablup/backend.ai/issues/2041))
* Expose user info to environment variables ([#2043](https://github.com/lablup/backend.ai/issues/2043))
* Introduce the `rolling_count` GraphQL field to provide the current rate limit counter for a keypair within the designated time window slice ([#2050](https://github.com/lablup/backend.ai/issues/2050))
* Deprecate the reliance on HTTP cookies for authenticating the pipeline service, switching to the use of HTTP headers instead ([#2051](https://github.com/lablup/backend.ai/issues/2051))
* Allow user to explicitly set filename of model definition YAML ([#2063](https://github.com/lablup/backend.ai/issues/2063))
* Add the `backend.ai plugin scan` command to inspect the plugin scan results from various entrypoint sources ([#2070](https://github.com/lablup/backend.ai/issues/2070))
* Bring back etcetra-backed Etcd as an option for ditributed lock backend ([#2079](https://github.com/lablup/backend.ai/issues/2079))
* Enable distribute-lock configuration ([#2080](https://github.com/lablup/backend.ai/issues/2080))
* Cache volume objects in `RootContext.get_volume` ([#2081](https://github.com/lablup/backend.ai/issues/2081))
* Revamp images GQL query by changing image filtering from flag-based to feature set-based and add `aliases` field to customized image GQL schema ([#2136](https://github.com/lablup/backend.ai/issues/2136))
* Added missing fields for `keypair_resource_policy` in client-py, models, etc. ([#2146](https://github.com/lablup/backend.ai/issues/2146))
* Add parameters to `check-presets` SDK function ([#2153](https://github.com/lablup/backend.ai/issues/2153))
* Add relay-aware `VirtualFolderNode` GQL Query ([#2165](https://github.com/lablup/backend.ai/issues/2165))
* Also perform basic model service validation process when updating model service via `ModifyEndpoint` ([#2167](https://github.com/lablup/backend.ai/issues/2167))
* Add support for mounting arbitrary VFolders on model service session ([#2168](https://github.com/lablup/backend.ai/issues/2168))
* Add support for CentOS 8 based kernels ([#2220](https://github.com/lablup/backend.ai/issues/2220))
* Clear zombie routes automatically ([#2229](https://github.com/lablup/backend.ai/issues/2229))
* Add `scaling_group.agent_count_by_status` and `scaling_group.agent_total_resource_slots_by_status` GQL fields to query the count and the resource allocation of agents that belong to a scaling group. ([#2254](https://github.com/lablup/backend.ai/issues/2254))
* Allow modifying model service session's environment variable setup ([#2255](https://github.com/lablup/backend.ai/issues/2255))
* Add `endpoint.runtime_variant` column ([#2256](https://github.com/lablup/backend.ai/issues/2256))
* Add new API to show list of supported inference runtimes ([#2258](https://github.com/lablup/backend.ai/issues/2258))
* Add support for model service provisioning without `model-definition.yaml` ([#2260](https://github.com/lablup/backend.ai/issues/2260))
* Allow superadmins to force-update session status through destroy API. ([#2275](https://github.com/lablup/backend.ai/issues/2275))
* Add session status check & update API. ([#2312](https://github.com/lablup/backend.ai/issues/2312))
* Add support for fetching container logs of a specific kernel. ([#2364](https://github.com/lablup/backend.ai/issues/2364))
* Introduce Python native WSProxy ([#2372](https://github.com/lablup/backend.ai/issues/2372))
* Implement scanning plugin entrypoints of external packages ([#2377](https://github.com/lablup/backend.ai/issues/2377))
* Add `row_id`, `type` and `container_registry` fields to the `GroupNode` GQL schema. ([#2409](https://github.com/lablup/backend.ai/issues/2409))
* Add support for PureStorage RapidFiles Toolkit v2 ([#2419](https://github.com/lablup/backend.ai/issues/2419))
* Add API that extends lifespan of webserver's login session. ([#2456](https://github.com/lablup/backend.ai/issues/2456))
* Allow bulk association and disassociation of scaling groups with domains, user groups, and key pairs. ([#2473](https://github.com/lablup/backend.ai/issues/2473))
* Match container's timezone to container host OS when available ([#2503](https://github.com/lablup/backend.ai/issues/2503))
* Add a pre-setup configuration menu to the TUI installer to allow setting the public-facing address of Backend.AI components ([#2541](https://github.com/lablup/backend.ai/issues/2541))
* Now Backend.AI can run arbitrary container images without Backend.AI-specific metadata labels by introducing good default values and replacing intrinsic kernel-runner binaries with statically built ones ([#2582](https://github.com/lablup/backend.ai/issues/2582))
* Allow `Bearer` as valid token type on model service authentication ([#2583](https://github.com/lablup/backend.ai/issues/2583))
* Introduce automatic creation of a 'model-store' group upon inserting a new domain. ([#2611](https://github.com/lablup/backend.ai/issues/2611))
* Add support for declaring custom description field for GraphQL `relay` edge types. ([#2643](https://github.com/lablup/backend.ai/issues/2643))
* Add an `enable_LLM_playground` option to show/hide the LLM playground tab on the serving page. ([#2677](https://github.com/lablup/backend.ai/issues/2677))
* Add `max_gaudi2_devices_per_container` config on webserver ([#2685](https://github.com/lablup/backend.ai/issues/2685))
* Add `max_atom_plus_device_per_container` config on webserver ([#2686](https://github.com/lablup/backend.ai/issues/2686))
* Introduce Account-manager component. ([#2688](https://github.com/lablup/backend.ai/issues/2688))
* * Add query depth limit config of GQL.
  * Add page size limit config of GQL Connection.
  * Set default page size of GQL Connection to 10. ([#2709](https://github.com/lablup/backend.ai/issues/2709))
* Add compute session GQL Relay query schema. ([#2711](https://github.com/lablup/backend.ai/issues/2711))
* Allow `DataLoaderManager` to get a loader function by function itself rather than function name. ([#2717](https://github.com/lablup/backend.ai/issues/2717))
* Allow filter and order in endpointlist gql request. ([#2723](https://github.com/lablup/backend.ai/issues/2723))
* Add new vfolder API to update sharing status. ([#2740](https://github.com/lablup/backend.ai/issues/2740))
* Avoid raising a type error even if a particular table in the toml file is empty, as long as the default value for all settings exists. ([#2782](https://github.com/lablup/backend.ai/issues/2782))
* Add an explicit configuration `scaling-group-type` to `agent.toml` so that the agent could distinguish whether itself belongs to an SFTP resource group or not ([#2796](https://github.com/lablup/backend.ai/issues/2796))
* Add per-session priority attributes and `ModifyComputeSession` GraphQL mutation to update session names and priorities ([#2840](https://github.com/lablup/backend.ai/issues/2840))
* Add dependee/dependent/graph ComputeSessionNode connection queries ([#2844](https://github.com/lablup/backend.ai/issues/2844))
* Implement the priority-aware scheduler that applies to any arbitrary scheduler plugin ([#2848](https://github.com/lablup/backend.ai/issues/2848))
* Add support for setting a timeout when pulling Docker images and upgrade aiodocker to version 0.23.0. ([#2852](https://github.com/lablup/backend.ai/issues/2852))

### Improvements
* Enable robust DB connection handling by allowing `pool-pre-ping` setting. ([#1991](https://github.com/lablup/backend.ai/issues/1991))
* Enhance update mechanism of session & kernel status. ([#2311](https://github.com/lablup/backend.ai/issues/2311))
* Remove database-level foreign key constraints in `vfolders.{user,group}` columns to decouple the timing of vfolder deletion and user/group deletion. ([#2404](https://github.com/lablup/backend.ai/issues/2404))
* Implement storage-host RBAC interface. ([#2505](https://github.com/lablup/backend.ai/issues/2505))
* Optimize the query latency when fetching a large number of agents with stat metrics from Redis ([#2558](https://github.com/lablup/backend.ai/issues/2558))
* Split out `ai.backend.logging` package from the `ai.backend.common` to improve reusability and reduce the startup time (i.e., import latencies) ([#2760](https://github.com/lablup/backend.ai/issues/2760))
* Avoid using `collections.OrderedDict` when not necessary in the manager API and client SDK ([#2842](https://github.com/lablup/backend.ai/issues/2842))

### Deprecations
* Remove no longer used `env-tester-{admin,user,user2}.sh` scripts and all references ([#1956](https://github.com/lablup/backend.ai/issues/1956))

### Fixes
* Merge `kernels.role` into `sessions.session_type` and check the image compatibility based on comparison with the `ai.backend.role` label ([#1587](https://github.com/lablup/backend.ai/issues/1587))
* Refactor `PendingSession` Scheduler into `PendingSession` scheduler and `AgentSelector`, and replace `roundrobin` flag with `AgentSelectionStrategy.RoundRobin` policy. ([#1655](https://github.com/lablup/backend.ai/issues/1655))
* Do not omit to update session's occupying resources to DB when a kernel starts. ([#1832](https://github.com/lablup/backend.ai/issues/1832))
* Fix DDN command output handling when exceeding quotas. ([#1901](https://github.com/lablup/backend.ai/issues/1901))
* Explicitly specify the storage-side UID/GID when creating qtrees in the NetApp storage backend ([#1983](https://github.com/lablup/backend.ai/issues/1983))
* Sync mismatch between `kernels.session_name` and `sessions.name` and fix session-rename API to update `session_name` of sibling kernels atomically. ([#1985](https://github.com/lablup/backend.ai/issues/1985))
* Change function default arguments from mutable object to `None`. ([#1986](https://github.com/lablup/backend.ai/issues/1986))
* Revert some VFolder APIs response type to remove mismatch between `Content-Type` header and body. ([#1988](https://github.com/lablup/backend.ai/issues/1988))
* Upgrade pants to 2.21.0.dev4 for Python 3.12 support in their embedded pex/pip versions ([#1998](https://github.com/lablup/backend.ai/issues/1998))
* Fix Graylog log adapter not working after upgrading to Python 3.12 ([#1999](https://github.com/lablup/backend.ai/issues/1999))
* Fix `compute_container` GraphQL query resolver functions. ([#2012](https://github.com/lablup/backend.ai/issues/2012))
* Fix harbor v2 image scanner skipping importing rest of the artifacts when any of the item does not include tag ([#2015](https://github.com/lablup/backend.ai/issues/2015))
* Let external log viewers display more accurate, meaningful stack frames of logger invocations. ([#2019](https://github.com/lablup/backend.ai/issues/2019))
* Fix handling of undefined values in the ModifyImage GraphQL mutation. ([#2028](https://github.com/lablup/backend.ai/issues/2028))
* Fix container commit not working on certain docker engine versions ([#2040](https://github.com/lablup/backend.ai/issues/2040))
* add omitted request fetching from client to manager about deleting vfolder in trash bin. ([#2042](https://github.com/lablup/backend.ai/issues/2042))
* Fix a buggy restriction on VFolder deletion due to wrong query condition ([#2055](https://github.com/lablup/backend.ai/issues/2055))
* Fix wrong usage of dataloader in GQL group resolver. ([#2056](https://github.com/lablup/backend.ai/issues/2056))
* Ensure that vfolders, including automount vfolders, are mounted during session creation only if their status is not set to "DEAD" (i.e., deleted). ([#2059](https://github.com/lablup/backend.ai/issues/2059))
* Fix wrong calculation of resource usage ([#2062](https://github.com/lablup/backend.ai/issues/2062))
* Fix VFolder file operation not working when user has been granted access to shared but deleted VFolder which has same name with the normal one ([#2072](https://github.com/lablup/backend.ai/issues/2072))
* Add missing type argument in group query ([#2073](https://github.com/lablup/backend.ai/issues/2073))
* Let the `backend.ai mgr clear-history` command clears session records as well as kernel records ([#2077](https://github.com/lablup/backend.ai/issues/2077))
* Fix `compute_session_list` GQL query not responding on an abundant amount of sessions ([#2084](https://github.com/lablup/backend.ai/issues/2084))
* Fix VFolder invitation not accepted when inviting VFolder shares name with already deleted one ([#2093](https://github.com/lablup/backend.ai/issues/2093))
* Fix orphan model service routes being created ([#2096](https://github.com/lablup/backend.ai/issues/2096))
* Fix initialization of the resource usage API's kernel-level usage aggregation ([#2102](https://github.com/lablup/backend.ai/issues/2102))
* Fix model server starting on every kernels (including sub role kernels) on multi container infernce session ([#2124](https://github.com/lablup/backend.ai/issues/2124))
* Add missing `commit_session_to_file` to `OP_EXC` ([#2127](https://github.com/lablup/backend.ai/issues/2127))
* Fix wrong SQL query build for GQL Relay node ([#2128](https://github.com/lablup/backend.ai/issues/2128))
* Pass ImageRef.canonical in `commit_session_to_file` ([#2134](https://github.com/lablup/backend.ai/issues/2134))
* Handle fileset-already-exists response of `create-filset` API request and make sure to wait between all GPFS job polling iterations ([#2144](https://github.com/lablup/backend.ai/issues/2144))
* Skip any possible redundant quota update requests when creating new quota ([#2145](https://github.com/lablup/backend.ai/issues/2145))
* * Fix error when calling `check_presets` Client SDK API with an invalid `group` parameter 
  * Rewrite Client SDK to access all APIConfig fields ([#2152](https://github.com/lablup/backend.ai/issues/2152))
* Ensure that all pending sessions are picked by schedulers ([#2155](https://github.com/lablup/backend.ai/issues/2155))
* Fix user creation error when any model-store does not exists. ([#2160](https://github.com/lablup/backend.ai/issues/2160))
* Fix buggy resolver of `model_card` GQL Query. ([#2161](https://github.com/lablup/backend.ai/issues/2161))
* Fix security vulnerability for `sudo_session_enabled` ([#2162](https://github.com/lablup/backend.ai/issues/2162))
* Rename `endpoints.model_mount_destiation` to `model_mount_destination` ([#2163](https://github.com/lablup/backend.ai/issues/2163))
* Wait for real quota scope directory creation after Netapp `create_qtree()` call ([#2170](https://github.com/lablup/backend.ai/issues/2170))
* Fix wrong per-user concurrency calculation logic ([#2175](https://github.com/lablup/backend.ai/issues/2175))
* Keep `sync_container_lifecycles()` bgtask alive in a loop. ([#2178](https://github.com/lablup/backend.ai/issues/2178))
* Fix missing check for group (project) vfolder count limit and error handling with an invalid `group` parameter ([#2190](https://github.com/lablup/backend.ai/issues/2190))
* Fix model service persisting on `degraded` status forever in rare chance when trying to delete the service ([#2191](https://github.com/lablup/backend.ai/issues/2191))
* Fix error when query or mutate GraphQL using `BigInt` field type ([#2203](https://github.com/lablup/backend.ai/issues/2203))
* Ensure that utilization idleness is checked after a set period. ([#2205](https://github.com/lablup/backend.ai/issues/2205))
* Fix `backend.ai ssh` command execution when packaged as SCIE/PEX ([#2226](https://github.com/lablup/backend.ai/issues/2226))
* * fix `endpoints` query not working when trying to load `image_row.aliases`
  * fix `endpoints.status` reporting `PROVISIONING` when its status is in `DESTROYING` state ([#2233](https://github.com/lablup/backend.ai/issues/2233))
* Fix GQL raising error when trying to resolve `endpoints.errors` field occasionally ([#2236](https://github.com/lablup/backend.ai/issues/2236))
* Fix `ZeroDivisionError` in volume usage calculation by returning 0% when volume capacity is zero ([#2245](https://github.com/lablup/backend.ai/issues/2245))
* Fix GraphQL to support query to non-installed images ([#2250](https://github.com/lablup/backend.ai/issues/2250))
* Add missing `push_image` method implementation to Dummy Agent ([#2253](https://github.com/lablup/backend.ai/issues/2253))
* Rename no-op `access_key` parameter of `endpoint_list` GQL Query to `user_uuid` ([#2287](https://github.com/lablup/backend.ai/issues/2287))
* Fix `ai.backend.service-ports` label syntax broken when image does not expose built-in service port ([#2288](https://github.com/lablup/backend.ai/issues/2288))
* Improve stability of `untag_image_from_registry` mutation ([#2289](https://github.com/lablup/backend.ai/issues/2289))
* SSH not working between kernels started with customized image ([#2290](https://github.com/lablup/backend.ai/issues/2290))
* Invalid container memory capacity reported ([#2291](https://github.com/lablup/backend.ai/issues/2291))
* Corrected an issue where the `resource_policy` field in the user model was incorrectly mapped to `domain_name`. ([#2314](https://github.com/lablup/backend.ai/issues/2314))
* Omit to clean containerless kernels which are still creating its container. ([#2317](https://github.com/lablup/backend.ai/issues/2317))
* Fix model service sessions created before 24.03.5 failing to spawn ([#2318](https://github.com/lablup/backend.ai/issues/2318))
* Image commit not working ([#2319](https://github.com/lablup/backend.ai/issues/2319))
* model service session scheduler (`scale_services()`) failing when sessions bound to active route already marked as terminated ([#2320](https://github.com/lablup/backend.ai/issues/2320))
* Fix container metric collection halted on systems with Cgroups v1 ([#2321](https://github.com/lablup/backend.ai/issues/2321))
* Run batch execution after the batch session starts. ([#2327](https://github.com/lablup/backend.ai/issues/2327))
* Add support for configuring `sync_container_lifecycles()` task. ([#2338](https://github.com/lablup/backend.ai/issues/2338))
* Fix mismatches between responses of `/services/_runtimes` and new model service creation input ([#2371](https://github.com/lablup/backend.ai/issues/2371))
* Fix incorrect check of values returned from docker stat API. ([#2389](https://github.com/lablup/backend.ai/issues/2389))
* Shutdown agent properly by removing a code that waits a cancelled task. ([#2392](https://github.com/lablup/backend.ai/issues/2392))
* Restrict GraphQL query to `user_nodes` field to require `superadmin` privilege ([#2401](https://github.com/lablup/backend.ai/issues/2401))
* Handle all possible exceptions when scheduling single node session so that the status information of pending session is not empty. ([#2411](https://github.com/lablup/backend.ai/issues/2411))
* Utilize `ExtendedJSONEncoder` for error logging to handle `UUID` objects in `extra_data` ([#2415](https://github.com/lablup/backend.ai/issues/2415))
* Change outdated references in event module from `kernels` to `sessions`. ([#2421](https://github.com/lablup/backend.ai/issues/2421))
* Upgrade `inquirer` to remove dependency on deprecated `distutils`, which breaks up execution of the scie builds ([#2424](https://github.com/lablup/backend.ai/issues/2424))
* Allow specific status of vfolders to query to purge. ([#2429](https://github.com/lablup/backend.ai/issues/2429))
* Update the install-dev scripts to use `pnpm` instead of `npm` to speed up installation and resolve some peculiar version resolution issues related to esbuild. ([#2436](https://github.com/lablup/backend.ai/issues/2436))
* Fix a packaging issue in the `backendai-webserver` scie executable due to missing explicit requirement of setuptools ([#2454](https://github.com/lablup/backend.ai/issues/2454))
* Improve pruning of non-physical filesystems when measuring disk usage in agents ([#2460](https://github.com/lablup/backend.ai/issues/2460))
* Update the install-dev scripts to install `pnpm` if pnpm isn't installed. ([#2472](https://github.com/lablup/backend.ai/issues/2472))
* Improve error handling of initialization failures in the kernel runner ([#2478](https://github.com/lablup/backend.ai/issues/2478))
* Fix `BACKEND_MODEL_NAME` environment always overwritten to model name specified at model definition ([#2481](https://github.com/lablup/backend.ai/issues/2481))
* Do not allow assigning preopen port which collides with image's own service port definition ([#2482](https://github.com/lablup/backend.ai/issues/2482))
* Fix GET requests with queryparams defined in API spec occasionally throwing 400 Bad Request error ([#2483](https://github.com/lablup/backend.ai/issues/2483))
* Check null value of user mutation by `Undefined` sentinel value rather than `None`. ([#2506](https://github.com/lablup/backend.ai/issues/2506))
* Do null check on `groups.total_resource_slots` and `domains.total_resource_slots` value. ([#2509](https://github.com/lablup/backend.ai/issues/2509))
* Fix hearbeat processing failing when agent reports image with its name not compilant to Backend.AI's naming rule ([#2516](https://github.com/lablup/backend.ai/issues/2516))
* Corrected a typo (`maanger` corrected to `manager`) in the `check_status()` API response of the storage component ([#2523](https://github.com/lablup/backend.ai/issues/2523))
* Rename `images.image_filters` GQL Query argument to `images.image_types` ([#2555](https://github.com/lablup/backend.ai/issues/2555))
* Prevent session status from being transit to `PULLING` status event if image pull is not required ([#2556](https://github.com/lablup/backend.ai/issues/2556))
* Prevent other user's customized image from being listed as a response of `images` GQL query ([#2557](https://github.com/lablup/backend.ai/issues/2557))
* skip resolving malformed `ModelCard` GQL item ([#2570](https://github.com/lablup/backend.ai/issues/2570))
* Delete sessions DB records when purging project. ([#2573](https://github.com/lablup/backend.ai/issues/2573))
* Initialize Redis connection pool objects with specified connection opts rather than ignoring them. ([#2574](https://github.com/lablup/backend.ai/issues/2574))
* Fix `GET /func/folders/{folderName}` API returning string literal `"null"` instead of null value on `user` and `group` fields ([#2584](https://github.com/lablup/backend.ai/issues/2584))
* Update `GQLPrivilegeCheckMiddleware` to align with upstream changes on `graphql-core` package ([#2598](https://github.com/lablup/backend.ai/issues/2598))
* Robust type check when idle checker fetches utilization data. ([#2601](https://github.com/lablup/backend.ai/issues/2601))
* Skip mounting zero-byte lxcfs files when lxcfs is activated to prevent crashes in session containers ([#2604](https://github.com/lablup/backend.ai/issues/2604))
* Fix typo in minilang query field spec and column map. ([#2605](https://github.com/lablup/backend.ai/issues/2605))
* Remove duplicate CPU quota arguments when creating containers ([#2608](https://github.com/lablup/backend.ai/issues/2608))
* Increase `MAX_CMD_LEN` of dropbear to improve compatibility with PyCharm debugger ([#2613](https://github.com/lablup/backend.ai/issues/2613))
* Silence falsy Redis timeout warnings when retrying blocking commands if the timeout does not exceed the expected command timeout ([#2632](https://github.com/lablup/backend.ai/issues/2632))
* Fix a regression of #2483 in the session-download API used by the `backend.ai ssh` command ([#2635](https://github.com/lablup/backend.ai/issues/2635))
* Implement missing `StrEnumType` handling in `populate_fixture()`. ([#2648](https://github.com/lablup/backend.ai/issues/2648))
* Let `GET /resource/usage/period` request contain data in query parameter rather than JSON body. ([#2661](https://github.com/lablup/backend.ai/issues/2661))
* Allow sudo-enabled container users to ovewrite `/usr/bin/scp` and `/usr/libexec/sftp-server` by unifying the intrinsic ssh binaries to use the merged `dropbearmulti` executable. ([#2667](https://github.com/lablup/backend.ai/issues/2667))
* Update `webserver` logout API to respond with HTTP 200 OK ([#2681](https://github.com/lablup/backend.ai/issues/2681))
* Fix WSProxy not properly handling WebSocket request sent from Firefox ([#2684](https://github.com/lablup/backend.ai/issues/2684))
* Scan parent directory of created qtree to avoid creating quota on non-existing directory. ([#2696](https://github.com/lablup/backend.ai/issues/2696))
* Fix `list_files`, `get_fstab_contents`, `get_performance_metric` and `shared_vfolder_info` Python SDK function not working with `ValidationError` exception printed ([#2706](https://github.com/lablup/backend.ai/issues/2706))
* Resolve the issue where the vfolder id does not match in `list_shared_vfolders`. ([#2731](https://github.com/lablup/backend.ai/issues/2731))
* Handle OS Error when deleting vfolders. ([#2741](https://github.com/lablup/backend.ai/issues/2741))
* Fix typo in Virtual-folder status update code. ([#2742](https://github.com/lablup/backend.ai/issues/2742))
* Correct `msgpack` deserialization of `ResourceSlot`. ([#2754](https://github.com/lablup/backend.ai/issues/2754))
* Fix regression error of `session create_from_template` command. ([#2761](https://github.com/lablup/backend.ai/issues/2761))
* Silence `model_` namespace warnings with pydantic-based model classes ([#2765](https://github.com/lablup/backend.ai/issues/2765))
* Change the initialization order of PackageContext to apply `target_path` correctly in the TUI installer ([#2768](https://github.com/lablup/backend.ai/issues/2768))
* Make the regex patterns to update configuration files working with multiline texts correctly in the TUI installer ([#2771](https://github.com/lablup/backend.ai/issues/2771))
* Omit null parameter when call `usage-per-period` API. ([#2777](https://github.com/lablup/backend.ai/issues/2777))
* Delete vfolder invitation and permission rows when deleting vfolders. ([#2780](https://github.com/lablup/backend.ai/issues/2780))
* Handle container port mismatch when creating kernel. ([#2786](https://github.com/lablup/backend.ai/issues/2786))
* Explicitly set the protected service ports depending on the resource group type and the service types ([#2797](https://github.com/lablup/backend.ai/issues/2797))
* Correct session status determiner function. ([#2803](https://github.com/lablup/backend.ai/issues/2803))
* Fix `endpoint_list.total_count` GQL field returning incorrect value ([#2805](https://github.com/lablup/backend.ai/issues/2805))
* Fix `Service.create()` SDK method and `service create` CLI command not working with `UnboundLocalError` exception ([#2806](https://github.com/lablup/backend.ai/issues/2806))
* Refresh expiration time of login session when login. ([#2816](https://github.com/lablup/backend.ai/issues/2816))
* Fix `kernel_id` assignment for main kernel log retrieval ([#2820](https://github.com/lablup/backend.ai/issues/2820))
* Use a safer TLS version (v1.2) when creating SSL sockets in the logstash handler ([#2827](https://github.com/lablup/backend.ai/issues/2827))
* Wrong count of concurrent compute sessions. ([#2829](https://github.com/lablup/backend.ai/issues/2829))
* Create kernels with correct `scaling_group` value. ([#2837](https://github.com/lablup/backend.ai/issues/2837))
* Fix a regression in progress bar rendering of the TUI installer after upgrading the Textual library ([#2867](https://github.com/lablup/backend.ai/issues/2867))

### Documentation Updates
* Add note about installing client library with same version as server ([#1976](https://github.com/lablup/backend.ai/issues/1976))
* Remove deprecated `version` from the docker compose YAML templates in package installation docs. ([#2035](https://github.com/lablup/backend.ai/issues/2035))
* Fix a typo in the `agent.toml` example of the package-based installation guide to have a duplicate double quote ([#2069](https://github.com/lablup/backend.ai/issues/2069))

### External Dependency Updates
* Upgrade the base runtime (CPython) version from 3.11.6 to 3.12.2 ([#1994](https://github.com/lablup/backend.ai/issues/1994))
* Upgrade aiodocker to v0.22.0 with minor bug fixes found by improved type annotations ([#2339](https://github.com/lablup/backend.ai/issues/2339))
* Update the halfstack containers to point the latest stable versions ([#2367](https://github.com/lablup/backend.ai/issues/2367))
* Upgrade aiodocker to 0.22.1 to fix error handling when trying to extract the log of non-existing containers ([#2402](https://github.com/lablup/backend.ai/issues/2402))
* Upgrade the base CPython from 3.12.2 to 3.12.4 ([#2449](https://github.com/lablup/backend.ai/issues/2449))
* Upgrade Python (3.12.4 -> 3.12.6) and common/tool dependencies to prepare for Python 3.13 and apply latest fixes ([#2851](https://github.com/lablup/backend.ai/issues/2851))

### Miscellaneous
* Wrap RPC authentication error to custom error for better logging. ([#1970](https://github.com/lablup/backend.ai/issues/1970))
* Add `requested_slots` field to compute session GQL type. ([#1984](https://github.com/lablup/backend.ai/issues/1984))
* Allow `pydantic.BaseModel` as the API handler return schema. ([#1987](https://github.com/lablup/backend.ai/issues/1987))
* Fix incorrect version notation of GQL Field. ([#1993](https://github.com/lablup/backend.ai/issues/1993))
* Add max_pending_session_count field to Keypair resource policy GQL schema ([#2013](https://github.com/lablup/backend.ai/issues/2013))
* Handle container creation exception and start exception in separate try-except contexts. ([#2316](https://github.com/lablup/backend.ai/issues/2316))
* Fix broken the workflow call for the action that auto-assigns PR numbers to news fragments ([#2358](https://github.com/lablup/backend.ai/issues/2358))
* Finally stabilize the hanging tests in our CI due to docker-internal races on TCP port mappings to concurrently spawned fixture containers by introducing monotonically increasing TCP port numbers ([#2379](https://github.com/lablup/backend.ai/issues/2379))
* Further improve the monotonic port allocation logic for the test containers to remove maximum concurrency restrictions ([#2396](https://github.com/lablup/backend.ai/issues/2396))
* Add PEX, SCIE binary build configs for the plugin subsystem. ([#2422](https://github.com/lablup/backend.ai/issues/2422))
* * Add POST `/folders` API endpoints to replace DELETE APIs that require request body.
  * Allow `DELETE` requests to have body data. ([#2571](https://github.com/lablup/backend.ai/issues/2571))
* Enhacne type hints for potential `None` arguments ([#2580](https://github.com/lablup/backend.ai/issues/2580))
* Add `ai.backend.manager.models.graphql` module for better code base management. ([#2669](https://github.com/lablup/backend.ai/issues/2669))
* Remove Scheduler related types that are no longer used. ([#2705](https://github.com/lablup/backend.ai/issues/2705))
* Allow adding required GQL field argument to schema. ([#2712](https://github.com/lablup/backend.ai/issues/2712))
* Upgrade `readthedocs` build environment to Python 3.12 ([#2814](https://github.com/lablup/backend.ai/issues/2814))## 24.03.0rc1 (2024-03-31)

### Features
* Allw filter `compute_session` query by `user_id`. ([#1805](https://github.com/lablup/backend.ai/issues/1805))
* Allow overriding vfolder mount permissions in API calls and CLI commands to create new sessions, with addition of a generic parser of comma-separated "key=value" list for CLI args and API params ([#1838](https://github.com/lablup/backend.ai/issues/1838))
* Always enable `ai.backend.accelerator.cuda_open` in the scie-based installer ([#1966](https://github.com/lablup/backend.ai/issues/1966))
* Use `config["pipeline"]["endpoint"]` as default value of `config["pipeline"]["frontend-endpoint"]` when not provided ([#1972](https://github.com/lablup/backend.ai/issues/1972))

### Fixes
* Set single agent per kernel resource usage. ([#1725](https://github.com/lablup/backend.ai/issues/1725))
* Abort container creation when duplicate container port definition exists ([#1750](https://github.com/lablup/backend.ai/issues/1750))
* To update image metadata, check if the min/max values in `resource_limits` are undefined. ([#1941](https://github.com/lablup/backend.ai/issues/1941))
* Explicitly disable the user-site package detection in the krunner python commands to avoid potential conflicts with user-installed packages in `.local` directories ([#1962](https://github.com/lablup/backend.ai/issues/1962))
* Fix `caf54fcc17ab` migration to drop a primary key only if it exists and in `589c764a18f1` migration, add missing table arguments. ([#1963](https://github.com/lablup/backend.ai/issues/1963))

### Documentation Updates
* Update docstrings in `ai.backend.client.request.Request:fetch()` and `ai.backend.client.request.FetchContextManager` as the support for synchronous context manager has been deprecated. ([#1801](https://github.com/lablup/backend.ai/issues/1801))
* Resize font-size of footer text in ethical ads in documentation hosted by read-the-docs ([#1965](https://github.com/lablup/backend.ai/issues/1965))
* Only resize font-size of footer text in ethical ads not in title of content in documentation ([#1967](https://github.com/lablup/backend.ai/issues/1967))

### Miscellaneous
* Revert response type of service create API. ([#1979](https://github.com/lablup/backend.ai/issues/1979))


## 24.03 and earlier

* [Unified changelog for the core components](https://github.com/lablup/backend.ai/blob/24.03/CHANGELOG.md)
