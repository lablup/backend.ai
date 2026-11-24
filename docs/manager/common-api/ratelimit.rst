Rate Limiting
=============

The API server imposes a rate limit to prevent clients from overloading the server.
The limit is applied per fixed window, 15 minutes by default:
the first request from a caller opens a window, every request until it expires counts against the same limit,
and the next request after that opens a new window with a fresh count.

The window length is the ``rate-limit-window-seconds`` value of the manager's ``api`` configuration section.
Setting it in etcd (``ai/backend/config/manager/api/rate-limit-window-seconds``) applies it to every manager without a restart.
A changed length applies to windows opened after the change, and open windows expire as they were opened.
A keypair's rate limit is the number of requests per window, so shortening the window raises the request rate the same limit allows.

For public non-authorized APIs such as version checks, the server uses the client's IP address seen by the server to impose rate limits.
Due to this, please keep in mind that large-scale NAT-based deployments may encounter the rate limits sooner than expected.
For authorized APIs, it counts per user, whichever of their keypairs signed the request, and takes the limit from the keypair they marked default.
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
     - The number of further allowed requests left in the current window.
   * - ``X-RateLimit-Reset``
     - The number of seconds until the current window expires and the count starts over.

       Deprecated in v3.20170615 along with the transitional ``X-Retry-After`` when the rolling counter was introduced,
       and reinstated with the fixed window.
   * - ``X-RateLimit-Window``
     - The length of the current window in seconds.
       (e.g., 900 means 15 minutes)

When the limit is exceeded, further API calls will get HTTP 429 "Too Many Requests".
If the client seems to be DDoS-ing, the server may block the client forever without prior notice.
