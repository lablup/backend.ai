# Backend.AI Proxy Coordinator API

> Version 24.03.0a1

Backend.AI Proxy Coordinator REST API specification

## Path Table

| Method | Path | Description |
| --- | --- | --- |
| DELETE | [/api/circuit/_/bulk](#deleteapicircuit_bulk) |  |
| GET | [/api/circuit/{circuit_id}](#getapicircuitcircuit_id) |  |
| DELETE | [/api/circuit/{circuit_id}](#deleteapicircuitcircuit_id) |  |
| GET | [/api/circuit/{circuit_id}/statistics](#getapicircuitcircuit_idstatistics) |  |
| POST | [/v2/conf](#postv2conf) |  |
| POST | [/v2/endpoints/{endpoint_id}](#postv2endpointsendpoint_id) |  |
| DELETE | [/v2/endpoints/{endpoint_id}](#deletev2endpointsendpoint_id) |  |
| POST | [/v2/endpoints/{endpoint_id}/token](#postv2endpointsendpoint_idtoken) |  |
| GET | [/health](#gethealth) |  |
| GET | [/health/status](#gethealthstatus) |  |
| GET | [/v2/proxy/{token}/{session_id}/add](#getv2proxytokensession_idadd) |  |
| GET | [/v2/proxy/auth](#getv2proxyauth) |  |
| GET | [/api/slots](#getapislots) |  |
| GET | [/api/worker](#getapiworker) |  |
| PUT | [/api/worker](#putapiworker) |  |
| GET | [/api/worker/{worker_id}](#getapiworkerworker_id) |  |
| PATCH | [/api/worker/{worker_id}](#patchapiworkerworker_id) |  |
| DELETE | [/api/worker/{worker_id}](#deleteapiworkerworker_id) |  |
| GET | [/api/worker/{worker_id}/circuits](#getapiworkerworker_idcircuits) |  |

## Reference Table

| Name | Path | Description |
| --- | --- | --- |
| X-BackendAI-Token | [#/components/securitySchemes/X-BackendAI-Token](#componentssecurityschemesx-backendai-token) |  |
| BulkRemoveCircuitsRequestModel | [#/components/schemas/BulkRemoveCircuitsRequestModel](#componentsschemasbulkremovecircuitsrequestmodel) |  |
| StubResponseModel | [#/components/schemas/StubResponseModel](#componentsschemasstubresponsemodel) |  |
| AppMode | [#/components/schemas/AppMode](#componentsschemasappmode) |  |
| FrontendMode | [#/components/schemas/FrontendMode](#componentsschemasfrontendmode) |  |
| ProxyProtocol | [#/components/schemas/ProxyProtocol](#componentsschemasproxyprotocol) |  |
| RouteInfo | [#/components/schemas/RouteInfo](#componentsschemasrouteinfo) |  |
| SerializableCircuit | [#/components/schemas/SerializableCircuit](#componentsschemasserializablecircuit) | Serializable representation of `ai.backend.appproxy.coordinator.models.Circuit` |
| CircuitStatisticsModel | [#/components/schemas/CircuitStatisticsModel](#componentsschemascircuitstatisticsmodel) |  |
| SessionConfig | [#/components/schemas/SessionConfig](#componentsschemassessionconfig) |  |
| ConfRequestModel | [#/components/schemas/ConfRequestModel](#componentsschemasconfrequestmodel) |  |
| TokenResponseModel | [#/components/schemas/TokenResponseModel](#componentsschemastokenresponsemodel) |  |
| EndpointConfig | [#/components/schemas/EndpointConfig](#componentsschemasendpointconfig) |  |
| EndpointTagConfig | [#/components/schemas/EndpointTagConfig](#componentsschemasendpointtagconfig) |  |
| InferenceAppConfig | [#/components/schemas/InferenceAppConfig](#componentsschemasinferenceappconfig) |  |
| EndpointCreationRequestModel | [#/components/schemas/EndpointCreationRequestModel](#componentsschemasendpointcreationrequestmodel) |  |
| EndpointCreationResponseModel | [#/components/schemas/EndpointCreationResponseModel](#componentsschemasendpointcreationresponsemodel) |  |
| EndpointAPITokenGenerationRequestModel | [#/components/schemas/EndpointAPITokenGenerationRequestModel](#componentsschemasendpointapitokengenerationrequestmodel) |  |
| EndpointAPITokenResponseModel | [#/components/schemas/EndpointAPITokenResponseModel](#componentsschemasendpointapitokenresponsemodel) |  |
| WorkerInfoModel | [#/components/schemas/WorkerInfoModel](#componentsschemasworkerinfomodel) |  |
| StatusResponseModel | [#/components/schemas/StatusResponseModel](#componentsschemasstatusresponsemodel) |  |
| AddRequestModel | [#/components/schemas/AddRequestModel](#componentsschemasaddrequestmodel) |  |
| AddResponseModel | [#/components/schemas/AddResponseModel](#componentsschemasaddresponsemodel) |  |
| ProxyRequestModel | [#/components/schemas/ProxyRequestModel](#componentsschemasproxyrequestmodel) |  |
| ProxyResponseModel | [#/components/schemas/ProxyResponseModel](#componentsschemasproxyresponsemodel) |  |
| ListSlotsRequestModel | [#/components/schemas/ListSlotsRequestModel](#componentsschemaslistslotsrequestmodel) |  |
| SlotModel | [#/components/schemas/SlotModel](#componentsschemasslotmodel) |  |
| ListSlotsResponseModel | [#/components/schemas/ListSlotsResponseModel](#componentsschemaslistslotsresponsemodel) |  |
| WorkerResponseModel | [#/components/schemas/WorkerResponseModel](#componentsschemasworkerresponsemodel) |  |
| WorkerListResponseModel | [#/components/schemas/WorkerListResponseModel](#componentsschemasworkerlistresponsemodel) |  |
| AppFilter | [#/components/schemas/AppFilter](#componentsschemasappfilter) |  |
| WorkerRequestModel | [#/components/schemas/WorkerRequestModel](#componentsschemasworkerrequestmodel) |  |
| CircuitListResponseModel | [#/components/schemas/CircuitListResponseModel](#componentsschemascircuitlistresponsemodel) |  |

## Path Details

***

### [DELETE]/api/circuit/_/bulk

- Description  
  
Removes circuit record from both coordinator and worker, in bulk.  
  
  
**Preconditions:**  
* Requires Worker token present at `X-BackendAI-Token` request header to work.  


#### RequestBody

- application/json

```ts
{
  circuit_ids?: string[]
}
```

#### Responses

- 200 

`application/json`

```ts
{
  success?: boolean //default: true
}
```

***

### [GET]/api/circuit/{circuit_id}

- Description  
  
Returns information of a circuit.  
  
  
**Preconditions:**  
* Requires Worker token present at `X-BackendAI-Token` request header to work.  


#### Responses

- 200 

`application/json`

```ts
// Serializable representation of `ai.backend.appproxy.coordinator.models.Circuit`
{
  // ID of circuit.
  id?: string
  // Name of the Backend.AI Kernel app circuit is hosting. Can be a blank string if circuit is referencing an inference app.
  app?: string
  // Protocol of the Backend.AI Kernel app.
  protocol?: #/components/schemas/ProxyProtocol
  // ID of the worker hosting the circuit.
  worker?: string
  // Application operation mode.
  app_mode?: #/components/schemas/AppMode
  // Frontend type of worker.
  frontend_mode?: #/components/schemas/FrontendMode
  envs: {
  }
  arguments: Partial(string) & Partial(null)
  // 
  // Shows if the circuit is open to public.
  // For interactive apps, this set as true means users without authorization cookie set will also be able to access application.
  // For inference apps it means that API will work without authorization token passed.
  // 
  open_to_public?: boolean
  // Comma separated list of CIDRs accepted as traffic source. null means the circuit is accessible anywhere.
  allowed_client_ips?: Partial(string) & Partial(null)
  // Occupied worker port. Only set if `frontend_mode` is `port`.
  port?: Partial(integer) & Partial(null)
  // Occupied worker subdomain. Only set if `frontend_mode` is `subdomain`.
  subdomain?: Partial(string) & Partial(null)
  // Session owner's UUID.
  user_id?: Partial(string) & Partial(null)
  // Model service's UUID. Only set if `app_mode` is inference.
  endpoint_id?: Partial(string) & Partial(null)
  route_info: {
    session_id: string
    session_name?: Partial(string) & Partial(null)
    kernel_host: string
    kernel_port: integer
    protocol: enum[http, grpc, h2, tcp]
    traffic_ratio?: number //default: 1
  }[]
  session_ids?: string[]
  created_at: string
  updated_at: string
}
```

***

### [DELETE]/api/circuit/{circuit_id}

- Description  
  
Removes circuit record from both coordinator and worker.  
  
  
**Preconditions:**  
* Requires Worker token present at `X-BackendAI-Token` request header to work.  


#### Responses

- 200 

`application/json`

```ts
{
  success?: boolean //default: true
}
```

***

### [GET]/api/circuit/{circuit_id}/statistics

- Description  
  
Lists statical informations about given circuit.  
  
  
**Preconditions:**  
* Requires Worker token present at `X-BackendAI-Token` request header to work.  


#### Responses

- 200 

`application/json`

```ts
{
  // ID of circuit.
  id?: string
  // Name of the Backend.AI Kernel app circuit is hosting. Can be a blank string if circuit is referencing an inference app.
  app?: string
  // Protocol of the Backend.AI Kernel app.
  protocol?: #/components/schemas/ProxyProtocol
  // ID of the worker hosting the circuit.
  worker?: string
  // Application operation mode.
  app_mode?: #/components/schemas/AppMode
  // Frontend type of worker.
  frontend_mode?: #/components/schemas/FrontendMode
  envs: {
  }
  arguments: Partial(string) & Partial(null)
  // 
  // Shows if the circuit is open to public.
  // For interactive apps, this set as true means users without authorization cookie set will also be able to access application.
  // For inference apps it means that API will work without authorization token passed.
  // 
  open_to_public?: boolean
  // Comma separated list of CIDRs accepted as traffic source. null means the circuit is accessible anywhere.
  allowed_client_ips?: Partial(string) & Partial(null)
  // Occupied worker port. Only set if `frontend_mode` is `port`.
  port?: Partial(integer) & Partial(null)
  // Occupied worker subdomain. Only set if `frontend_mode` is `subdomain`.
  subdomain?: Partial(string) & Partial(null)
  // Session owner's UUID.
  user_id?: Partial(string) & Partial(null)
  // Model service's UUID. Only set if `app_mode` is inference.
  endpoint_id?: Partial(string) & Partial(null)
  route_info: {
    session_id: string
    session_name?: Partial(string) & Partial(null)
    kernel_host: string
    kernel_port: integer
    protocol: enum[http, grpc, h2, tcp]
    traffic_ratio?: number //default: 1
  }[]
  session_ids?: string[]
  created_at: string
  updated_at: string
  // Number of requests processed by this circuit.
  requests: integer
  // Last access timestamp.
  last_access: Partial(integer) & Partial(null)
  // Number of seconds remaining before this circuit will be discharged due to inactivity. Can be null if `app_mode` is `interactive`.
  ttl: Partial(integer) & Partial(null)
}
```

***

### [POST]/v2/conf

- Description  
  
Generates and returns a token which will be used as an authentication credential for  
 /v2/proxy/{token}/{session}/add request.  


#### RequestBody

- application/json

```ts
{
  login_session_token: Partial(string) & Partial(null)
  kernel_host: string
  kernel_port: integer
  session: {
    id?: Partial(string) & Partial(null)
    user_uuid: string
    group_id: string
    access_key?: Partial(string) & Partial(null)
    domain_name: string
  }
}
```

#### Responses

- 200 

`application/json`

```ts
{
  token: string
}
```

***

### [POST]/v2/endpoints/{endpoint_id}

- Description  
  
Creates or updates an inference circuit.  
  
  
**Preconditions:**  
* Requires Manager token present at `X-BackendAI-Token` request header to work.  


#### RequestBody

- application/json

```ts
{
  // Name of the model service.
  service_name: string
  // Metadata of target model service and dependent sessions.
  tags: #/components/schemas/EndpointTagConfig
  // 
  // key-value pair of available applications exposed by requested endpoint.
  // Key should be name of the app, and value as list of host-port pairs app is bound to.
  // 
  apps: {
  }
  // 
  // If set to true, AppProxy will require an API token (which can be obtained from `generate_endpoint_api_token` request)
  // fullfilled at request header.
  // 
  open_to_public?: boolean
  // Preferred port number.
  port?: Partial(integer) & Partial(null)
  // Preferred subdomain name.
  subdomain?: Partial(string) & Partial(null)
}
```

#### Responses

- 200 

`application/json`

```ts
{
  endpoint: string
}
```

***

### [DELETE]/v2/endpoints/{endpoint_id}

- Description  
  
Deassociates inference circuit from system.  
  
  
**Preconditions:**  
* Requires Manager token present at `X-BackendAI-Token` request header to work.  


#### Responses

- 200 

`application/json`

```ts
{
  success?: boolean //default: true
}
```

***

### [POST]/v2/endpoints/{endpoint_id}/token

- Description  
  
Creates and returns API token required for execution of model service apps hosted by AppProxy.  
 This API is meant to be called from Backend.AI manager rather than model service callee itself.  
  
  
**Preconditions:**  
* Requires Manager token present at `X-BackendAI-Token` request header to work.  


#### RequestBody

- application/json

```ts
{
  user_uuid: string
  exp: string
}
```

#### Responses

- 200 

`application/json`

```ts
{
  token: string
}
```

***

### [GET]/health

#### Responses

***

### [GET]/health/status

- Description  
  
Returns health status of coordinator.  
  
  
**Preconditions:**  
* Requires Manager token present at `X-BackendAI-Token` request header to work.  


#### Responses

- 200 

`application/json`

```ts
{
  coordinator_version: string
  workers: {
    authority: string
    available_slots: integer
    occupied_slots: integer
    ha_setup: boolean
  }[]
}
```

***

### [GET]/v2/proxy/{token}/{session_id}/add

- Description  
  
Deprecated: only for legacy applications. Just call `proxy` API directly.  
Returns URL to AppProxy's `proxy` API handler.  


#### RequestBody

- application/json

```ts
{
  app: string
  protocol: enum[http, grpc, h2, tcp]
  envs: {
  }
  args?: Partial(string) & Partial(null)
  open_to_public?: boolean
  allowed_client_ips?: Partial(string) & Partial(null)
  redirect?: string
  no_reuse?: boolean
  port?: Partial(integer) & Partial(null)
  subdomain?: Partial(string) & Partial(null)
}
```

#### Responses

- 200 

`application/json`

```ts
{
  code: integer
  url: string
}
```

***

### [GET]/v2/proxy/auth

- Description  
  
Assigns worker to host proxy app and starts proxy process.  
When `Accept` HTTP header is set to `application/json` access information to worker will be handed out inside response body;  
otherwise coordinator will try to automatically redirect callee via `Location: ` response header.  


#### RequestBody

- application/json

```ts
{
  app: string
  protocol: enum[http, grpc, h2, tcp]
  envs: {
  }
  args?: Partial(string) & Partial(null)
  open_to_public?: boolean
  allowed_client_ips?: Partial(string) & Partial(null)
  redirect?: string
  no_reuse?: boolean
  port?: Partial(integer) & Partial(null)
  subdomain?: Partial(string) & Partial(null)
  token: string
  session_id: string
}
```

#### Responses

- 200 

`application/json`

```ts
{
  redirect_url: string
  reuse: boolean
}
```

- 302 undefined

***

### [GET]/api/slots

- Description  
  
Provides slot information hosted by worker mentioned.  
  
  
**Preconditions:**  
* Requires Worker token present at `X-BackendAI-Token` request header to work.  


#### RequestBody

- application/json

```ts
{
  // Authority string (not UUID) of AppProxy worker. If not set, API will return slots of every workers.
  wsproxy_host?: Partial(string) & Partial(null)
  // If set true, only returns information of occupied slots.
  in_use?: boolean //default: true
}
```

#### Responses

- 200 

`application/json`

```ts
{
  slots: {
    frontend_mode: enum[wildcard, port]
    in_use: boolean
    port?: Partial(integer) & Partial(null)
    subdomain?: Partial(string) & Partial(null)
    circuit_id?: Partial(string) & Partial(null)
  }[]
}
```

***

### [GET]/api/worker

- Description  
  
Lists all workers recognized by coordinator.  
  
  
**Preconditions:**  
* Requires Worker token present at `X-BackendAI-Token` request header to work.  


#### Responses

- 200 

`application/json`

```ts
{
  workers: {
    // authority string of worker. Unique across every workers joined on a single coordinator.
    authority: string
    frontend_mode: enum[wildcard, port]
    protocol: enum[http, grpc, h2, tcp]
    hostname: string
    use_tls: boolean
    api_port: integer
    port_range?: Partial([]) & Partial(null)
    wildcard_domain?: Partial(string) & Partial(null)
    filtered_apps_only: boolean
    accepted_traffics?: enum[interactive, inference][]
    // ID of worker.
    id: string
    created_at: string
    updated_at: string
    // 
    // Number of slots worker is capable to hold. Workers serving `subdomain` frontend have -1 as `available_circuits`.
    // For `port` frontend this value is number of ports exposed by the worker.
    // 
    available_slots: integer
    // Number of slots occupied by circuit.
    occupied_slots: integer
    // Number of actual nodes claiming as same worker. Can be considered as HA set up if this value is greater than 1.
    nodes: integer
    slots: {
      frontend_mode:#/components/schemas/FrontendMode
      in_use: boolean
      port?: Partial(integer) & Partial(null)
      subdomain?: Partial(string) & Partial(null)
      circuit_id?: Partial(string) & Partial(null)
    }[]
  }[]
}
```

***

### [PUT]/api/worker

- Description  
  
Registers worker to coordinator.  
  
  
**Preconditions:**  
* Requires Worker token present at `X-BackendAI-Token` request header to work.  


#### RequestBody

- application/json

```ts
{
  // authority string of worker. Unique across every workers joined on a single coordinator.
  authority: string
  frontend_mode: enum[wildcard, port]
  protocol: enum[http, grpc, h2, tcp]
  hostname: string
  use_tls: boolean
  api_port: integer
  port_range?: Partial([]) & Partial(null)
  wildcard_domain?: Partial(string) & Partial(null)
  filtered_apps_only: boolean
  accepted_traffics?: enum[interactive, inference][]
  app_filters: {
    key: string
    value: string
  }[]
}
```

#### Responses

- 200 

`application/json`

```ts
{
  // authority string of worker. Unique across every workers joined on a single coordinator.
  authority: string
  frontend_mode: enum[wildcard, port]
  protocol: enum[http, grpc, h2, tcp]
  hostname: string
  use_tls: boolean
  api_port: integer
  port_range?: Partial([]) & Partial(null)
  wildcard_domain?: Partial(string) & Partial(null)
  filtered_apps_only: boolean
  accepted_traffics?: enum[interactive, inference][]
  // ID of worker.
  id: string
  created_at: string
  updated_at: string
  // 
  // Number of slots worker is capable to hold. Workers serving `subdomain` frontend have -1 as `available_circuits`.
  // For `port` frontend this value is number of ports exposed by the worker.
  // 
  available_slots: integer
  // Number of slots occupied by circuit.
  occupied_slots: integer
  // Number of actual nodes claiming as same worker. Can be considered as HA set up if this value is greater than 1.
  nodes: integer
  slots: {
    frontend_mode:#/components/schemas/FrontendMode
    in_use: boolean
    port?: Partial(integer) & Partial(null)
    subdomain?: Partial(string) & Partial(null)
    circuit_id?: Partial(string) & Partial(null)
  }[]
}
```

***

### [GET]/api/worker/{worker_id}

- Description  
  
Returns information about worker mentioned.  
  
  
**Preconditions:**  
* Requires Worker token present at `X-BackendAI-Token` request header to work.  


#### Responses

- 200 

`application/json`

```ts
{
  // authority string of worker. Unique across every workers joined on a single coordinator.
  authority: string
  frontend_mode: enum[wildcard, port]
  protocol: enum[http, grpc, h2, tcp]
  hostname: string
  use_tls: boolean
  api_port: integer
  port_range?: Partial([]) & Partial(null)
  wildcard_domain?: Partial(string) & Partial(null)
  filtered_apps_only: boolean
  accepted_traffics?: enum[interactive, inference][]
  // ID of worker.
  id: string
  created_at: string
  updated_at: string
  // 
  // Number of slots worker is capable to hold. Workers serving `subdomain` frontend have -1 as `available_circuits`.
  // For `port` frontend this value is number of ports exposed by the worker.
  // 
  available_slots: integer
  // Number of slots occupied by circuit.
  occupied_slots: integer
  // Number of actual nodes claiming as same worker. Can be considered as HA set up if this value is greater than 1.
  nodes: integer
  slots: {
    frontend_mode:#/components/schemas/FrontendMode
    in_use: boolean
    port?: Partial(integer) & Partial(null)
    subdomain?: Partial(string) & Partial(null)
    circuit_id?: Partial(string) & Partial(null)
  }[]
}
```

***

### [PATCH]/api/worker/{worker_id}

- Description  
  
**Preconditions:**  
* Requires Worker token present at `X-BackendAI-Token` request header to work.  


#### Responses

- 200 

`application/json`

```ts
{
  // authority string of worker. Unique across every workers joined on a single coordinator.
  authority: string
  frontend_mode: enum[wildcard, port]
  protocol: enum[http, grpc, h2, tcp]
  hostname: string
  use_tls: boolean
  api_port: integer
  port_range?: Partial([]) & Partial(null)
  wildcard_domain?: Partial(string) & Partial(null)
  filtered_apps_only: boolean
  accepted_traffics?: enum[interactive, inference][]
  // ID of worker.
  id: string
  created_at: string
  updated_at: string
  // 
  // Number of slots worker is capable to hold. Workers serving `subdomain` frontend have -1 as `available_circuits`.
  // For `port` frontend this value is number of ports exposed by the worker.
  // 
  available_slots: integer
  // Number of slots occupied by circuit.
  occupied_slots: integer
  // Number of actual nodes claiming as same worker. Can be considered as HA set up if this value is greater than 1.
  nodes: integer
  slots: {
    frontend_mode:#/components/schemas/FrontendMode
    in_use: boolean
    port?: Partial(integer) & Partial(null)
    subdomain?: Partial(string) & Partial(null)
    circuit_id?: Partial(string) & Partial(null)
  }[]
}
```

***

### [DELETE]/api/worker/{worker_id}

- Description  
  
Deassociates worker from coordinator.  
  
  
**Preconditions:**  
* Requires Worker token present at `X-BackendAI-Token` request header to work.  


#### Responses

- 200 

`application/json`

```ts
{
  success?: boolean //default: true
}
```

***

### [GET]/api/worker/{worker_id}/circuits

- Description  
  
Lists every circuits worker is currently serving.  
  
  
**Preconditions:**  
* Requires Worker token present at `X-BackendAI-Token` request header to work.  


#### Responses

- 200 

`application/json`

```ts
{
  // Serializable representation of `ai.backend.appproxy.coordinator.models.Circuit`
  circuits: {
    // ID of circuit.
    id?: string
    // Name of the Backend.AI Kernel app circuit is hosting. Can be a blank string if circuit is referencing an inference app.
    app?: string
    // Protocol of the Backend.AI Kernel app.
    protocol?: #/components/schemas/ProxyProtocol
    // ID of the worker hosting the circuit.
    worker?: string
    // Application operation mode.
    app_mode?: #/components/schemas/AppMode
    // Frontend type of worker.
    frontend_mode?: #/components/schemas/FrontendMode
    envs: {
    }
    arguments: Partial(string) & Partial(null)
    // 
    // Shows if the circuit is open to public.
    // For interactive apps, this set as true means users without authorization cookie set will also be able to access application.
    // For inference apps it means that API will work without authorization token passed.
    // 
    open_to_public?: boolean
    // Comma separated list of CIDRs accepted as traffic source. null means the circuit is accessible anywhere.
    allowed_client_ips?: Partial(string) & Partial(null)
    // Occupied worker port. Only set if `frontend_mode` is `port`.
    port?: Partial(integer) & Partial(null)
    // Occupied worker subdomain. Only set if `frontend_mode` is `subdomain`.
    subdomain?: Partial(string) & Partial(null)
    // Session owner's UUID.
    user_id?: Partial(string) & Partial(null)
    // Model service's UUID. Only set if `app_mode` is inference.
    endpoint_id?: Partial(string) & Partial(null)
    route_info: {
      session_id: string
      session_name?: Partial(string) & Partial(null)
      kernel_host: string
      kernel_port: integer
      protocol: enum[http, grpc, h2, tcp]
      traffic_ratio?: number //default: 1
    }[]
    session_ids?: string[]
    created_at: string
    updated_at: string
  }[]
}
```

## References

### #/components/securitySchemes/X-BackendAI-Token

```ts
{
  "type": "http",
  "scheme": "bearer",
  "bearerFormat": "JWT"
}
```

### #/components/schemas/BulkRemoveCircuitsRequestModel

```ts
{
  circuit_ids?: string[]
}
```

### #/components/schemas/StubResponseModel

```ts
{
  success?: boolean //default: true
}
```

### #/components/schemas/AppMode

```ts
{
  "enum": [
    "interactive",
    "inference"
  ],
  "title": "AppMode",
  "type": "string"
}
```

### #/components/schemas/FrontendMode

```ts
{
  "enum": [
    "wildcard",
    "port"
  ],
  "title": "FrontendMode",
  "type": "string"
}
```

### #/components/schemas/ProxyProtocol

```ts
{
  "enum": [
    "http",
    "grpc",
    "h2",
    "tcp"
  ],
  "title": "ProxyProtocol",
  "type": "string"
}
```

### #/components/schemas/RouteInfo

```ts
{
  session_id: string
  session_name?: Partial(string) & Partial(null)
  kernel_host: string
  kernel_port: integer
  protocol: enum[http, grpc, h2, tcp]
  traffic_ratio?: number //default: 1
}
```

### #/components/schemas/SerializableCircuit

```ts
// Serializable representation of `ai.backend.appproxy.coordinator.models.Circuit`
{
  // ID of circuit.
  id?: string
  // Name of the Backend.AI Kernel app circuit is hosting. Can be a blank string if circuit is referencing an inference app.
  app?: string
  // Protocol of the Backend.AI Kernel app.
  protocol?: #/components/schemas/ProxyProtocol
  // ID of the worker hosting the circuit.
  worker?: string
  // Application operation mode.
  app_mode?: #/components/schemas/AppMode
  // Frontend type of worker.
  frontend_mode?: #/components/schemas/FrontendMode
  envs: {
  }
  arguments: Partial(string) & Partial(null)
  // 
  // Shows if the circuit is open to public.
  // For interactive apps, this set as true means users without authorization cookie set will also be able to access application.
  // For inference apps it means that API will work without authorization token passed.
  // 
  open_to_public?: boolean
  // Comma separated list of CIDRs accepted as traffic source. null means the circuit is accessible anywhere.
  allowed_client_ips?: Partial(string) & Partial(null)
  // Occupied worker port. Only set if `frontend_mode` is `port`.
  port?: Partial(integer) & Partial(null)
  // Occupied worker subdomain. Only set if `frontend_mode` is `subdomain`.
  subdomain?: Partial(string) & Partial(null)
  // Session owner's UUID.
  user_id?: Partial(string) & Partial(null)
  // Model service's UUID. Only set if `app_mode` is inference.
  endpoint_id?: Partial(string) & Partial(null)
  route_info: {
    session_id: string
    session_name?: Partial(string) & Partial(null)
    kernel_host: string
    kernel_port: integer
    protocol: enum[http, grpc, h2, tcp]
    traffic_ratio?: number //default: 1
  }[]
  session_ids?: string[]
  created_at: string
  updated_at: string
}
```

### #/components/schemas/CircuitStatisticsModel

```ts
{
  // ID of circuit.
  id?: string
  // Name of the Backend.AI Kernel app circuit is hosting. Can be a blank string if circuit is referencing an inference app.
  app?: string
  // Protocol of the Backend.AI Kernel app.
  protocol?: #/components/schemas/ProxyProtocol
  // ID of the worker hosting the circuit.
  worker?: string
  // Application operation mode.
  app_mode?: #/components/schemas/AppMode
  // Frontend type of worker.
  frontend_mode?: #/components/schemas/FrontendMode
  envs: {
  }
  arguments: Partial(string) & Partial(null)
  // 
  // Shows if the circuit is open to public.
  // For interactive apps, this set as true means users without authorization cookie set will also be able to access application.
  // For inference apps it means that API will work without authorization token passed.
  // 
  open_to_public?: boolean
  // Comma separated list of CIDRs accepted as traffic source. null means the circuit is accessible anywhere.
  allowed_client_ips?: Partial(string) & Partial(null)
  // Occupied worker port. Only set if `frontend_mode` is `port`.
  port?: Partial(integer) & Partial(null)
  // Occupied worker subdomain. Only set if `frontend_mode` is `subdomain`.
  subdomain?: Partial(string) & Partial(null)
  // Session owner's UUID.
  user_id?: Partial(string) & Partial(null)
  // Model service's UUID. Only set if `app_mode` is inference.
  endpoint_id?: Partial(string) & Partial(null)
  route_info: {
    session_id: string
    session_name?: Partial(string) & Partial(null)
    kernel_host: string
    kernel_port: integer
    protocol: enum[http, grpc, h2, tcp]
    traffic_ratio?: number //default: 1
  }[]
  session_ids?: string[]
  created_at: string
  updated_at: string
  // Number of requests processed by this circuit.
  requests: integer
  // Last access timestamp.
  last_access: Partial(integer) & Partial(null)
  // Number of seconds remaining before this circuit will be discharged due to inactivity. Can be null if `app_mode` is `interactive`.
  ttl: Partial(integer) & Partial(null)
}
```

### #/components/schemas/SessionConfig

```ts
{
  id?: Partial(string) & Partial(null)
  user_uuid: string
  group_id: string
  access_key?: Partial(string) & Partial(null)
  domain_name: string
}
```

### #/components/schemas/ConfRequestModel

```ts
{
  login_session_token: Partial(string) & Partial(null)
  kernel_host: string
  kernel_port: integer
  session: {
    id?: Partial(string) & Partial(null)
    user_uuid: string
    group_id: string
    access_key?: Partial(string) & Partial(null)
    domain_name: string
  }
}
```

### #/components/schemas/TokenResponseModel

```ts
{
  token: string
}
```

### #/components/schemas/EndpointConfig

```ts
{
  id: string
  existing_url: Partial(string) & Partial(null)
}
```

### #/components/schemas/EndpointTagConfig

```ts
{
  session: {
    id?: Partial(string) & Partial(null)
    user_uuid: string
    group_id: string
    access_key?: Partial(string) & Partial(null)
    domain_name: string
  }
  endpoint: {
    id: string
    existing_url: Partial(string) & Partial(null)
  }
}
```

### #/components/schemas/InferenceAppConfig

```ts
{
  session_id: string
  kernel_host: string
  kernel_port: integer
  protocol?: #/components/schemas/ProxyProtocol
  traffic_ratio?: number //default: 1
}
```

### #/components/schemas/EndpointCreationRequestModel

```ts
{
  // Name of the model service.
  service_name: string
  // Metadata of target model service and dependent sessions.
  tags: #/components/schemas/EndpointTagConfig
  // 
  // key-value pair of available applications exposed by requested endpoint.
  // Key should be name of the app, and value as list of host-port pairs app is bound to.
  // 
  apps: {
  }
  // 
  // If set to true, AppProxy will require an API token (which can be obtained from `generate_endpoint_api_token` request)
  // fullfilled at request header.
  // 
  open_to_public?: boolean
  // Preferred port number.
  port?: Partial(integer) & Partial(null)
  // Preferred subdomain name.
  subdomain?: Partial(string) & Partial(null)
}
```

### #/components/schemas/EndpointCreationResponseModel

```ts
{
  endpoint: string
}
```

### #/components/schemas/EndpointAPITokenGenerationRequestModel

```ts
{
  user_uuid: string
  exp: string
}
```

### #/components/schemas/EndpointAPITokenResponseModel

```ts
{
  token: string
}
```

### #/components/schemas/WorkerInfoModel

```ts
{
  authority: string
  available_slots: integer
  occupied_slots: integer
  ha_setup: boolean
}
```

### #/components/schemas/StatusResponseModel

```ts
{
  coordinator_version: string
  workers: {
    authority: string
    available_slots: integer
    occupied_slots: integer
    ha_setup: boolean
  }[]
}
```

### #/components/schemas/AddRequestModel

```ts
{
  app: string
  protocol: enum[http, grpc, h2, tcp]
  envs: {
  }
  args?: Partial(string) & Partial(null)
  open_to_public?: boolean
  allowed_client_ips?: Partial(string) & Partial(null)
  redirect?: string
  no_reuse?: boolean
  port?: Partial(integer) & Partial(null)
  subdomain?: Partial(string) & Partial(null)
}
```

### #/components/schemas/AddResponseModel

```ts
{
  code: integer
  url: string
}
```

### #/components/schemas/ProxyRequestModel

```ts
{
  app: string
  protocol: enum[http, grpc, h2, tcp]
  envs: {
  }
  args?: Partial(string) & Partial(null)
  open_to_public?: boolean
  allowed_client_ips?: Partial(string) & Partial(null)
  redirect?: string
  no_reuse?: boolean
  port?: Partial(integer) & Partial(null)
  subdomain?: Partial(string) & Partial(null)
  token: string
  session_id: string
}
```

### #/components/schemas/ProxyResponseModel

```ts
{
  redirect_url: string
  reuse: boolean
}
```

### #/components/schemas/ListSlotsRequestModel

```ts
{
  // Authority string (not UUID) of AppProxy worker. If not set, API will return slots of every workers.
  wsproxy_host?: Partial(string) & Partial(null)
  // If set true, only returns information of occupied slots.
  in_use?: boolean //default: true
}
```

### #/components/schemas/SlotModel

```ts
{
  frontend_mode: enum[wildcard, port]
  in_use: boolean
  port?: Partial(integer) & Partial(null)
  subdomain?: Partial(string) & Partial(null)
  circuit_id?: Partial(string) & Partial(null)
}
```

### #/components/schemas/ListSlotsResponseModel

```ts
{
  slots: {
    frontend_mode: enum[wildcard, port]
    in_use: boolean
    port?: Partial(integer) & Partial(null)
    subdomain?: Partial(string) & Partial(null)
    circuit_id?: Partial(string) & Partial(null)
  }[]
}
```

### #/components/schemas/WorkerResponseModel

```ts
{
  // authority string of worker. Unique across every workers joined on a single coordinator.
  authority: string
  frontend_mode: enum[wildcard, port]
  protocol: enum[http, grpc, h2, tcp]
  hostname: string
  use_tls: boolean
  api_port: integer
  port_range?: Partial([]) & Partial(null)
  wildcard_domain?: Partial(string) & Partial(null)
  filtered_apps_only: boolean
  accepted_traffics?: enum[interactive, inference][]
  // ID of worker.
  id: string
  created_at: string
  updated_at: string
  // 
  // Number of slots worker is capable to hold. Workers serving `subdomain` frontend have -1 as `available_circuits`.
  // For `port` frontend this value is number of ports exposed by the worker.
  // 
  available_slots: integer
  // Number of slots occupied by circuit.
  occupied_slots: integer
  // Number of actual nodes claiming as same worker. Can be considered as HA set up if this value is greater than 1.
  nodes: integer
  slots: {
    frontend_mode:#/components/schemas/FrontendMode
    in_use: boolean
    port?: Partial(integer) & Partial(null)
    subdomain?: Partial(string) & Partial(null)
    circuit_id?: Partial(string) & Partial(null)
  }[]
}
```

### #/components/schemas/WorkerListResponseModel

```ts
{
  workers: {
    // authority string of worker. Unique across every workers joined on a single coordinator.
    authority: string
    frontend_mode: enum[wildcard, port]
    protocol: enum[http, grpc, h2, tcp]
    hostname: string
    use_tls: boolean
    api_port: integer
    port_range?: Partial([]) & Partial(null)
    wildcard_domain?: Partial(string) & Partial(null)
    filtered_apps_only: boolean
    accepted_traffics?: enum[interactive, inference][]
    // ID of worker.
    id: string
    created_at: string
    updated_at: string
    // 
    // Number of slots worker is capable to hold. Workers serving `subdomain` frontend have -1 as `available_circuits`.
    // For `port` frontend this value is number of ports exposed by the worker.
    // 
    available_slots: integer
    // Number of slots occupied by circuit.
    occupied_slots: integer
    // Number of actual nodes claiming as same worker. Can be considered as HA set up if this value is greater than 1.
    nodes: integer
    slots: {
      frontend_mode:#/components/schemas/FrontendMode
      in_use: boolean
      port?: Partial(integer) & Partial(null)
      subdomain?: Partial(string) & Partial(null)
      circuit_id?: Partial(string) & Partial(null)
    }[]
  }[]
}
```

### #/components/schemas/AppFilter

```ts
{
  key: string
  value: string
}
```

### #/components/schemas/WorkerRequestModel

```ts
{
  // authority string of worker. Unique across every workers joined on a single coordinator.
  authority: string
  frontend_mode: enum[wildcard, port]
  protocol: enum[http, grpc, h2, tcp]
  hostname: string
  use_tls: boolean
  api_port: integer
  port_range?: Partial([]) & Partial(null)
  wildcard_domain?: Partial(string) & Partial(null)
  filtered_apps_only: boolean
  accepted_traffics?: enum[interactive, inference][]
  app_filters: {
    key: string
    value: string
  }[]
}
```

### #/components/schemas/CircuitListResponseModel

```ts
{
  // Serializable representation of `ai.backend.appproxy.coordinator.models.Circuit`
  circuits: {
    // ID of circuit.
    id?: string
    // Name of the Backend.AI Kernel app circuit is hosting. Can be a blank string if circuit is referencing an inference app.
    app?: string
    // Protocol of the Backend.AI Kernel app.
    protocol?: #/components/schemas/ProxyProtocol
    // ID of the worker hosting the circuit.
    worker?: string
    // Application operation mode.
    app_mode?: #/components/schemas/AppMode
    // Frontend type of worker.
    frontend_mode?: #/components/schemas/FrontendMode
    envs: {
    }
    arguments: Partial(string) & Partial(null)
    // 
    // Shows if the circuit is open to public.
    // For interactive apps, this set as true means users without authorization cookie set will also be able to access application.
    // For inference apps it means that API will work without authorization token passed.
    // 
    open_to_public?: boolean
    // Comma separated list of CIDRs accepted as traffic source. null means the circuit is accessible anywhere.
    allowed_client_ips?: Partial(string) & Partial(null)
    // Occupied worker port. Only set if `frontend_mode` is `port`.
    port?: Partial(integer) & Partial(null)
    // Occupied worker subdomain. Only set if `frontend_mode` is `subdomain`.
    subdomain?: Partial(string) & Partial(null)
    // Session owner's UUID.
    user_id?: Partial(string) & Partial(null)
    // Model service's UUID. Only set if `app_mode` is inference.
    endpoint_id?: Partial(string) & Partial(null)
    route_info: {
      session_id: string
      session_name?: Partial(string) & Partial(null)
      kernel_host: string
      kernel_port: integer
      protocol: enum[http, grpc, h2, tcp]
      traffic_ratio?: number //default: 1
    }[]
    session_ids?: string[]
    created_at: string
    updated_at: string
  }[]
}
```
