Using Mocked Accelerators
=========================

For developers who do not have access to physical accelerator devices such as CUDA GPUs, we provide a mock-up plugin to simulate the system configuration with such devices, allowing development and testing of accelerator-related features in various components including the web UI.

Configuring the mock-accelerator plugin
---------------------------------------

Check out the examples in |examples|_.

.. |examples| replace:: the ``configs/accelerator`` directory
.. _examples: https://github.com/lablup/backend.ai/tree/main/configs/accelerator

Here are the description of each field:

* ``slot_name``: The resource slot's main key name.  The plugin's resource slot name has the form of ``"<slot_name>.<subtype>"``, where the subtype may be something such as ``device``, ``shares`` (for fractionally-allocatable ones), or other arbitrary strings like ``10g-mig`` for CUDA MIG devices.

* ``device_plugin_name``: The class name to use as the actual implementation. Currently there are two: ``CUDADevice`` and ``MockDevice``.

* ``human_readable_name``: The device name displayed in the UI.

* ``description``: The device description displayed in the UI.

* ``display_icon``: The device icon type displayed in the UI.

* ``dispaly_unit``: The resource slot unit displayed in the UI, alongside the amount numbers.

* ``number_format``: The number formatting string used for the UI.

* ``devices``: The list of mocked device declarations

  * ``mother_uuid``: The unique ID of the device, which may be random-generated

  * ``model_name``: The model name to report to the manager as metadata

  * ``numa_node``: The NUMA node index to place this device.

  * ``smp_count``: The number of processing cores (for instances, the number of SMPs of CUDA GPUs)

  * ``memory_size``: The size of on-device memory represented as human-readable binary sizes

  * ``is_mig_devices``: (CUDA-specific) whether this device is a MIG slice or a full device

Activating the mock-accelerator plugin
--------------------------------------

Add ``"ai.backend.accelerator.mock"`` to the ``agent.toml``'s ``[agent].allowed-compute-plugins`` field.
Then restart the agent.
