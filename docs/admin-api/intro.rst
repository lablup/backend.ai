Introduction
============

Backend.AI's Admin API is for developing in-house management consoles.

There are two modes of operation:

1. Full admin access: you can query all information of all users. It requires a
   privileged keypair.
2. Restricted owner access: you can query only your own information. The server
   processes your request in this mode if you use your own plain keypair.

Basics of GraphQL
-----------------

The Admin API uses a single GraphQL endpoint for both queries and mutations.

.. code-block:: text

   https://api.sorna.io/v3/admin/graphql

For more information about GraphQL concepts and syntax, please visit the following site(s):

* `GraphQL official website <http://graphql.org/>`_


Pagination Convention
~~~~~~~~~~~~~~~~~~~~~

GraphQL itself does not enforce how to pass pagination information when
querying multiple objects of the same type.

We use a de-facto standard pagination convention as described below:

TODO


Authentication
--------------

The admin API shares the same authentication method of the user API.


Versioning
----------

As we use GraphQL, there is no explicit versioning.
You can use any version prefix in the endpoint URL, from ``v1`` to ``vN`` where
``N`` is the latest major API version.
