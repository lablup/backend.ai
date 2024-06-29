.. role:: raw-html-m2r(raw)
   :format: html


Version Numbering
=================

* Version numbering uses ``x.y.z`` format (where ``x``\ , ``y``\ , ``z`` are integers).
* Mostly, we follow `the calendar versioning scheme <https://calver.org/>`_.
* ``x.y`` is a release branch name (major releases per 6 months).

  * When ``y`` is smaller than 10, we prepend a zero sign like ``05`` in the version numbers (e.g., ``20.09.0``).
  * When referring the version in other Python packages as requirements, you need to strip the leading zeros (e.g., ``20.9.0`` instead of ``20.09.0``) because Python setuptools normalizes the version integers.

* ``x.y.z`` is a release tag name (patch releases).
* When releasing ``x.y.0``\ :

  * Create a new ``x.y`` branch, do all bugfix/hotfix there, and make ``x.y.z`` releases there.
  * All fixes must be *first* implemented on the ``main`` branch and then *cherry-picked* back to ``x.y`` branches.

    * When cherry-picking, use the ``-e`` option to edit the commit message.\ :raw-html-m2r:`<br>`
      Append ``Backported-From: main`` and ``Backported-To: X.Y`` lines after one blank line at the end of the existing commit message.

  * Change the version number of ``main`` to ``x.(y+1).0.dev0``
  * There is no strict rules about alpha/beta/rc builds yet. We will elaborate as we scale up.\ :raw-html-m2r:`<br>`
    Once used, alpha versions will have ``aN`` suffixes, beta versions ``bN`` suffixes, and RC versions ``rcN`` suffixes where ``N`` is an integer.

* New development should go on the ``main`` branch.

  * ``main``\ : commit here directly if your changes are a self-complete one as a single commit.
  * Use both short-lived and long-running feature branches freely, but ensure there names differ from release branches and tags.

* The major/minor (\ ``x.y``\ ) version of Backend.AI subprojects will go together to indicate compatibility.  Currently manager/agent/common versions progress this way, while client SDKs have their own version numbers and the API specification has a different ``vN.yyyymmdd`` version format.

  * Generally ``backend.ai-manager 1.2.p`` is compatible with ``backend.ai-agent 1.2.q`` (where ``p`` and ``q`` are same or different integers)

    * As of 22.09, this won't be guaranteed anymore.  All server-side core component versions should **exactly match** with others, as we release them at once from the mono-repo, even for those who do not have any code changes.

  * The client is guaranteed to be backward-compatible with the server they share the same API specification version.


Upgrading
=========

You can upgrade the installed Python packages using ``pip install -U ...`` command along with dependencies.

If you have cloned the stable version of source code from git, then pull and check out the next ``x.y`` release branch.
It is recommended to re-run ``pip install -U -r requirements.txt`` as dependencies might be updated.

For the manager, ensure that your database schema is up-to-date by running ``alembic upgrade head``. If you setup your development environment with Pants and ``install-dev.sh`` script, keep your database schema up-to-date via ``./py -m alembic upgrade head`` instead of plain alembic command above.

Also check if any manual etcd configuration scheme change is required, though we will try to keep it compatible and automatically upgrade when first executed.
