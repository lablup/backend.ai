Restore the `agent_resources` model tests, which every one of them failed on since `agent_uuid` became a NOT NULL column: the fixtures still wrote rows without it.
