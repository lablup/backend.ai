# Local Wheel Repository

This directory is to test against locally built wheels for 3rd party packages under development within our pantsbuild-based build toolchain.

1. Build a 3rd-party local wheel.
2. Copy the wheel file here.
3. Update the root's `requirements.txt` to use the exact version of the copied wheel.
4. Run `pants generate-lockfiles --resolve=python-default && pants export --resolve=python-default`.
5. Run any pants commands, like `pants check` and `pants test`.
   You may also run `./backend.ai ...` as well.

> [!CAUTION]
> You **SHOULD NOT** add the locally modified `requirements.txt` and `python-default.lock` file in your commits and PRs.
> Use this directory *only for local testing*.

> [!TIP]
> To pin the official release dependency to a custom-built 3rd-party wheel, use our "oven" repository
> to publicly store and serve them.  See https://github.com/lablup/backend.ai-oven for more details.
