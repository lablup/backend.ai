Upgrade existing Backend.AI cluster
===================================

.. note::

  It is considered as an ideal situation to terminate every workload (including compute sessions)
  before initiating upgrade. There may be unexpected side effects when performing a rolling upgrade.

.. note::

  Unless you know how each components interacts with others, it is best to retain a single version
  installed across every parts of Backend.AI cluster.


Performing minor upgrade
------------------------

A minor upgrade means upgrading a Backend.AI cluster while keeping the major version same (e.g. 24.03.0 to 24.03.1).
Usually changes for minor upgrades are meant for fixing critical bugs rather than introducing new features.
In general there should be only trivial changes between minor versions that won't affect how users interact with the software.
To plan the upgrade, first check following facts:

* Read every bit of the release changelog.

* Run the minor upgrade consecutively version by version.

  Do not skip the intermediate version event when trying to upgrade an outdated cluster.

* Check if there is a change at the database schema.

  As it is mentioned at the beginning it is best to maintain database schema as concrete, but in rare situations it is
  inevitable to alter it.

* Make sure every mission critical workloads are shut down when performing a rolling upgrade.


Upgrading Backend.AI Manager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Stop the manager process running at server.
2. Upgrade the Python package by executing ``pip install -U backend.ai-manager==<target version>``.
3. Match databse schema with latest by executing ``alembic upgrade head``.
4. Restart the process.


Upgrading other Backend.AI components
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Stop the ongoing server process.
2. Upgrade the Python package by executing ``pip install -U backend.ai-<component name>==<target version>``.
3. Restart the process.


Others
~~~~~~

Depending on the situation there might be an additional process required which must be manually performed by the system administrator.
Always check out the release changelog to find out whether it indicates to do so.


Performing major upgrade
------------------------

A major upgrade involves significant feature additions and structural changes.
DO NOT perform rolling upgrades in any cases.
Please make sure to shutdown every workload of the cluster and notify users of a relatively prolonged downtime.

To plan the upgrade, first check following facts:

* Upgrade the Backend.AI cluster to the very latest minor version of the prior release before starting major version upgrade.

  By the policy, it is not allowed to upgrade the cluster to the latest major on a cluster with an outdated minor version installed.

* Do not skip the intermediate major version

  You can not skip the stop-gap version!


Example of allowed upgrade paths
~~~~~~~~~~~~~~~~~~~~~
* **23.09.10 (latest in the previous major)** -> 24.03.0
* **23.09.10 (latest in the previous major)** -> 24.03.5
* 23.09.9 -> **23.09.10 (latest in the previous major)** -> 24.03.0
* 23.03.11 -> 23.09.0 -> 23.09.1 -> ... -> **23.09.10 (latest in the previous major)** -> 24.03.0
* ...

Example of forbidden upgrade paths
~~~~~~~~~~~~~~~~~~~~~~~
* 23.09.9 (a non-latest minor version of the prior release) -> 24.03.0
* 23.03.0 (not a direct prior release) -> 24.03.0
* ...


Upgrading Backend.AI Manager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Stop the manager process running at server.
2. Upgrade the Python package by executing ``pip install -U backend.ai-manager==<target version>``.
3. Match databse schema with latest by executing ``alembic upgrade head``.
4. Fill out any missing DB revisions by executing ``backend.ai mgr schema apply-mission-revisions <version number of previous Backend.AI software>``.
5. Start the process again.


Upgrading other Backend.AI components
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Stop the ongoing server process.
2. Upgrade the Python package by executing ``pip install -U backend.ai-<component name>==<target version>``.
3. Restart the process.


Others
~~~~~~

Depending on the situation there might be an additional process required which must be manually performed by system administrator.
Always check out the release changelog to find out whether it indicates to do so.
