Using Mocked Accelerators
=========================

For developers who do not have access to physical accelerator devices such as CUDA GPUs, we provide a mock-up plugin to simulate the system configuration with such devices, allowing development and testing of accelerator-related features in various components including the web UI.

Configuring the mock-accelerator plugin
---------------------------------------

Check out the examples in |examples|_.

.. |examples| replace:: the ``configs/accelerator`` directory
.. _examples: https://github.com/lablup/backend.ai/tree/main/configs/accelerator

Here are the description of each field:

* ``slot_name``: The resource slot's main key name.  The plugin's resource slot name has the form of ``"<slot_name>.<subtype>"``, where the subtype may be something such as ``device`` (default), ``shares`` (for the fractional allocation mode).
  For CUDA MIG devices, it becomes a string including the slice size from the device memory size such as ``10g-mig``.

  To configure the *fractional* allocation mode, you should also specify the **etcd** accelerator plugin configuration like the following JSON, where ``unit_mem`` and ``unit_proc`` is used as the divisor to calculate 1.0 fraction:

  .. code-block:: json

     {
        "config": {
          "plugins": {
            "accelerator": {
              "<slot_name>": {
                "allocation_mode": "fractional",
                "unit_mem": 1073741824,
                "unit_proc": 10
              }
            }
          }
        }
     }

  In the above example, the 10 subprocessors and 1 GiB of device memory is regarded as 1.0 fractional device.
  You may store it as a JSON file and put in the etcd configuration tree like:

  .. code-block:: console

     $ ./backend.ai mgr etcd put-json '' mydevice-fractional-mode.json

* ``device_plugin_name``: The class name to use as the actual implementation. Currently there are two: ``CUDADevice`` and ``MockDevice``.

* ``formats.<subtype>``: The tables for per-subtype formatting details

  * ``display_icon``: The device icon type displayed in the UI.

  * ``display_unit``: The resource slot unit displayed in the UI, alongside the amount numbers.

  * ``human_readable_name``: The device name displayed in the UI.

  * ``description``: The device description displayed in the UI.

  * ``number_format``: The number formatting string used for the UI.

    * ``binary``: A boolean flag to indicate whether to use the binary suffixes (divided by 2^(10n) instead of 10^(3n))

    * ``round_length``: The length of fixed points to wrap the numeric value of this resource slot. If zero, the number is treated as an integer.

* ``devices``: The list of mocked device declarations

  * ``mother_uuid``: The unique ID of the device, which may be random-generated

  * ``model_name``: The model name to report to the manager as metadata

  * ``numa_node``: The NUMA node index to place this device.

  * ``subproc_count``: The number of sub-processing cores (e.g., the number of streaming multi-processors of CUDA GPUs)

  * ``memory_size``: The size of on-device memory represented as human-readable binary sizes

  * ``is_mig_devices``: (CUDA-specific) whether this device is a MIG slice or a full device

Activating the mock-accelerator plugin
--------------------------------------

Add ``"ai.backend.accelerator.mock"`` to the ``agent.toml``'s ``[agent].allowed-compute-plugins`` field.
Then restart the agent.
