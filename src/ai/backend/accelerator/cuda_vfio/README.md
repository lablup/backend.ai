Backend.AI Accelerator Plugin for CUDA GPUs bound to vfio-pci
=============================================================

This plugin offers NVIDIA GPUs that are bound to `vfio-pci` on the host as whole-device
`cuda.device` slots, and hands each allocated GPU to the container runtime as an iommufd
device node (`/dev/vfio/devices/vfioN`). It reads sysfs only and needs neither NVML nor
the CUDA runtime library.

It uses the same device key (`cuda`) as `backend.ai-accelerator-cuda-open`, so a host must
load only one of them. It is loaded only when listed explicitly in the agent configuration:

```toml
[agent]
allow-compute-plugins = ["ai.backend.accelerator.cuda_vfio"]
```

A GPU is offered only when every other member of its IOMMU group is bound to `vfio-pci`
or is a PCI bridge.

The device id is the PCI address with `:` replaced by `-` (e.g. `0001-0b-00.0`).
`memory_overrides` keys are the PCI address in either form, or the PCI device ID (e.g. `2bb5`).
