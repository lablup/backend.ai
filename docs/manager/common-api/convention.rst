API and Document Conventions
============================

HTTP Methods
------------

We use the standard HTTP/1.1 methods (`RFC-2616 <https://tools.ietf.org/html/rfc2616>`_), such as ``GET``, ``POST``, ``PUT``, ``PATCH`` and ``DELETE``, with some additions from WebDAV (`RFC-3253 <https://tools.ietf.org/html/rfc3253>`_) such as ``REPORT`` method to send JSON objects in request bodies with ``GET`` semantics.

If your client runs under a restrictive environment that only allows a subset of above methods, you may use the universal ``POST`` method with an extra HTTP header like ``X-Method-Override: REPORT``, so that the Backend.AI gateway can recognize the intended HTTP method.

Parameters in URI and JSON Request Body
---------------------------------------

The parameters with *colon prefixes* (e.g., ``:id``) are part of the URI path and must be encoded using a proper URI-compatible encoding schemes such as ``encodeURIComponent(value)`` in Javascript and ``urllib.parse.quote(value, safe='~()*!.\'')`` in Python 3+.

Other parameters should be set as a key-value pair of the JSON object in the HTTP request body.
The API server accepts both UTF-8 encoded bytes and standard-compliant Unicode-escaped strings in the body.

HTTP Status Codes and JSON Response Body
----------------------------------------

The API responses always contain a root JSON object, regardless of success or failures.

For successful responses (HTTP status 2xx), the root object has a varying set of key-value pairs depending on the API.

For failures (HTTP status 4xx/5xx), the root object contains at least two keys: ``type`` which uniquely identifies the failure reason as an URI and ``title`` for human-readable error messages.
Some failures may return extra structured information as additional key-value pairs.
We use `RFC 7807 <https://tools.ietf.org/html/rfc7807>`_-style problem detail description returned in JSON of the response body.

JSON Field Notation
-------------------

Dot-separated field names means a nested object.
If the field name is a pure integer, it means a list item.

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Example
     - Meaning
   * - ``a``
     - The attribute ``a`` of the root object.
       (e.g., ``123`` at ``{"a": 123}``)
   * - ``a.b``
     - The attribute ``b`` of the object ``a`` on the root.
       (e.g., ``456`` at ``{"a": {"b": 456}}``)
   * - ``a.0``
     - An item in the list ``a`` on the root.
       ``0`` means an arbitrary array index, not the specific item at index zero.
       (e.g., any of ``13``, ``57``, ``24``, and ``68`` at ``{"a": [13, 57, 24, 68]}``)
   * - ``a.0.b``
     - The attribute ``b`` of an item in the list ``a`` on the root.
       (e.g., any of ``1``, ``2``, and ``3`` at ``{"a": [{"b": 1}, {"b": 2}, {"b": 3}]}``)

JSON Value Types
----------------

This documentation uses a type annotation style similar to `Python's typing module <https://docs.python.org/3/library/typing.html>`_, but with minor intuitive differences such as lower-cased generic type names and wildcard as asterisk ``*`` instead of ``Any``.

The common types are ``array`` (JSON array), ``object`` (JSON object), ``int`` (integer-only subset of JSON number), ``str`` (JSON string), and ``bool`` (JSON ``true`` or ``false``).
``tuple`` and ``list`` are aliases to ``array``.
Optional values may be omitted or set to ``null``.

We also define several custom types:

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Type
     - Description
   * - ``decimal``
     - Fractional numbers represented as ``str`` not to loose precision. (e.g., to express money amounts)
   * - ``slug``
     - Similar to ``str``, but the values should contain only alpha-numeric characters, hyphens, and underscores.
       Also, hyphens and underscores should have at least one alphanumeric neighbor as well as cannot become the prefix or suffix.
   * - ``datetime``
     - ISO-8601 timestamps in ``str``, e.g., ``"YYY-mm-ddTHH:MM:SS.ffffff+HH:MM"``.
       It may include an optional timezone information. If timezone is not included, the value is assumed to be UTC.
       The sub-seconds parts has at most 6 digits (micro-seconds).
   * - ``enum[*]``
     - Only allows a fixed/predefined set of possible values in the given parametrized type.

API Versioning
--------------

A version string of the Backend.AI API uses two parts: a major revision (prefixed with ``v``) and minor release dates after a dot following the major revision.
For example, ``v23.20250101`` indicates a 23rd major revision with a minor release at January 1st in 2025.

We keep backward compatibility between minor releases within the same major version.
Therefore, all API query URLs are prefixed with the major revision, such as ``/v2/kernel/create``.
Minor releases may introduce new parameters and response fields but no URL changes.
Accessing unsupported major revision returns HTTP 404 Not Found.

.. versionchanged:: v3.20170615
   Version prefix in API queries are deprecated. (Yet still supported currently)
   For example, now users should call ``/kernel/create`` rather than ``/v2/kernel/create``.

A client must specify the API version in the HTTP request header named ``X-BackendAI-Version``.
To check the latest minor release date of a specific major revision, try a GET query to the URL with only the major revision part (e.g., ``/v2``).
The API server will return a JSON string in the response body containing the full version.
When querying the API version, you do not have to specify the authorization header and the rate-limiting is enforced per the client IP address.
Check out more details about :doc:`auth` and :doc:`ratelimit`.

Example version check response body:

.. code-block:: json

   {
      "version": "v2.20170315"
   }
