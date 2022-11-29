Manager GraphQL API
===================

Backend.AI GraphQL API is for developing in-house management consoles.

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
   Using this you do not have to add any custom header configurations to your favorite API development tools such as `GraphiQL <https://github.com/graphql/graphiql>`_.

.. toctree::
   :maxdepth: 2

   domains
   scaling-groups
   resource-presets
   agents
   users
   groups
   keypairs
   keypair-resource-policies
   sessions
   vfolders
   images

Basics of GraphQL
-----------------

The Admin API uses a single GraphQL endpoint for both queries and mutations.

.. code-block:: text

   https://api.backend.ai/admin/graphql

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


Common Object Types
~~~~~~~~~~~~~~~~~~~

``ResourceLimit`` represents a range (``min``, ``max``) of specific resource slot (``key``).
The ``max`` value may be the string constant "Infinity" if not specified.

.. code-block:: graphql

   type ResourceLimit {
     key: String
     min: String
     max: String
   }

``KVPair`` is used to represent a mapping data structure with arbitrary (runtime-determined) key-value pairs, in contrast to other data types in GraphQL which have a set of predefined static fields.

.. code-block:: graphql

   type KVPair {
     key: String
     value: String
   }


Pagination Convention
~~~~~~~~~~~~~~~~~~~~~

GraphQL itself does not enforce how to pass pagination information when
querying multiple objects of the same type.

We use a pagination convention as described below:

.. code-block:: graphql

   interface Item {
     id: UUID
     # other fields are defined by concrete types
   }

   interface PaginatedList(
     offset: Integer!,
     limit: Integer!,
     # some concrete types define ordering customization fields:
     #   order_key: String,
     #   order_asc: Boolean,
     # other optional filter condition may be added by concrete types
   ) {
     total_count: Integer
     items: [Item]
   }

``offset`` and ``limit`` are interpreted as SQL's offset and limit clauses.
For the first page, set the offset to zero and the limit to the page size.
The ``items`` field may contain from zero up to ``limit`` items.
Use ``total_count`` field to determine how many pages are there.
Fields that support pagination is suffixed with ``_list`` in our schema.


Custom Scalar Types
~~~~~~~~~~~~~~~~~~~

* ``UUID``: A hexademically formatted (8-4-4-4-12 alphanumeric characters connected via single hyphens) UUID values represented as ``String``
* ``DateTime``: An ISO-8601 formatted date-time value represented as ``String``
* ``BigInt``: GraphQL's integer is officially 32-bits only,
  so we define a "big integer" type which can represent from -9007199254740991 (-2\ :sup:`53`\ +1) to 9007199254740991 (2\ :sup:`53`\ -1) (or, ±(8 PiB - 1 byte).
  This range is regarded as a "safe" (i.e., can be compared without loosing precision) integer range in most Javascript implementations which represent numbers in the IEEE-754 double (64-bit) format.
* ``JSONString``: It contains a stringified JSON value, whereas the whole query result is already a JSON object.  A client must parse the value *again* to get an object representation.


Authentication
~~~~~~~~~~~~~~

The admin API shares the same authentication method of the user API.


Versioning
~~~~~~~~~~

As we use GraphQL, there is no explicit versioning.
Check out the descriptions for each API for its own version history.
