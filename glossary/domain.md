# Glossary: Product and domain concepts

The style rules are in the [glossary](../GLOSSARY.md). Korean: [domain.ko.md](domain.ko.md)

| English | Meaning | Do not write | Note |
|---|---|---|---|
| accelerator | A plugin installed on an agent to add resource slots. | Compute Plugins |   |
| Agent | A component that manages the container lifecycle on a node, monitors resource usage, and reports its status to the manager. | compute node | In Backend.AI documentation, Agent alone is fine. Use node when referring only to the node where it runs, not to the agent. |
| agent selection strategy | A strategy for choosing the agent on which to place a session. |   |   |
| alert | A feature that sends automatic notifications to external messaging services based on monitoring metric thresholds. |   |   |
| alias | A path used instead of the folder name when mounting. |   |   |
| API endpoint | The address of the API server to connect to. |   |   |
| app config | The value of an app config key merged from the fragments of all visible scopes. | AppConfig |   |
| app config allow list | A list that determines, per config name, whether a scope can write a value and the fragment merge priority. |   |   |
| app service | An application service started inside a session. |   |   |
| artifact | A model, package, or image in an artifact registry. |   |   |
| artifact registry | A registry that manages AI models, packages and images from external sources such as HuggingFace Hub and Reservoir. |   |   |
| artifact revision | A version of an artifact that is created by a registry scan and imported separately. |   |   |
| artifact storage | A destination for storing artifacts that is preconfigured in the system settings. |   |   |
| artifact type | A grouping of artifact kinds. |   |   |
| audit log | A record of who executed which action on what. |   |   |
| auto-mount vfolder | A vfolder that is automatically mounted to every session created by a project or a user. | Auto-mount vfolders, vfolder auto-mount |   |
| auto-scaling rule | A rule that adjusts the number of replicas of a deployment based on metrics. |   |   |
| Backend.AI | A container-based computing cluster platform. |   |   |
| base image | An image attached to a container-based or VM-based kernel. |   |   |
| bootstrap script | A script that runs when a session starts. |   |   |
| channel type | A classification of notification channel kinds. |   |   |
| circuit | A routing rule from the client to the session service. |   | Will be moved to manager management and replaced with ingress later. |
| client IP masking | Masks the client IP with one policy row per target_type. |   |   |
| cluster mode | A value that indicates whether a session runs on a single node or multiple nodes. |   |   |
| code execution | An API that interacts with an interactive session. |   |   |
| compute environment | A list of image environments scanned from the container registry and shown on the screen. |   |   |
| compute schedule | An operation that calculates whether a session can be placed in a resource group without provisioning. |   |   |
| container registry | A registry for pulling container images and its access credentials. |   |   |
| Control Panel | An add-on service for advanced management and monitoring of the manager. |   |   |
| custom image | An image created by a session commit. | customized image |   |
| dashboard | An add-on service that shows real-time and past performance metrics. | Backend.AI Dashboard |   |
| deployment | A model service that has the number of replicas to maintain and the replica group serving them. | Model Service |   |
| deployment agent designation | A feature that designates the agent on which a deployment is placed. | deployment designated agent |   |
| deployment endpoint | A model serving unit that has replicas, revisions and autoscaling. | endpoint |   |
| deployment preset | A named template for a single runtime variant that holds the initial values of a deployment. |   |   |
| deployment strategy | A way to release the revisions of a deployment, which has the values ROLLING and BLUE_GREEN. |   |   |
| domain | The top-level tenant that contains projects and users. |   |   |
| error log | An error record exposed to users that can be marked as read or deleted. |   |   |
| fair share | A scheduling feature that fairly distributes resources based on usage history. |   |   |
| fair share factor | A metric calculated by reflecting past usage, where a higher value means higher scheduling priority. | Fairness Score |   |
| fractional GPU sharing | A GPU sharing feature available only in the enterprise edition. | GPU sharing, fractional sharing of GPUs |   |
| GUI desktop client | A desktop client that enables GUI features not possible on the web. | Backend.AI Web UI App |   |
| HuggingFace registry | A registry entry that holds a HuggingFace Hub address and an access token. |   |   |
| idle checker | A rule that terminates a session based on lifetime, network unresponsiveness, and resource utilization. |   |   |
| image | A container image that launches sessions and belongs to a registry. |   |   |
| image alias | An alias attached to an image, whose registration and removal are protected by superadmin validation. |   |   |
| intrinsic service | A service available in every kernel without separate support from the image author. |   |   |
| kernel | A container that runs a session. |   |   |
| kernel group | One role in a session, the unit in which its member kernels share one execution spec. |   |   |
| kernel group role | The role a kernel takes in a multi-kernel session, where the first container is main and the rest are sub. | cluster role |   |
| login client type | The type of client that opens a login session. |   |   |
| login history | A single login attempt recorded for a user. |   |   |
| login session | A session that persists while a user stays authenticated, with values active, invalidated and revoked. |   |   |
| model card | A description of a model contained in a vfolder. |   |   |
| model definition | A configuration that defines the model composition and metadata of a model service. |   |   |
| model revision | An immutable version of a model within a model deployment. |   |   |
| model store | A store where a user picks models and imports them into their own vfolder. |   |   |
| model store project | A project of the MODEL_STORE project type to which a model card belongs. |   |   |
| model vfolder | A vfolder that holds model parameters and execution configuration files. |   |   |
| multi-kernel session | A session that has multiple kernels. | cluster session |   |
| notification channel | The target to which a notification is sent. |   |   |
| notification rule | A rule that defines the message to use when sending one type of event to a channel. |   |   |
| object storage | An S3-compatible object storage accessed with an endpoint and credentials. |   |   |
| personal project | A project for an individual user, with only one per user. |   |   |
| pipeline | A unit for designing and executing computational tasks in sequence. |   |   |
| project | A group of users that owns sessions and vfolders within a domain. | group |   |
| project type | A type that defines the purpose and behavior of a project. |   |   |
| prometheus query preset | A named Prometheus query template and execution time range saved in advance. |   |   |
| quota scope | A storage usage limit per user and per project. |   |   |
| rate limit | A limit that caps the number of API requests so that a client does not overload the server. |   |   |
| replica | A single session serving a deployment, which receives part of the traffic when healthy. |   |   |
| replica group | A unit that groups the replicas of a deployment and adjusts traffic while moving between revisions. |   |   |
| Reservoir | A type of artifact registry used as an artifact storage. |   | Written only in English because it is a product name. |
| resource allocation | An entry that records the amount of a resource that a kernel requested, received, and actually used. |   |   |
| resource group | A unit that groups agents and places sessions with an independent scheduler. | scaling group, sgroup |   |
| resource preset | A named bundle of resource amounts that a session can request. |   |   |
| resource slot | A resource unit such as CPU, memory, and GPU allocated to a session. |   |   |
| resource slot type | A classification of the resource slot value shape, with the values count, bytes, unique, and unified. |   |   |
| resource weight | A fair share priority multiplier set per resource type. |   |   |
| revision | A snapshot of a deployment configuration at a single point in time. |   |   |
| rolling update | A method in which a deployment gradually deploys a new revision. |   |   |
| runtime variant | The model serving runtime in which a deployment revision runs. |   |   |
| runtime variant preset | A stored configuration of a single runtime variant. |   |   |
| scheduler type | The kind of scheduler used by a resource group. |   |   |
| scratch storage | A local temporary storage space given to each kernel and cleaned up on termination. |   |   |
| service catalog | A catalog where running components register themselves with the manager. | SD catalog |   |
| service group | An identifier that groups service instances of the same kind in the service catalog. |   |   |
| service port | A port through which a container exposes its service to the outside. | Service Proxies |   |
| session | A unit that groups kernels for execution. Kernels with the same execution spec are managed as a kernel group within the session. | compute session, computing session |   |
| session dependency | A dependency between sessions in which one session waits for another. |   |   |
| session group | A unit that places multiple sessions together on the same agent or spreads them across agents. | placement group |   |
| session history | A record that leaves status changes and results each time a session scheduling handler runs. |   |   |
| session lifetime | The maximum time a session can run. |   |   |
| session template | A stored configuration used when creating a session. | task template |   |
| session type | A bundle of session kind values, including interactive, batch, inference, and system. |   |   |
| storage host | A storage backend host that holds vfolders. |   |   |
| storage namespace | A bucket of an object storage or a subpath of a VFS storage. |   |   |
| storage volume | A logical volume on a storage backend, identified by the name that each service declares. |   |   |
| system session | A system type of session that a user launches, such as an SFTP session. |   |   |
| terminate | An operation that ends a session. |   |   |
| unmanaged vfolder | A vfolder that points directly to a path on the storage host and keeps that path in unmanaged_path. | unmanaged virtual folder |   |
| user | An account within a domain. |   |   |
| user resource policy | A resource limit policy applied per user. |   |   |
| vfolder | A storage space owned by a user or project and mounted to a container at runtime. | virtual folder | A concept distinct from an ordinary folder. |
