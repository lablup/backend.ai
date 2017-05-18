Rate Limiting
=============

The API server imposes a rate limit to prevent clients from overloading the server.
The window size of rate limiting is 15 minutes.

For public non-authorized APIs such as version checks, the server uses the client's IP address seen by the server to impose rate limits.
Due to this, please keep in mind that large-scale NAT-based deployments may encounter the rate limits sooner than expected.
For authorized APIs, it uses the access key in the authorization header to impose rate limits.
The rate limit includes both all successful and failed requests.

Upon a valid request, the HTTP response contains the following header fields to help the clients flow-control their requests.

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - HTTP Headers
     - Values
   * - ``X-RateLimit-Limit``
     - The maximum allowed number of requests per each rate-limit windows (15-minutes).
   * - ``X-RateLimit-Remaining``
     - The number of requests left for the time window. If zero, the client should wait for the time specified by ``X-Retry-After``.
   * - ``X-Retry-After``
     - The time to wait until the current rate limit window resets, in milli-seconds.

       .. versionchanged:: v3.20170615

          Formerly this header was named ``X-RateLimit-Reset``, but it has caused confusion with GitHub API which uses this name for absolute timestamp.

When the limit is exceeded, further API calls will get HTTP 429 "Too Many Requests".
If the client seems to be DDoS-ing, the server may block the client without prior notice.
