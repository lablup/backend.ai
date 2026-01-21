Backend.AI Logging Subsystem
============================

Package Structure
-----------------

* `ai.backend.logging`
  - `abc`: Abstract base classes
  - `logger`: The core logging facility
    - `Logger`: The standard multiprocess-friendly logger using `RelayHandler` based on ZeroMQ
    - `LocalLogger`: A minimalized console/file logger that does not require serialization via networks at all
  - `handler`: Collection of vendor-specific handler implementations
  - `formatter`: Collection of formatters
  - `types`: Definition of enums/types like `LogLevel`
  - `utils`: Brace-style message formatting adapters and other extras
