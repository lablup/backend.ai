Introduction
============

Backend.AI's Admin API is for developing in-house management consoles.

There are two modes of operation:

1. Full admin access: you can query all information of all users. It requires a
   privileged keypair.
2. Restricted owner access: you can query only your own information. The server
   processes your request in this mode if you use your own plain keypair.

.. warning::

   The Admin API *only* accepts authenticated requests.

.. tip::

   To test and debug with the Admin API easily, try the proxy mode of `the official Python client <https://pypi.python.org/pypi/backend.ai-client>`_.
   It provides an insecure (non-SSL, non-authenticated) local HTTP proxy where all the required authorization headers are attached from the client configuration.
   Using this you do not have to add any custom header configurations to your favorite API development tools.

Basics of GraphQL
-----------------

The Admin API uses a single GraphQL endpoint for both queries and mutations.

.. code-block:: text

   https://api.sorna.io/v3/admin/graphql

For more information about GraphQL concepts and syntax, please visit the following site(s):

* `GraphQL official website <http://graphql.org/>`_


HTTP Request Convention
~~~~~~~~~~~~~~~~~~~~~~~

A client must use the ``POST`` HTTP method.
The server accepts a JSON-encoded body with an object containing two fields: ``query`` and ``variables``,
pretty much like other GraphQL server implementations.

.. warning::

   Currently the API gateway does not support schema discovery which is often
   used by API development tools such as Insomnia and GraphiQL.


Field Naming Convention
~~~~~~~~~~~~~~~~~~~~~~~

We do *NOT* automatically camel-case our field names.
All field names follow the underscore style, which is common in the Python world
as our server-side framework uses Python.


Pagination Convention
~~~~~~~~~~~~~~~~~~~~~

GraphQL itself does not enforce how to pass pagination information when
querying multiple objects of the same type.

We use a de-facto standard pagination convention as described below:

TODO

Custom Scalar Types
~~~~~~~~~~~~~~~~~~~

* ``UUID``: A hexademically formatted (8-4-4-4-12 alphanumeric characters connected via single hyphens) UUID values represented as ``String``
* ``DateTime``: An ISO-8601 formatted date-time value represented as ``String``


Authentication
~~~~~~~~~~~~~~

The admin API shares the same authentication method of the user API.


Versioning
~~~~~~~~~~

As we use GraphQL, there is no explicit versioning.
You can use any version prefix in the endpoint URL, from ``v1`` to ``vN`` where
``N`` is the latest major API version.
