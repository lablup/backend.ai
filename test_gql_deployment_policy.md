# GQL Deployment Policy Test Examples

Strawberry endpoint: `POST /admin/gql/strawberry`

## 1. createModelDeployment (with ROLLING + IntOrPercent)

```graphql
mutation {
  createModelDeployment(input: {
    metadata: {
      projectId: "2de2b969-1d04-48a6-af16-0bc8adb3c831"
      domainName: "default"
      name: "test-rolling-percent"
    }
    networkAccess: {
      openToPublic: false
    }
    defaultDeploymentStrategy: {
      type: ROLLING
      rollingUpdate: {
        maxSurge: { type: PERCENT, percent: 0.25 }
        maxUnavailable: { type: COUNT, count: 1 }
      }
    }
    desiredReplicaCount: 3
    initialRevision: {
      clusterConfig: { mode: SINGLE_NODE, size: 1 }
      resourceConfig: {
        resourceGroup: { name: "default" }
        resourceSlots: {
          entries: [
            { resourceType: "cpu", quantity: "1" }
            { resourceType: "mem", quantity: "2g" }
          ]
        }
      }
      image: { id: "02b5da49-3569-4ad5-89b7-1fc44729233d" }
      modelRuntimeConfig: { runtimeVariant: "custom" }
      modelMountConfig: {
        vfolderId: "2c7d47fa-e3bd-4afa-8412-72b3da94e355"
        mountDestination: "/models"
        definitionPath: "/models/model.yaml"
      }
    }
  }) {
    deployment {
      id
    }
  }
}
```

## 2. updateDeploymentPolicy (COUNT)

```graphql
mutation {
  updateDeploymentPolicy(input: {
    deploymentId: "<DEPLOYMENT_ID>"
    strategy: ROLLING
    rollingUpdate: {
      maxSurge: { type: COUNT, count: 2 }
      maxUnavailable: { type: COUNT, count: 1 }
    }
  }) {
    deploymentPolicy {
      id
    }
  }
}
```

## 3. updateDeploymentPolicy (PERCENT)

```graphql
mutation {
  updateDeploymentPolicy(input: {
    deploymentId: "<DEPLOYMENT_ID>"
    strategy: ROLLING
    rollingUpdate: {
      maxSurge: { type: PERCENT, percent: 0.25 }
      maxUnavailable: { type: PERCENT, percent: 0.1 }
    }
  }) {
    deploymentPolicy {
      id
    }
  }
}
```

## 4. updateDeploymentPolicy (BLUE_GREEN)

```graphql
mutation {
  updateDeploymentPolicy(input: {
    deploymentId: "<DEPLOYMENT_ID>"
    strategy: BLUE_GREEN
    blueGreen: {
      autoPromote: true
      promoteDelaySeconds: 30
    }
  }) {
    deploymentPolicy {
      id
    }
  }
}
```

## 5. updateDeploymentPolicy (defaults - surge/unavailable omitted)

```graphql
mutation {
  updateDeploymentPolicy(input: {
    deploymentId: "<DEPLOYMENT_ID>"
    strategy: ROLLING
  }) {
    deploymentPolicy {
      id
    }
  }
}
```
