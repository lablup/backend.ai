How Backend.AI Agent Works
================



`AbstractAgent`
---------------
`AbstractAgent` defines atomic operations for Backend.AI agent to work, with its core container-related works left as abstract function. Actual implementation of this class varies by container backend. We currently support Kubernetes (`KubernetesAgent`) and Docker (`DockerAgent`) by default.

`AbstractKernel`
----------------
`AbstractKernel` acts as a controller of created Backend.AI kernel. `AbstractKernel` manages lifecycle of each app on kernel, transfers input/output data between user and kernel app, and so on. Just like `AbstractAgent`, actual implementation varies by container backend.
