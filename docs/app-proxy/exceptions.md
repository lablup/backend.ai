# Backend.AI AppProxy error codes
## Common
### AssertionError
This usually means the integrity of data types are broken. Hand out full log footage at that time and consult with DevOps team for more information.

### E00001: Server misconfigured - {component}:{config key}
Occurs when server reads unexpected config value from its local config file. Check configuration file of faulty component and see if there is any misconfigured value.

### E00002: No such {component-:coordinator}:{object}
- When component is not specified or is coordinator
This happens when there is no matching database record of target object.
- When component is worker
This happens when there is no matching database record of target object under coordinator DB.

## Proxy Coordinator
### E10001: Proxy worker not responding
This happens when proxy worker does not respond to coordinator's configuration request. Contact administrator to check for activeness of proxy worker.
## Proxy Worker
### E20001: Route event not delivered to worker
This states Proxy Worker has not received circuit creation request event from Proxy Coordinator. This can happen either when proxy coordinator or proxy worker has lost contact with its redis backend.

### E20002: Protocol not available as interactive app
This error can happen when users try to launch interactive app with non-supported protocol (e.g. gRPC / HTTP2). AppProxy prohibits such beahivor, hence facing this error is intended.

### E20003: Timed out while waiting for proxy frontend to set up
This happens when proxy frontend could not initiate tunnel connection between frontend and backend (server spawned under Backend.AI Kernel) in an abundant amount of time. In most cases, this error is a side effect of other fundamental issues. Check out other logs from proxy worker or target container for more information.

### E20004: Authorization cookie not provided
Raised when request from user does not include required sets of cookie. Check your browser settings and see if something is blocking your cookie setup.

### E20005: Invalid authorization cookie
Raised when authorization credentials sent does not match the record filed on the server. Clear your browser cache and retry from launching the app.

### E20006: Authorization header not provided
Raised when inference endpoint requires valid authorization token but is not supplied.

### E20007: Unsupported authorization method {auth_type}
Raised when invalid authorization method is defined on `Authorization` header. At this moment Backend.AI only supports `BackendAI` authorization method.

### E20008: Authorization token mismatch
Raised when invalid authorization token is supplied.

### E20009: Subdomain {subdomain} not registered
This happens when requested subdomain is not recognized from proxy frontend. Check if there is a typo at the hostname. If not, try again to create the app.

### E20010: nghttpx terminated unexpectedly
Printed when nghttpx process terminates without explicit request. Check other logs beginning with `nghttpx:` for more details.

### E20011: Not supported for inference apps
This error can happen when users try to launch inference app from browser. AppProxy prohibits such beahivor, hence facing this error is intended.

### E20012: Not supported for interactive apps
This error can happen when users try to launch interactive app from manager. AppProxy prohibits such beahivor, hence facing this error is intended.

### E20013: Failed to register worker to coordinator
This error occurs when worker failed to advertise itself to coordinator. Check coordinator log for more information.