Authentication
==============

Access Tokens and Secret Key
----------------------------

To make requests to the API server, a client needs to get a pair of an access token and a secret key as sepcified in :doc:`/gsg/registration`.
The server uses access tokens to identify each client and secret keys to verify integrity of API requests as well as to authenticate clients.

For local deployments, you may create a master dummy pair in the configuration (TODO).

Common Structure of API Requests
--------------------------------

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - HTTP Headers
     - Values
   * - Method
     - GET / POST / PUT / PATCH / DELETE
   * - ``Content-Type``
     - Always should be ``application/json``
   * - ``Authorization``
     - Signature information generated as the section `Signing API Requests`_ describes.
   * - ``Date``
     - The date/time of the request formatted in RFC 8022 or ISO 8601.
       If no timezone is specified, UTC is assumed.
       The deviation with the server-side clock must be within 15-minutes.
   * - ``X-Sorna-Date``
     - Same as ``Date``. May be omitted if ``Date`` is present.
   * - ``X-Sorna-Version``
     - ``vX.yyymmdd`` where ``X`` is the major version and
       ``yyyymmdd`` is the minor release date of the specified API version.
       (e.g., 20160915)
   * - ``X-Sorna-Client-Token``
     - An optional, client-generated random string to allow the server to distinguish repeated duplicate requests.
       It is important to keep idempotent semantics with multiple retries for intermittent failures.
       (Not implemented yet)
   * - Body
     - JSON-encoded request parameters


Common Structure of API Responses
---------------------------------

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - HTTP Headers
     - Values
   * - Status code
     - API-specific HTTP-standard status codes. Responses commonly used throughout all APIs include 200, 201, 2014, 400, 401, 403, 404, 429, and 500, but not limited to.
   * - ``Content-Type``
     - ``application/json`` and its variants (e.g., ``application/problem+json`` for errors)
   * - ``Link``
     - Web link headers specified as in `RFC 5988 <https://tools.ietf.org/html/rfc5988>`_. Only optionally used when returning a collection of objects.
   * - ``X-RateLimit-*``
     - The rate-limiting information (see :doc:`/api/ratelimit`).
   * - Body
     - JSON-encoded results


Signing API Requests
--------------------

Each API request must be signed with a signature.
First, the client should generate a signing key derived from its API secret key and a string to sign by canonicalizing the HTTP request.

Generating a signing key
^^^^^^^^^^^^^^^^^^^^^^^^

Here is a Python code that derives the signing key from the secret key.
The key is nestedly signed against the current date (without time) and the API endpoint address.

.. code-block:: python

   import hashlib, hmac
   from datetime import datetime

   SECRET_KEY = b'abc...'

   def sign(key, msg):
     return hmac.new(key, msg, hashlib.sha256).digest()

   def get_sign_key():
     t = datetime.utcnow()
     k1 = sign(SECRET_KEY, t.strftime('%Y%m%d').encode('utf8'))
     k2 = sign(k1, b'your.sorna.api.endpoint')
     return k2


Generating a string to sign
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The string to sign is generated from the following request-related values:

* HTTP Method (uppercase)
* URI including query strings
* The value of ``Date`` (or ``X-Sorna-Date`` if ``Date`` is not present) formatted in ISO 8601 (``YYYYmmddTHHMMSSZ``) using the UTC timezone.
* The canonicalized header/value pair of ``Host``
* The canonicalized header/value pair of ``Content-Type``
* The canonicalized header/value pair of ``X-Sorna-Version``
* The hex-encoded hash value of body as-is. The hash function must be same to the one given in the ``Authorization`` header (e.g., SHA256).

To generate a string to sign, the client should join the above values using the newline (``"\n"``, ASCII 10) character.
All non-ASCII strings must be encoded with UTF-8.
To canonicalize a pair of HTTP header/value, first trim all leading/trailing whitespace characters (``"\n"``, ``"\r"``, ``" "``, ``"\t"``; or ASCII 10, 13, 32, 9) of its value, and join the lowercased header name and the value with a single colon (``":"``, ASCII 58) character.

The success example in `Example Requests and Responses`_ makes a string to sign as follows (where the newlines are ``"\n"``):

.. code-block:: text

   GET
   /v1
   20160930T01:23:45Z
   host:your.sorna.api.endpoint
   content-type:application/json
   x-sorna-version:v1.20160915
   e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855

In this example, the hash value  ``e3b0c4...`` is generated from an empty string using the SHA256 hash function since there is no body for GET requests.

Then, the client should calculate the signature using the derived signing key and the generated string with the hash function, as follows:

.. code-block:: python

   import hashlib, hmac

   str_to_sign = 'GET\n/v1...'
   sign_key = get_sign_key()  # see "Generating a signing key"
   m = hmac.new(sign_key, str_to_sign.encode('utf8'), hashlib.sha256)
   signature = m.hexdigest()


Attaching the signature
^^^^^^^^^^^^^^^^^^^^^^^

Finally, the client now should construct the following HTTP ``Authorization`` header:

.. code-block:: text

   Authorization: Sorna method=HMAC-SHA256, credential=<access-key>:<signature>


Example Requests and Responses
------------------------------

For the examples here, we use a dummy access key and secret key:

* Example access key: ``AKIAIOSFODNN7EXAMPLE``
* Example secret key: ``wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY``

Success example for checking the latest API version
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: text

   GET /v1 HTTP/1.1
   Host: your.sorna.api.endpoint
   Date: 20160930T01:23:45Z
   Authorization: Sorna method=HMAC-SHA256, credential=AKIAIOSFODNN7EXAMPLE:022ae894b4ecce097bea6eca9a97c41cd17e8aff545800cd696112cc387059cf
   Content-Type: application/json
   X-Sorna-Version: v1.20160915

.. code-block:: text

   HTTP/1.1 200 OK
   Content-Type: application/json
   Content-Language: en
   Content-Length: 31
   X-RateLimit-Limit: 2000
   X-RateLimit-Remaining: 1999
   X-RateLimit-Reset: 897065

   {
      "version": "v1.20160915"
   }
   

Failure example with a missing authorization header
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: text

   GET /v1/kernel/create HTTP/1.1
   Host: your.sorna.api.endpoint
   Content-Type: application/json
   X-Sorna-Date: 20160930T01:23:45Z
   X-Sorna-Version: v1.20160915

.. code-block:: text

   HTTP/1.1 401 Unauthorized
   Content-Type: application/problem+json
   Content-Language: en
   Content-Length: 139
   X-RateLimit-Limit: 2000
   X-RateLimit-Remaining: 1998
   X-RateLimit-Reset: 834821

   {
      "type": "https://sorna.io/problems/unauthorized",
      "title": "Unauthorized access",
      "detail": "Authorization header is missing."
   }


