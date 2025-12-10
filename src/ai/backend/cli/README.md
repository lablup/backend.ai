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


## Shell Tab Completion

The CLI provides built-in shell tab completion support for bash, zsh, and fish shells.

### Quick Setup

```bash
# Show completion setup instructions
backend.ai completion --show

# Install completion automatically
backend.ai completion --shell bash  # Install to ~/.bashrc
backend.ai completion --shell zsh   # Install to ~/.zshrc
backend.ai completion --shell fish  # Install to fish completions
```

### Manual Setup

If you prefer manual setup, you can add completion to your shell configuration:

**Bash** (`~/.bashrc`):
```bash
eval "$(_BACKEND_AI_COMPLETE=bash_source backend.ai)"
```

**Zsh** (`~/.zshrc`):
```bash
eval "$(_BACKEND_AI_COMPLETE=zsh_source backend.ai)"
```

**Fish** (`~/.config/fish/config.fish`):
```fish
backend.ai completion --shell fish | source
```

### Features

Tab completion supports:
- **Commands**: All available commands and subcommands
- **Options**: Short and long flags with descriptions
- **Arguments**: Context-aware argument completion where applicable
- **Help**: Descriptions for commands and options

### Examples

```bash
backend.ai <TAB>              # Show all available commands
backend.ai session <TAB>      # Show session subcommands
backend.ai session create <TAB>  # Show creation options
backend.ai --<TAB>            # Show global options
```
