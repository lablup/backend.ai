# backend.ai-cli

Unified command-line interface for Backend.AI


## How to adopt in CLI-enabled Backend.AI packages

An example `setup.cfg` in Backend.AI Manager:
```
[options.entry_points]
backendai_cli_v10 =
    mgr = ai.backend.manager.cli.__main__:main
    mgr.start-server = ai.backend.gateway.server:main
```

Define your package entry points that returns a Click command group using a
prefix, and add additional entry points that returns a Click command using a
prefix followed by a dot and sub-command name for shortcut access, under the
`backendai_cli_v10` entry point group.

Then add `backend.ai-cli` to the `install_requires` list.

You can do the same in `setup.py` as well.
