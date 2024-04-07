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

Minor upgrade means upgrading a Backend.AI cluster while keeping major version same (e.g. 24.03.0 to 24.03.1). 
Usually changes are meant for fixing bugs that are critial but not to introduce a new major feature, so in general 
there should be not that much of changes between version being upgraded and will upgraded to in terms of how individual 
users interact with the software.
To plan the upgrade, first check following facts:

* Read every bit of release changelog

* Always try to upgrade the version consecutively

  Do not skip the intermediate version event when trying to upgrade outdated cluster.

* Check if there is a change at the database schema

  As it is mentioned at the beginning it is best to maintain database schema as concrete, but in rare situations it is 
  inevitable to alter it. 

* Make sure every mission critical workloads are shut down when performing a rolling upgrade


Upgrading Backend.AI Manager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Stop the manager process running at server.
2. Upgrade the Python package by executing `pip install -U backend.ai-manager==<target version>`.
3. Match databse schema with latest by executing `alembic upgrade head`.
4. Restart the process.


Upgrading other Backend.AI components
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Stop the ongoing server process.
2. Upgrade the Python package by executing `pip install -U backend.ai-<component name>==<target version>`.
3. Restart the process.


Others
~~~~~~

Depending on the situation there might be an additional process required which must be manually performed by system administrator. 
Always check out the release changelog to find out whether it indicates to do so.


Performing major upgrade
------------------------

Major upgrade implies that there will be significant changes involved between the versions. You should not try to perform 
a rolling upgrade in any cases. Please make sure to stop every workload and notify users of an abundant amount of downtime.

To plan the upgrade, first check following facts:

* Upgrade Backend.AI cluster to very latest minor version of prior release before starting major version upgrade

  By policy it is not allowed to upgrade the cluster to latest major on a cluster with outdated minor version installed.

* Do not skip the intermediate major version

  You can not skip the stop-gap version! 


Allowed upgrade paths
~~~~~~~~~~~~~~~~~~~~~
* 23.09.10 -> 24.03.0
* 23.09.10 -> 24.03.5
* 23.09.9 -> 23.09.10 -> 24.03.0
* 23.03.11 -> 23.09.0 -> 23.09.1 -> ... -> 23.09.10 -> 24.03.0

Forbidden upgrade paths
~~~~~~~~~~~~~~~~~~~~~~~
* 23.09.9 -> 24.03.0
* 23.03.0 -> 24.03.0


Upgrading Backend.AI Manager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Stop the manager process running at server.
2. Upgrade the Python package by executing `pip install -U backend.ai-manager==<target version>`.
3. Match databse schema with latest by executing `alembic upgrade head`.
4. Fill out any missing DB revisions by executing `backend.ai mgr schema apply-mission-revisions <version number of previous Backend.AI software>`.
5. Start the process again.


Upgrading other Backend.AI components
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Stop the ongoing server process.
2. Upgrade the Python package by executing `pip install -U backend.ai-<component name>==<target version>`.
3. Restart the process.


Others
~~~~~~

Depending on the situation there might be an additional process required which must be manually performed by system administrator. 
Always check out the release changelog to find out whether it indicates to do so.
