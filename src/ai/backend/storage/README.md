# Backend.AI Storage Proxy

Backend.AI Storage Proxy is an RPC daemon to manage vfolders used in Backend.AI agent, with quota and
storage-specific optimization support.

## Package Structure

-   `ai.backend.storage`
    -   `server`: The agent daemon which communicates between Backend.AI Manager
    -   `api.client`: The client-facing API to handle tus.io server-side protocol for uploads and ranged HTTP
        queries for downloads.
    -   `api.manager`: The manager-facing (internal) API to provide abstraction of volumes and separation of
        the hardware resources for volume and file operations.
    -   `vfs`
        -   The minimal fallback backend which only uses the standard Linux filesystem interfaces
    -   `xfs`
        -   XFS-optimized backend with a small daemon to manage XFS project IDs for quota limits
        -   `agent`: Implementation of `AbstractVolumeAgent` with XFS support
    -   `purestorage`
        -   PureStorage's FlashBlade-optimized backend with RapidFile Toolkit (formerly PureTools)
    -   `netapp`
        -   NetApp QTree integration backend based on the NetApp ONTAP REST API
    -   `weka`
        -   Weka.IO integration backend with Weka.IO V2 REST API
    -   `cephfs` (TODO)
        -   CephFS-optimized backend with quota limit support

## Installation

### Prerequisites

-   Python 3.8 or higher with [pyenv](https://github.com/pyenv/pyenv)
    and [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv) (optional but recommended)

### Installation Process

First, prepare the source clone of this agent:

```console
# git clone https://github.com/lablup/backend.ai-storage-proxy
```

From now on, let's assume all shell commands are executed inside the virtualenv.

Now install dependencies:

```console
# pip install -U -r requirements/dist.txt  # for deployment
# pip install -U -r requirements/dev.txt   # for development
```

Then, copy halfstack.toml to root of the project folder and edit to match your machine:

```console
# cp config/sample.toml storage-proxy.toml
```

When done, start storage server:

```console
# python -m ai.backend.storage.server
```

It will start Storage Proxy daemon bound at `127.0.0.1:6021` (client API) and
`127.0.0.1:6022` (manager API).

NOTE: Depending on the backend, the server may require to be run as root.

### Production Deployment

To get performance boosts by using OS-provided `sendfile()` syscall
for file transfers, SSL termination should be handled by reverse-proxies
such as nginx and the storage proxy daemon itself should be run without SSL.

## Filesystem Backends

### VFS

#### Prerequisites

-   User account permission to access for the given directory
    -   Make sure a directory such as `/vfroot/vfs` a directory or you want to mount exists

### XFS

#### Prerequisites

-   Local device mounted under `/vfroot`
-   Native support for XFS filesystem
    -   Mounting XFS volume with an option `-o pquota` to enable project quota
    -   To turn on quotas on the root filesystem, the quota mount flags must be
        set with the `rootflags=` boot parameter. Usually, this is not recommended.
-   Access to root privilege
    -   Execution of `xfs_quota`, which performs quota-related commands, requires
        the `root` privilege.
    -   Thus, you need to start the Storage-Proxy service by a `root` user or a
        user with passwordless sudo access.
    -   If the root user starts the Storage-Proxy, the owner of every file created
        is also root. In some situations, this would not be the desired setting.
        In that case, it might be better to start the service with a regular user
        with passwordless sudo privilege.

#### Creating virtual XFS device for testing

Create a virtual block device mounted to `lo` (loopback) if you are the only one
to use the storage for testing:

1. Create file with your desired size

```console
# dd if=/dev/zero of=xfs_test.img bs=1G count=100
```

2. Make file as XFS partition

```console
# mkfs.xfs xfs_test.img
```

3. Mount it to loopback

```console
# export LODEVICE=$(losetup -f)
# losetup $LODEVICE xfs_test.img
```

4. Create mount point and mount loopback device, with pquota option

```console
# mkdir -p /vfroot/xfs
# mount -o loop -o pquota $LODEVICE /vfroot/xfs
```

#### Note on operation

XFS keeps quota mapping information on two files: `/etc/projects` and
`/etc/projid`. If they are deleted or damaged in any way, per-directory quota
information will also be lost. So, it is crucial not to delete them
accidentally. If possible, it is a good idea to backup them to a different disk
or NFS.

### PureStorage FlashBlade

#### Prerequisites

-   NFSv3 export mounted under `/vfroot`
-   Purity API access

### CephFS

#### Prerequisites

-   FUSE export mounted under `/vfroot`

### NetApp ONTAP

#### Prerequisites

-   NFSv3 export mounted under `/vfroot`
-   NetApp ONTAP API access
-   native NetApp XCP or Dockerized NetApp XCP container
    -   To install NetApp XCP, please refer [NetApp XCP install guide](https://xcp.netapp.com/)
-   Create Qtree in Volume explicitly using NetApp ONTAP Sysmgr GUI

#### Note on operation

The volume host of Backend.AI Storage proxy corresponds to Qtree of NetApp ONTAP, not NetApp ONTAP Volume.  
Please DO NOT remove Backend.AI mapped qtree in NetApp ONTAP Sysmgr GUI. If not, you cannot access to NetApp ONTAP Volume through Backend.AI.

> NOTE:  
> Qtree name in configuration file(`storage-proxy.toml`) must have the same name created in NetApp ONTAP Sysmgr.

### Weka.IO

#### Prerequisites

-   Weka.IO agent installed and running
-   Weka.IO filesystem mounted under local machine, with permission set to somewhat storage-proxy process can read and write
-   Weka.IO REST API access (username/password/organization)
