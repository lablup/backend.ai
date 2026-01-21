Plugin Development Flow
-----------------------

Run `./scripts/install-plugin.sh {github-owner}/{repo-name}`.
(Example: `./scripts/install-plugin.sh lablup/backend.ai-accelerator-cuda-mock`)

The plugin code will be cloned into `./plugins/{repo-name}` and it will be installed
as an editable package inside the Pants exported unified virtualenv.

Note that whenever you run `pants export` again, you need to run
`./scripts/reinstall-plugins.sh` again to redo editable installation.
