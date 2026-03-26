"""Transport-agnostic adapters bridging Pydantic DTOs and Processors.

Each domain adapter accepts Pydantic DTO inputs, calls the appropriate
Processor action, and returns Pydantic DTO responses.  Both REST handlers
and GQL resolvers use the same adapter, ensuring a single service call path.
"""
