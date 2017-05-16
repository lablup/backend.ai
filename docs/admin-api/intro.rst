Introduction
============

Sorna Admin API is for developing in-house management consoles.
It requires a privileged keypair to invoke the admin APIs.
It shares :doc:`the same request/response conventions of the user API </user-api/intro>`.

Rate-limiting
-------------

The admin API does not have rate-limits.
The Sorna gateway serves all incoming requests as much as possible for authenticated requests.

Versioning
----------

To match the pace with the user API, the version of the admin API is paired with the corresponding user API.
As we introduce the admin API since the user API v2, its initial version begins with v2.
