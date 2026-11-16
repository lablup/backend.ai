# Glossary: Permissions

The style rules are in the [glossary](../GLOSSARY.md). Korean: [permissions.ko.md](permissions.ko.md)

| English | Meaning | Do not write | Note |
|---|---|---|---|
| 2FA | An authentication feature that requires a 2FA code at login when configured. | two-factor authentication |   |
| access key | A key used for programmatic access in keypair authentication. |   |   |
| admin_ | A prefix for API operations reserved for the superadmin. |   | This is a code name. |
| agent selection policy | A method that determines whether to enforce designated_agent_ids or allow alternatives. |   |   |
| allowed client ip | A client IP list that, when specified, allows login only from those addresses. |   |   |
| allowed container registry | A list of container registries allowed in a domain. | allowed docker registries |   |
| allowed resource group | A list of resource groups allowed for use by a domain or project. |   |   |
| allowed storage host | A list of storage hosts allowed by a domain. | allowed vfolder hosts | This will be unified into storage group later. |
| API keypair | A pair of an access key and a secret key used for programmatic access. |   |   |
| authentication mode | The authentication method of a user account, with session based on a browser session and keypair based on an access/secret key pair. |   |   |
| authority | An identification string registered by app proxy worker nodes. |   | Will be moved to ingress group later. |
| client IP allowlist | A feature that allows access to exposed apps only from addresses allowed by the circuit. |   |   |
| client IP masking policy | A policy that determines how to mask client addresses before storing them in login history or audit log. |   |   |
| default access key | The access key that a user uses as their primary key, which can be changed to another key. | main access key | The error message in the code is already default access key. |
| deployment token | A token that calls a deployment and fixes which user to act as. | access token, deployment access token |   |
| domain admin | An administrator role with full permissions within the domain scope. |   | Exists only as an RBAC role. |
| domain member | The basic member role of the domain scope. |   |   |
| effective permission | The permission actually applied by combining multiple role grants and caps. |   |   |
| entity share | A grant that proposes transferring an entity to another user or project. | invitation, offer |   |
| gate | A validator that checks action execution and authorizes each scope. |   |   |
| idle checker assignment | An assignment that binds a global idle checker to a single scope. | idle checker binding |   |
| impersonation | A feature that lets a superadmin run operations in the permission context of a target user. | Act As |   |
| keypair | A pair of an access key and a secret key with which a user signs API calls. |   |   |
| keypair resource policy | A resource policy bound to a keypair that controls session-related resource limits. |   | Scheduled for removal. Do not use it for new work. |
| mount policy | The mount level that a user has on a vfolder, with the values none, ro, and rw. |   |   |
| my | A prefix for operations that handle only the current user's own resources. |   |   |
| permission | A single authority that a role grants on one entity type within a scope. |   |   |
| permission bit | A value that represents a granted action as one bit of a permission mask. |   |   |
| project admin | An administrator role with full authority within a project scope. |   | Exists only as an RBAC role. |
| project member | The default member role of a project scope. |   |   |
| project resource policy | A resource policy that controls the shared quota of resources at the project level. |   |   |
| public | A prefix for operations allowed to all authenticated users without a permission check. It is not anonymous access. |   |   |
| RBAC | A system that expresses authority through combinations of roles, scope types, entity types, and permission bits. | Role-Based Access Control |   |
| resource policy | A policy that defines resource limits per keypair, user, and project. |   |   |
| role | A unit that bundles permissions and grants them to a user within a scope. |   |   |
| role assignment | An assignment relation linking a user and a role. Revoking it deletes the row. |   |   |
| role permission preset | A permission entry granted by a role preset. | permission entry |   |
| role preset | A template used when creating a role, loaded as seed YAML. |   |   |
| role status | A set of role status values where inactive means temporary deactivation and deleted means purge. |   |   |
| RPC keypair | A keypair used for RPC authentication and encryption between the manager and the agent. |   |   |
| scope | A range that defines an access boundary, with units such as domain, project, and user. |   |   |
| scope cap | An upper limit that narrows granted permissions per scope. |   |   |
| scoped permission | An operation permission on entity types within a specific scope. | Scope-Level Permission |   |
| secret key | The confidential counterpart of the access key in an API keypair. |   | A different concept from the secret key of pk and sk. |
| SSH keypair | A keypair owned by a user, used for SSH/SFTP access. |   |   |
| storage proxy client API | An API that the Storage Proxy exposes to users. | client-facing API, client API |   |
| storage proxy manager API | An API that the Manager calls on the Storage Proxy. | manager-facing API |   |
| sudo session | A privileged session that a user can create. |   |   |
| superadmin | A system-wide administrator who passes all permission checks without a role row. | suerp-admin, super-admin |   |
| vfolder permission | The permission that a user has on a vfolder. |   | Going forward, everything except the mount policy is integrated into RBAC. |
| virtual scope | A hub node for permission decisions, placed one per owning scope. |   |   |
