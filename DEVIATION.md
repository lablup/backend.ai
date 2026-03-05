# Deviation Report: BA-4905

| Item | Type | Reason / Alternative |
|------|------|----------------------|
| Task 1: `LoginSecurityPolicy(BaseModel)` placed in `data/login_session/types.py` | Alternative applied | `data/` CLAUDE.md prohibits Pydantic imports. Pydantic models used with PydanticColumn follow the `models/{domain}/types.py` pattern (see `models/scaling_group/types.py`, `models/resource_slot/types.py`). `LoginSecurityPolicy` placed in `models/login_session/types.py` instead. |
