Rate Limiting
=============

The API server imposes a rate limit to prevent clients from overloading the server.
The limit is applied to the last *N* minutes at ANY moment (*N* is 15 minutes by default).

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
     - The maximum allowed number of requests during the rate-limit window.
   * - ``X-RateLimit-Remaining``
     - The number of further allowed requests left for the moment.
   * - ``X-RateLimit-Window``
     - The constant value representing the window size in seconds.
       (e.g., 900 means 15 minutes)

       .. versionchanged:: v3.20170615

          Deprecated ``X-RateLimit-Reset`` and transitional ``X-Retry-After`` as we have implemented a rolling counter that measures last 15 minutes API call counts at any moment.

When the limit is exceeded, further API calls will get HTTP 429 "Too Many Requests".
If the client seems to be DDoS-ing, the server may block the client forever without prior notice.
