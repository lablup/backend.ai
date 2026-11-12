# Backend.AI Logging Subsystem

## Package Structure

* `ai.backend.logging`
  - `abc`: Abstract base classes
  - `logger`: The core logging facility
    - `Logger`: The standard multiprocess-friendly logger using `RelayHandler` based on ZeroMQ
    - `LocalLogger`: A minimal console and file logger that does not serialize messages over the network
  - `handler`: Collection of vendor-specific handler implementations
  - `formatter`: Collection of formatters
  - `types`: Definition of enums and types such as `LogLevel`
  - `utils`: Brace-style message formatting adapters and other extras
