Installation from multipass
============================



Multipass Enviroment Setting
----------------------------------------------------------------------------------

Download appropriate version of multipass here.

https://multipass.run/

After finish downloading, you may try a few lines of code to verify multipass successfully download.

Launch an instance (by default you get the current Ubuntu LTS)

.. code-block:: console

   $ multipass launch --name <instance-name>

or you can specify cpu core, memory size, and disk size.

.. code-block:: console

   $ multipass launch --cpus <cpu-core> --disk <disk-size M/G> --memory <memory-size M/G> --name <instance-name> <ubuntu lts version>
   
For example

.. code-block:: console      

   $ multipass launch --cpus 4 --disk 100G --memory 6G --name foo 20.04

Recommended specification is more then 4 cpu-cores, disk is more then 100G and memory is more then 6G.

`launch failed: Downloaded image hash does not match`
https://github.com/canonical/multipass/issues/1299

Once the VM instance setup is complete, run the following command.

.. code-block:: console

   $ multipass shell <instance-name>

Install Backend.AI on Multipass
--------------------------------

First, install docker libraries.
Second, give permission to user for executing docker. 
Third, clone git repository.
Last, excute install-dev.sh.

.. code-block:: console

   $ git clone https://github.com/lablup/backend.ai
   $ cd ./backend.ai
   $ ./scripts/install-dev.sh

If you encounter any issue with docker, https://docs.docker.com/engine/install/ubuntu/ this link may help you.
