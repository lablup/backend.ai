# pants-scie-plugin

> **Note**
> This plugin is written by @sureshjoshi.
> Please refer the original code [at the author's repository.](https://github.com/sureshjoshi/pants-plugins/tree/main/pants-plugins/experimental/scie)

This plugin provides a `scie_binary` target that can be used to create a single-file Python executable with an embedded Python interpreter, built via [scie-jump](https://github.com/a-scie/jump).

It uses [science](https://github.com/a-scie/lift) and a `.toml` configuration file to build the executable, expecting a `pex_binary` as a dependency.

## Installation

This plugin was developed using Python 3.9 and Pants 2.16.0.rc3, but should work with Pants 2.15+ (however, your mileage may vary).

Add the following to your `pants.toml` file:

```toml
[GLOBAL]
plugins = [
    ...
    "robotpajamas.pants.scie",
]

...

backend_packages = [
    ...
    "experimental.scie",
]
```

## Usage

At the moment, the `scie_binary` expects a `pex_binary` as its only dependency. There is no technical limitation to this, but it simplified the initial implementation.

For trivial packaging, you can set an `entry_point` on your `pex_binary` and the `scie_binary` will directly call your pex (e.g. `python myapp.pex`). This can be particularly useful for CLIs or other simple applications. The name of your binary will be the name of your `scie_binary` target, and it will be placed in the `dist` directory.

```python
# BUILD

pex_binary(
    name="mycli-pex",
    entry_point="mycli.main",
    ...
)

scie_binary(
    name="mycli",
    dependencies=[":mycli-pex"],
    ...
)
```

You can optionally cross-build your executable by setting the `platforms` field on your `scie_binary` target. This will create a binary for the specified platform, and will be named accordingly (e.g. `mycli-linux-x86_64`). You should also ensure that your `pex_binary` is built for the same platform(s).

```python
# BUILD

pex_binary(
    name="mycli-pex",
    entry_point="mycli.main",
    platforms=["linux-x86_64-cp-312-cp312", "macosx-13.3-arm64-cp-312-cp312",]
    ...
)

scie_binary(
    name="mycli",
    dependencies=[":mycli-pex"],
    platforms=["linux-x86_64", "macos-aarch64",]
    ...
)
```

## Advanced Usage

For non-trivial packaging, it is much easier (and cleaner) to use the `science` config TOML file to specify what should be in the package and how it should work. This may be in situations where you want multiple commands, or you require boot bindings. A good example of this is setting up a FastAPI application with a Uvicorn or Gunicorn runner, which requires using PEX_TOOLS and creating a `venv` from your code.

The plugin will attempt to replace variables in the TOML with equivalent ones specified in the target. For example, the binary name, the binary description, `platforms` (if specified), etc... The one critical aspect to note is that in order to reference another target (e.g. the output of `pex_binary`), use the `:target_name` syntax in the TOML. The plugin will use `science`'s `--file` mapping argument to replace the target name with the actual file path.

```python
# BUILD

pex_binary(
    name="hellofastapi-pex",
    entry_point="hellofastapi.main",
    dependencies=[":libhellofastapi"],
    include_tools=True,
)

scie_binary(
    name="hellofastapi",
    dependencies=[":hellofastapi-pex"],
    lift="lift.toml",
    ...
)
```

```toml
# lift.toml

[lift]
name = "hellofastapi"
description = "An example FastAPI Lift application including using an external uvicorn server"

[[lift.interpreters]]
id = "cpython"
provider = "PythonBuildStandalone"
release = "20240713"
version = "3.12.4"

[[lift.files]]
# Note the leading colon, which is required to reference the pex_binary dependency
name = ":hellofastapi-pex"

[[lift.commands]]
exe = "{scie.bindings.venv}/venv/bin/uvicorn"
args = ["hellofastapi.main:app", "--port", "7999"]
description = "The FastAPI executable."

[[lift.bindings]]
name = "venv"
description = "Installs HelloFastAPI into a venv and pre-compiles .pyc"
exe = "#{cpython:python}"
args = [
    "{:hellofastapi-pex}",
    "venv",
    "--bin-path",
    "prepend",
    "--compile",
    "--rm",
    "all",
    "{scie.bindings}/venv",
]

[lift.bindings.env.default]
"=PATH" = "{cpython}/python/bin:{scie.env.PATH}"
"PEX_TOOLS" = "1"
"PEX_ROOT" = "{scie.bindings}/pex_root"
```
