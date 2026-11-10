# Glossary: Operations

The style rules are in the [glossary](../GLOSSARY.md). Korean: [operations.ko.md](operations.ko.md)

| English | Meaning | Do not write | Note |
|---|---|---|---|
| activate revision | An operation that changes the revision of a deployment to the current revision. |   |   |
| approve | An operation that approves an artifact revision. |   |   |
| assign users to project | An operation that assigns a user to a project together with a project role. |   |   |
| batch | A prefix for operations that process multiple rows atomically in a single SQL statement. |   |   |
| bulk | A prefix for operations that handle multiple entities in a single operation. Whether partial success is possible is distinguished by the partial_bulk and atomic_bulk notations. |   |   |
| clone | An operation that clones a vfolder. |   |   |
| delete | An operation that marks a row as deleted while keeping it. Permanent deletion is purge. | soft delete, soft-delete |   |
| deregister | An operation that removes a registered service instance from the registration list. |   |   |
| destroy | An operation value that terminates a session. |   |   |
| enqueue session | Enqueues a new session into the queue. |   |   |
| execute | The core call of the user API that runs user code in an isolated session. |   |   |
| force purge | An escape hatch that deletes rows immediately without waiting for cleanup. |   |   |
| grant | An operation that grants a role to a user. The former permission bit grant:* is abolished, and entity share now handles transferring entities. |   |   |
| purge | An operation that completely removes an entity so that it cannot be restored. | hard delete |   |
| rescan | An operation that re-reads the metadata of an external registry to update the DB. |   |   |
| restore | An operation that reverses delete to bring something back. |   |   |
| revocation | An operation that takes back permission. |   |   |
| revoke | An operation that takes back a granted credential, used for keypair, login session, role, and sharing. |   |   |
| scan | An operation that reads images and artifacts from a registry to register and update them. |   |   |
| scoped search | A query method that takes a scope identifier as a required argument and searches within that scope. |   |   |
| session commit | An operation that saves the container state of a session as a new image. | container commit, imagify |   |
| upsert | A write operation that creates a new row or updates an existing row. |   |   |
| vfolder invitation | A sharing mechanism that invites other users to collaborate on a vfolder. |   |   |
| vfolder leave | An operation to leave a vfolder that has been shared with the user. | leave |   |
