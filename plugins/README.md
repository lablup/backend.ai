# Plugin Development Flow

Run `./scripts/install-plugin.sh {github-owner}/{repo-name}`.
(Example: `./scripts/install-plugin.sh lablup/backend.ai-accelerator-cuda-mock`)

The script clones the plugin code into `./plugins/{repo-name}` and installs it as an editable
package inside the Pants-exported unified virtualenv.

After every `pants export`, run `./scripts/reinstall-plugins.sh` again to redo the editable
installation.
