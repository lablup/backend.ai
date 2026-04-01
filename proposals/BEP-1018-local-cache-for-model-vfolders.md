---
Author: Joongi Kim (joongi@lablup.com)
Status: Draft
Created: 2025-07-09
Created-Version:
Target-Version:
Implemented-Version:
---

# Local cache for model vfolders

## Motivation

In Backend.AI, model deployments load the model parameters (checkpoints) and launch configurations from a remote filesystem mounted as "vfolders".
This is convenient for organizing and centralizing RBAC of model vfolders, but it may become a source of instability due to high-volume I/O when there are multiple containers loading models at the same time.
We also observed many _mountpoint loss_ issues in production by whatever network/filesystem issues.

The model deployments should be VERY STABLE because it would directly affect the customer's sales.
In this sense, @inureyes has proposed having a local cache for model vfolders used in model deployments.


## Potential Designs

* **Explicit file copy**: let the Backend.AI agent copy the model vfolder contents upon container startup.

  - It incurs an explicit delay on the model service launches.  We may need to add some kind of progress tracking before marking the model deployment is "healthy".

* **Caching FUSE**: insert a fuse filesystem like [catfs](https://github.com/kahing/catfs/) or [mcachefs](https://github.com/Doloops/mcachefs) to transparently copy the target files into a local directory when reading the file for the first time.

  - Since there are multiple such "caching" fuse implementations, we need to investigate which one would work better for us, in terms of performance and stability.

  - It would be simpler to implement, but requires updates on the APC team's deplyoment processes and installation tools.


## Related Work

Currently we have a _recommended_ setting for [`fsc`](https://docs.kernel.org/filesystems/caching/fscache.html) following [the `cachefilesd` configuration of NVIDIA's DGX OS](https://docs.nvidia.com/dgx/dgx-os-6-user-guide/installing_on_ubuntu.html#configuring-data-drives).
Note that `cachefilesd` is a user-level service that interacts with the kernel-level `fsc` layer.

Though, it only works for remote filesystems like NFS mounts and cannot be used to provide caching of FUSE-based filesystems like `s3fs`.


## Proposed Design

In combination with the object storage support ([BA-255](https://lablup.atlassian.net/browse/BA-255) or lablup/backend.ai#665), I'd prefer the FUSE-based approach using `catfs`.

### Things to check

- Do we need to pre-load all files by trying to `open()` when starting the container or just do on-demand loading?

- Does `catfs` ensure cleaning up of cached data when unmounting?

### Things to consider when deploying (cc: APC team)

- `catfs` has a configuration to keep the free space of the cache volume as percentage. It means that `catfs` may evict some files when it reaches the space limit.
  Due to possibility of eviction, it DOES NOT guarantee that all model vfolder mounts are fully cached all the time.

### Impacts to the existing vfolder subsystem

- By default, the mount caching should only be enabled for the main model vfolder of a model deployment container.

- We could add a per-user vfolder-access record attribute to control whether to apply local caching (with warnings and descriptions about non-POSIX I/O behaviors).
