Backend.AI Accelerator Plugin for CUDA GPUs bound to vfio-pci
=============================================================

Offers NVIDIA GPUs bound to `vfio-pci` as whole-device `cuda.device` slots and hands each
allocated GPU to the runtime as an iommufd node (`/dev/vfio/devices/vfioN`). It reads sysfs
only. It shares the `cuda` key with `cuda-open`, so load only one, and only via
`allow-compute-plugins = ["ai.backend.accelerator.cuda_vfio"]`. An allowlist that names both
plugins, or the broad prefix `ai.backend.accelerator`, makes the agent fail to start: name only one.

```console
$ pip install backend.ai-accelerator-cuda-vfio
```

A GPU is offered only when the rest of its IOMMU group is `vfio-pci`-bound or a bridge.
Device ids are PCI addresses with `:` replaced by `-`.

Plugin config `memory_overrides` maps a PCI address or device id (`0x2bb5`) to a memory size
such as `96 GiB`, for models missing from the built-in table.
