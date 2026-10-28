Backend.AI Accelerator Plugin for CUDA GPUs bound to vfio-pci
=============================================================

Offers NVIDIA GPUs bound to `vfio-pci` as whole-device `cuda.device` slots and hands each
allocated GPU to the runtime as an iommufd node (`/dev/vfio/devices/vfioN`). It reads sysfs
only. It shares the `cuda` key with `cuda-open`, so load only one, and only via
`allow-compute-plugins = ["ai.backend.accelerator.cuda_vfio"]`.

A GPU is offered only when the rest of its IOMMU group is `vfio-pci`-bound or a bridge.
Device ids are PCI addresses with `:` replaced by `-`.
