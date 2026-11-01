# 제목

새 모델 서빙을 위한 GraphQL 스키마

## 동기

[BEP-1009 모델 서빙 레지스트리](https://github.com/lablup/beps/blob/main/drafts/BEP-1009-model-serving-registry.md)의 후속으로, 이 BEP 는 Backend.AI 의 새 모델 서빙 서비스를 위한 포괄적인 GraphQL 스키마를 제안한다.

## 제안 설계

GraphQL 스키마는 모델 서빙 인프라를 관리하려고 두 가지 주요 엔티티와 이를 뒷받침하는 타입을 도입한다.

### 핵심 엔티티

1. **ModelDeployment**: 모델 서빙 배포를 나타내는 최상위 엔티티다. 다음을 관리한다.
   - 활성 리비전과 리비전 이력
   - 배포 전략(Rolling, Blue-Green, Canary)
   - 공개 엔드포인트 설정과 사용자 정의 도메인
   - 도메인과 프로젝트 연결
   - 오토스케일링 규칙을 포함한 복제본 관리

2. **ModelRevision**: 배포 안에서 모델의 불변 버전을 나타낸다. 다음을 다룬다.
   - container image 와 런타임 설정
   - 모델 저장과 마운트 설정
   - 클러스터 설정과 자원 그룹
   - 자원 요구 사항과 runtime variant
   - 서비스별 설정
   - 추가 볼륨 마운트

## 기술 세부 사항

### ModelDeployment

배포는 여러 리비전을 관리하는 최상위 개념이다.

#### 기본 필드
- `id`: 고유 식별자
- `name`: 배포 이름(도메인 안에서 고유)
- `endpointUrl`: 모델 서빙 접근용 공개 URL(예: https://llama-3.model.ai)
- `preferredDomainName`(선택): 선호하는 사용자 정의 도메인 이름
- `status`: 배포 상태
  - ACTIVE, HIBERNATED, PROVISIONING, UPDATING, FAILED, DESTROYING, DESTROYED
- `openToPublic`: 공개 접근 가능 여부
- `tags`: 모델 서빙 tag

#### 복제본 관리
- `replicaManagement`:
    - `desiredReplicaCount`: 목표 복제본 수
    - `replicas`: 배포가 관리하는 `ModelReplica` 목록
    - `routings`: 각 복제본의 라우팅 정보

#### 배포 전략
- `deploymentStrategy`
    - `type`: 배포 전략 타입
    - `config`: 배포 전략에 필요한 설정(예: maxSurge)

#### 리비전 정보
- `revision`: 배포가 참조하는 현재 활성 ModelRevision
- `revisionHistory`: 배포가 이전에 참조한 ModelRevision 목록

#### 연관 필드
- `domain`: Backend.AI 도메인
- `project`: 소유 프로젝트(group)
- `createdUser`: 배포를 생성한 사용자
- `revisions`: 이 배포에 속한 모든 리비전
- `accessTokens`: endpoint url 접근용 토큰

#### 메타데이터
- `createdAt`: 생성 시각
- `updatedAt`: 마지막 변경 시각

#### 스키마
```graphql
enum DeploymentStatus {
    INACTIVE
    ACTIVE
}

type ReplicaManagement {
    desiredReplicaCount: Int!
    replicas: [ModelReplica!]!
    autoScalingRules: [AutoScalingRule!]!
}

type ModelReplica {
    name: String!
    revision: ModelRevision!
    routings(first: Int, after: String): RoutingConnection!
}

enum DeploymentStrategyType {
    ROLLING
    BLUE_GREEN
    CANARY
}

union StrategyConfig = RollingConfig | BlueGreenConfig | CanaryConfig

type DeploymentStrategy {
    type: DeploymentStrategyType!
    config: StrategyConfig
}

type ModelDeployment {
    id: ID!
    name: String!
    endpointUrl: String
    preferredDomainName: String
    status: DeploymentStatus!
    openToPublic: Boolean!
    tags: [String!]!

    revision: ModelRevision
    revisionHistory: [ModelRevision!]!
    
    replicaManagement: ReplicaManagement!

    deploymentStrategy: DeploymentStrategy!

    domain: Domain!
    project: Project!
    createdUser: User!
    resourceGroup: ResourceGroup!
    accessTokens: [AccessToken!]!

    createdAt: DateTime!
    updatedAt: DateTime!
}
```

#### Query 와 Subscription
```graphql

type ReplicaMetric {
  ... # TODO: Fill up metric fields
}

type DeploymentMetrics {
    replicaMetrics: [ReplicaMetric!]!
}

type Query {
    # Deployment Queries
    deployments(filter: DeploymentFilter, limit: Int, offset: Int): [ModelDeployment!]!
    deployment(id: ID!): Deployment
 
    # Replica Queries
    replica(id: ID!): ModelReplica

    # Metrics
    deploymentMetrics(id: ID!, filter: DeploymentMetricsFilter): [DeploymentMetrics!]!
}

type DeploymentMetrics {
    replicaMetrics: [ReplicaMetric!]!
}

type Subscription {
    # Real-time Updates
    deploymentStatusChanged(deploymentId: ID!): ModelDeployment!
    replicaStatusChanged(revisionId: ID!): ModelReplica!
    metricsUpdated(deploymentId: ID!): DeploymentMetrics!
}

```

#### Mutation
```graphql

type Mutation {
    # Deployment Management
    createModelDeployment(input: CreateModelServingDeploymentInput! ): CreateModelDeploymentPayload!
    updateModelDeployment(input: UpdateModelServingDeploymentInput! ): UpdateModelDeploymentPayload!
    deleteModelServingDeployment(id: ID!): ID!
}

```

### ModelRevision

리비전은 모델 서빙의 특정 버전을 나타낸다. 불변인 세션 실행 설정을 담는다. 리비전의 특정 값을 변경하려면 사용자가 새 리비전을 발행해야 한다.

#### 기본 필드
- `id`: 고유 식별자
- `name`: 리비전 이름(선택)
- `tags`: 리비전 tag 목록
- `status`: 리비전 상태(ACTIVE, INACTIVE)

#### 클러스터 설정
- `clusterConfig`:
    - `mode`: 클러스터 모드('single-node' 또는 'multi-node')
    - `size`: 클러스터의 node 수

#### 자원과 런타임 설정
- `resourceConfig`: 자원 요구 사항과 추가 옵션
    - `resourceSlots`: 필요한 자원 슬롯 정보 
        - `cpu`
        - `mem`
        - `extra`
    - `resourceOpts`: 추가 자원 옵션(예: {"shmem": "64m"})
        - `shmem`
        - `extra`
    - `resourceGroup`: 리비전의 자원 그룹
- `ModelRuntimeConfig`: 런타임 타입과 서비스 설정
    - `runtimeVariant`: 런타임 타입(VLLM, SGLANG, NVIDIA, MOJO 등)
    - `serviceConfig`: 서비스별 설정(예: vLLM 의 max_model_length, parallelism 등)
    - `environ`: container 환경 변수(JSON)

#### 모델과 마운트 설정
- `modelVFolderConfig`: 모델 파일과 마운트 정보
    - `vfolder`: 모델을 저장한 vfolder
    - `mountDestination`: container 안 마운트 경로(기본값: /models)
    - `definitionPath`: 모델 정의 파일 경로(기본값: model-definition.yaml)
- `mounts`: 추가 볼륨 마운트 목록(각 항목: vfolderId, destination, type, permission)
- `image`: 사용한 container image 정보

#### 메타데이터
- `errorData`: 실패 시 에러 정보
- `createdAt`: 생성 시각

#### 스키마
```graphql
scalar JSONString

enum ClusterMode {
    SINGLE_NODE
    MULTI_NODE
}

type ClusterConfig {
    mode: ClusterMode!
    size: Int!
}

enum MountPermission {
    READ_ONLY
    READ_WRITE
}

type Mount {
    vfolderId: ID!
    destination: String!
    type: MountType!
    permission: MountPermission!
}

type ModelVFolderConfig {
    vfolder: VirtualFolderNode!
    mountDestination: String!
    definitionPath: String!
}

type ResourceSlots {
    cpu: Int!
    mem: String!
    extra: JSONString
}

type ResourceOpts {
    shmem: String
    extra: JSONString
}

type ResourceConfig {
    resourceGroup: ResourceGroup!
    resourceSlots: ResourceSlots!
    resourceOpts: ResourceOpts
}

union ServiceConfig = VLLMServiceConfig | SGLANGServiceConfig | NVIDIAServiceConfig | MOJOServiceConfig | CustomServiceConfig

type ModelRuntimeConfig {
    runtimeVariant: String!
    serviceConfig: ServiceConfig
    environ: JSONString
}

type ModelRevision {
    id: ID!
    name: String
    tags: [String!]!

    clusterConfig: ClusterConfig!
    resourceConfig: ResourceConfig!
    modelRuntimeConfig: ModelRuntimeConfig!
    modelVFolderConfig: ModelVFolderConfig!
    mounts: [Mount!]!
 
    image: Image!
    
    # Error and Metadata
    errorData: JSONString
    createdAt: DateTime!
}

```

#### Query 와 Subscription

```graphql
type Query {
    # Revision Queries
    revision(id: ID!): ModelRevision
    revisions(filter: ModelRevisionFilter, order: ModelRevisionOrder, first, after): [Revision!]!
}

type Subscription {
  # Real-time Updates
  deploymentStatusChanged(deploymentId: ID!): Deployment!
  replicaStatusChanged(revisionId: ID!): ReplicaInstance!
  metricsUpdated(deploymentId: ID!): DeploymentMetrics!
}

```

#### Mutation
```graphql
type Mutation {
    createModelRevision(input: CreateModelRevisionInput! ): CreateModelRevisionPayload!
}
```


## 입력 타입

### CreateModelDeploymentInput
새 배포를 생성하는 데 필요한 필드다.
- `name`: 배포 이름(도메인 안에서 고유)
- `preferredDomainName`(선택): 선호하는 사용자 정의 도메인
- `domain`: Backend.AI 도메인 이름이나 id
- `project`: 프로젝트(group) id 나 이름
- `openToPublic`: 공개 접근 가능 여부
- `tags`(선택): 모델 서빙 tag
- `clusterConfig`: 클러스터 설정
  - `mode`: 단일 node 또는 여러 node
  - `size`: 클러스터의 node 수
- `deploymentStrategy`: 배포 전략 설정
  - `type`: ROLLING, BLUE_GREEN 또는 CANARY
  - `config`: 전략별 설정
- `initialRevision`: 초기 리비전 설정

### CreateModelRevisionInput
새 리비전을 생성하는 데 필요한 필드다.
- `name`(선택): 리비전 이름
- `tags`(선택): 리비전 tag 목록
- `image`: container image 정보
  - `name`: tag 를 포함한 이미지 이름
  - `architecture`: CPU 아키텍처
- `modelRuntimeConfig`: 런타임 설정
  - `runtimeVariant`: VLLM, SGLANG, NVIDIA, MOJO 또는 custom
  - `serviceConfig`: 서비스별 설정
  - `environ`(선택): 환경 변수(JSON)
- `modelVFolderConfig`: 모델 vfolder 설정
  - `vfolderId`: 모델 vfolder id
  - `mountDestination`: 모델 마운트 경로(기본값: /models)
  - `definitionPath`: 모델 정의 파일 경로
- `mounts`(선택): 추가 볼륨 마운트
- `resourceConfig`: 자원 설정
    - `resourceGroup`: 배포용 자원 그룹
    - `resourceSlots`: 자원 요구 사항
        - `cpu`
        - `mem`
        - `extra`
    - `resourceOpts`(선택): 추가 자원 옵션
        - `shmem`
        - `extra`


### 1. 배포 상세 조회

```graphql
query GetDeploymentDetails {
  deployment(id: "deployment-uuid") {
    id
    name
    endpointUrl
    preferredDomainName
    status
    openToPublic
    tags
    
    revision {
        id
        name
        tags
        status
    }
    
    revisionHistory(
    first: 10
    orderBy: { field: CREATED_AT, direction: DESC }
    ) {
        edges {
            node {
                id
                name
                tags
                createdAt
            }
        }
        pageInfo {
            hasNextPage
            endCursor
        }
    }
    
    replicaManagement {
        desiredReplicaCount
        replicas {
            name
            revision {
                id
                name
            }
            routings(first: 10) {
                edges {
                    node {
                        id
                        status
                    }
                }
            }
        }
        autoScalingRules {
            id
            metricType
            threshold
        }
    }
    
    clusterConfig {
        mode
        size
    }
    
    deploymentStrategy {
        type
        config
    }
    
    domain {
        name
    }
    
    project {
        name
    }
    
    createdUser {
        email
    }
    
    createdAt
    updatedAt
  }
}
```

### 2. 필터로 배포 목록 조회

```graphql
enum OrderDirection {
  ASC
  DESC
}

enum DeploymentOrderField {
  CREATED_AT
  UPDATED_AT
}

input DeploymentOrderBy {
  field: DeploymentOrderField!
  direction: OrderDirection!
}

query ListDeployments {
    deployments(
        filter: {
            status: ACTIVE
            openToPublic: true
        }
        orderBy: { field: CREATED_AT, direction: DESC }
        limit: 20
        offset: 0
    ) {
        id
        name
        endpointUrl
        status
        tags
        openToPublic
        
        revision {
            id
            name
            tags
            status
        }
        
        clusterConfig {
            mode
            size
        }
        
        replicaManagement {
            desiredReplicaCount
            replicas {
                name
            }
            autoScalingRules {
                id
                metricType
                threshold
            }
        }
    }
}
```

### 3. 특정 리비전 상세 조회

```graphql
query GetRevisionDetails {
  revision(id: "revision-uuid") {
    id
    name
    tags
    status
    
    resourceConfig {
        resourceGroup {
            name
        }
        resourceSlots {
            cpu
            mem
        }
        resourceOpts {
            shmem
        }
    }
    
    modelRuntimeConfig {
        runtimeVariant
        serviceConfig
        environ
    }
    
    modelVFolderConfig {
        vfolder {
            id
            name
        }
        mountDestination
        definitionPath
    }
    mounts {
        vfolderId
        destination
        type
        permission
    }
    
    image {
        name
        architecture
    }
    
    errorData
    createdAt
  }
}
```

## Mutation 예

### 1. 단순 배포 생성

```graphql
mutation CreateSimpleDeployment {
  createModelDeployment(input: {
    name: "llama-3-service"
    domain: "default"
    project: "ml-team-project-id"
    openToPublic: true
    tags: ["production", "llm"]
    clusterConfig: {
        mode: SINGLE_NODE
        size: 1
    }
    deploymentStrategy: {
        type: ROLLING
        config: {
            maxSurge: 1
            maxUnavailable: 0
        }
    }
    initialRevision: {
        name: "initial"
        tags: ["v1.0", "stable"]
        image: {
            name: "vllm:0.9.1"
            architecture: "x86_64"
        }
    modelRuntimeConfig: {
        runtimeVariant: "VLLM"
        serviceConfig: {
            maxModelLength: 4096
            parallelism: {
                ppSize: 1
                tpSize: 2
            }
        }
        environ: "{\"CUDA_VISIBLE_DEVICES\": \"0,1\"}"
      }
    modelVFolderConfig: {
        vfolderId: "eeb8c377-15d2-4a16-8ed8-01215f3a5353"
        mountDestination: "/models"
        definitionPath: "model-definition.yaml"
      }
    mounts: [
        {
            vfolderId: "550e8400-e29b-41d4-a716-446655440001"
            destination: "/data"
            type: BIND
            permission: READ_ONLY
        }
    ]
    resourceConfig: {
        resourceGroup: {
            name: "gpu-cluster"
        }
        resourceSlots: {
            cpu: 8
            mem: "8Gib"
        }
        resourceOpts: {
            shmem: "64m"
        }
      }
    }
    }) {
        deployment {
            id
            name
            endpointUrl
            status
            tags
            revision {
                id
                name
                tags
                status
            }
        }
    }
}
```

### 2. Canary 전략으로 전문가 모드 배포 생성

```graphql
mutation CreateExpertDeployment {
    createModelDeployment(input: {
        name: "falcon-7b-optimized"
        preferredDomainName: "falcon.mycompany.ai"
        domain: "default"
        project: "research-team-id"
        openToPublic: false
        tags: ["experimental", "falcon"]
        clusterConfig: {
            mode: MULTI_NODE
            size: 3
        }
        deploymentStrategy: {
            type: CANARY
            config: {
                canaryPercentage: 10
                canaryDuration: "30m"
                successThreshold: 95
            }
        }
        initialRevision: {
            name: "baseline"
            tags: ["v1.0", "baseline"]
            image: {
                name: "python-tcp-app:3.9-ubuntu20.04"
                architecture: "x86_64"
            }
            modelRuntimeConfig: {
                runtimeVariant: "CUSTOM"
                serviceConfig: {
                extraCliParameters: "--trust-remote-code --enable-lora --gpu-memory-utilization 0.95"
                }
                environ: "{\"CUDA_VISIBLE_DEVICES\": \"0,1,2,3\"}"
            }
            modelVFolderConfig: {
                vfolderId: "550e8400-e29b-41d4-a716-446655440000"
                mountDestination: "/models"
                definitionPath: "model-definition.yaml"
            }
            mounts: [
                {
                    vfolderId: "7a83e195-7410-4768-a338-a949cef6be83"
                    destination: "/home/work/datasets"
                    type: BIND
                    permission: READ_WRITE
                }
                ]
            resourceConfig: {
                resourceGroup: {
                    name: "gpu-premium"
                }
                resourceSlots: {
                    mem: "96g"
                    cpu: 16
                }
                resourceOpts: {
                    shmem: "128m"
                }
            }
        }
    }) {
        deployment {
            id
            name
            endpointUrl
            preferredDomainName
            tags
            clusterConfig {
                mode
                size
            }
            deploymentStrategy {
                type
                config
            }
        }
    }
}
```

### 3. 새 리비전 생성

```graphql
mutation CreateNewRevision {
    createModelRevision(input: {
        deploymentId: "deployment-uuid"
        name: "optimized-version"
        tags: ["v2.0", "optimized"]
        image: {
            name: "vllm:0.9.2"
            architecture: "x86_64"
        }
        modelRuntimeConfig: {
            runtimeVariant: "VLLM"
            serviceConfig: {
                maxModelLength: 8192
                parallelism: {
                ppSize: 2
                tpSize: 4
                }
                extraCliParameters: "--enable-lora"
            }
            environ: "{\"CUDA_VISIBLE_DEVICES\": \"0,1,2,3\"}"
        }
        modelVFolderConfig: {
            vfolderId: "550e8400-e29b-41d4-a716-446655440000"
            mountDestination: "/models"
            definitionPath: "model-definition.yaml"
        }
        mounts: []
        resourceConfig: {
            resourceGroup: {
                name: "gpu-premium"
            }
            resourceSlots: {
                mem: "96g" 
                cpu: 16
            }
            resourceOpts: {
                shmem: "128m"
            }
        }
    }) {
        revision {
            id
            name
            tags
            status
            createdAt
        }
    }
}
```

### 4. 배포 설정 변경

```graphql
mutation UpdateDeployment {
    updateModelDeployment(input: {
        id: "deployment-uuid"
        openToPublic: true
        tags: ["production", "llm", "updated"]
        deploymentStrategy: {
        type: BLUE_GREEN
        config: {
            autoPromotionEnabled: true
            terminationWaitTime: 300
        }
        }
    }) {
        deployment {
        id
        name
        openToPublic
        tags
        deploymentStrategy {
            type
            config
        }
        }
    }
}
```

### 5. 활성 리비전 전환

```graphql
mutation SwitchActiveRevision {
    updateModelDeployment(input: {
        id: "deployment-uuid"
        activeRevisionId: "new-revision-uuid"
}) {
        deployment {
            id
            name
            revision {
                id
                name
                tags
                status
            }
            revisionHistory {
                id
                name
                tags
            }
        }
    }
}
```

### 6. 배포 삭제

```graphql
mutation DeleteDeployment {
  deleteModelServingDeployment(id: "deployment-uuid") {
    deletedId
  }
}
```

## 사용자와 개발자에 미치는 영향

- **사용자:**  
    사용자는 더 유연하고 견고한 모델 서빙 경험을 얻는다. 배포 관리, 버전 관리, 확장이 쉬워진다. 공개 엔드포인트와 도메인 설정 기능은 접근과 통합을 단순하게 만든다.

- **개발자:**  
    개발자는 배포와 리비전을 관리하는 잘 구조화된 GraphQL API 를 얻는다. 스키마는 고급 배포 전략(예: canary, blue-green), 자원 설정, 트래픽 관리를 지원해 운영 복잡성을 줄인다.

## 참고

- [BEP-1009 모델 서빙 레지스트리](https://github.com/lablup/beps/blob/main/drafts/BEP-1009-model-serving-registry.md)
- [GraphQL 명세](https://spec.graphql.org/)
