.. role:: raw-html-m2r(raw)
   :format: html

Resource Management
===================

Resource slots
--------------

Backend.AI abstracts each different type of computing resources as a "resource slot".
Resource slots are distinguished by its name consisting of two parts: the device name and the slot name.

.. list-table::
   :header-rows: 1

   * - Resource slot name
     - Device name
     - Slot name
   * - ``cpu``
     - ``cpu``
     - (implicitly defined as ``root``)
   * - ``mem``
     - ``mem``
     - (implicitly defined as ``root``)
   * - ``cuda.device``
     - ``cuda``
     - ``device``
   * - ``cuda.shares``
     - ``cuda``
     - ``shares``
   * - ``cuda.mig-2c10g``
     - ``cuda``
     - ``mig-2c10g``

Each resource slot has a slot type as follows:

.. list-table::
   :header-rows: 1

   * - Slot type
     - Meaning
     - Examples
   * - ``COUNT``
     - The value of the resource slot is an integer or decimal to represent how many of the device(s) are available/allocated.
       It may also represent fractions of devices.
     - ``cpu``, ``cuda.device``, ``cuda.shares``
   * - ``BYTES``
     - The value of the resource slot is an integer to represent how many bytes of the resources are available/allocated.
     - ``mem``
   * - ``UNIQUE``
     - Only "each one" of the device can be allocated to each different kernel exclusively.
     - ``cuda.mig-10g``

Compute plugins
---------------

Backend.AI administrators may install one or more compute plugins to each agent.
Without any plugin, only the intrinsic ``cpu`` and ``mem`` resource slots are available.

Each compute plugin may declare one or more resource slots.
The plugin is invoked upon startup of the agent to get the list of devices and the resource slots to report.
Administrators can inspect the per-agent accelerator details provided by the compute plugins in the control panel.

The most well-known compute plugin is ``cuda_open``, which is included in the open source version.
It declares ``cuda.device`` resource slot that represents each NVIDIA GPU as one unit.

There is a special compute plugin to simulate non-existent devices: ``mock``.
Developers may put a local configuration to declare an arbitrary set of devices and resource slots to test the schedulers and the frontend.
It is useful to develop integrations with new hardware devices before you get the actual devices on your hands.

.. _concept-resource-group:
Resource groups
---------------

Resource group is a logical group of the Agents with independent schedulers.
Each agent belongs to a single resource group only.
It self-reports which resource group to join when sending the heartbeat messages, but the specified resource group must exist in prior.

.. seealso::

   :ref:`concept-scheduler`
