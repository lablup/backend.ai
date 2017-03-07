Conventions
===========

Parameters in URI and JSON Request Body
---------------------------------------

The parameters with colon prefixes (e.g., ``:id``) are part of the query URI and must be encoded using a proper URI-compatible encoding schemes such as ``encodeURIComponent(value)`` in Javascript and ``urllib.parse.quote(value, safe='~()*!.\'')`` in Python 3+.

Other parameters should be set as a key-value pair of the JSON object in the HTTP request body.
The API server accepts both UTF-8 encoded bytes and standard-compliant Unicode-escaped strings in the body.

HTTP Status Codes and JSON Response Body
----------------------------------------

All JSON responses described here are only for successful returns (HTTP status 2xx).
For failures (HTTP status 4xx/5xx), the JSON response is an object that contains at least two keys: ``type`` which uniquely identifies the failure reason as an URI and ``title`` for human-readable error messages.
Some failures may return extra structured information as additional key-value pairs.
We use `RFC 7807 <https://tools.ietf.org/html/rfc7807>`_-style problem detail description returned in JSON of the response body.

API Versioning
--------------

A version string of the Sorna API uses two parts: a major revision (prefixed with ``v``) and minor release dates after a dot following the major revision.
For example, ``v23.20250101`` indicates a 23rd major revision with a minor release at January 1st in 2025.

We keep backward compatibility between minor releases within the same major version.
Therefore, all API query URLs are prefixed with the major revision, such as ``/v2/kernel/create``.
Minor releases may introduce new parameters and response fields but no URL changes.
Accessing unsupported major revision returns HTTP 404 Not Found.

A client must specify the API version in the HTTP request header named ``X-Sorna-Version``.
To check the latest minor release date of a specific major revision, try a GET query to the URL with only the major revision part (e.g., ``/v2``).
The API server will return a JSON string in the response body containing the full version.
When querying the API version, you do not have to specify the authorization header and the rate-limiting is enforced per the client IP address.
Check out more details about :doc:`auth` and :doc:`ratelimit`.

Example version check response body:

.. code-block:: json

   {
      "version": "v2.20170315"
   }
