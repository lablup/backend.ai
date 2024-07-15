Backend.AI Installer
====================

Package Structure
-----------------

* `ai.backend.install`: The installer package

Development
-----------

### Using the textual debug mode

First, install the textual-dev package in the `python-default` venv.
```shell
./py -m pip install textual-dev
```

Open two terminal sessions.
In the first one, run:
```shell
dist/export/python/virtualenvs/python-default/3.12.4/bin/textual console
```

> **Warning**
> You should use the `textual` executable created *inside the venv's `bin` directory*.
> `./py -m textual` only shows the demo instead of executing the devtool command.

In the second one, run:
```shell
TEXTUAL=devtools,debug ./backend.ai install
```
