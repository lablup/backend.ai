# Local Wheel Repository

This directory tests against locally built wheels for third-party packages under development in the Pants-based build toolchain.

1. Build a third-party local wheel.
2. Copy the wheel file here.
3. Update the root's `requirements.txt` to use the exact version of the copied wheel.
4. Run `pants generate-lockfiles --resolve=python-default && pants export --resolve=python-default`.
5. Run any Pants command, such as `pants check` and `pants test`.
   You may also run `./backend.ai ...`.

> [!CAUTION]
> Do not add the locally modified `requirements.txt` and `python-default.lock` file to your commits and PRs.
> Use this directory for local testing only.

> [!TIP]
> To pin the official release dependency to a custom-built third-party wheel, use the "oven" repository
> to store and serve them publicly. See https://github.com/lablup/backend.ai-oven for details.
