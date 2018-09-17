## Version Numbering

* Version numbering uses `x.y.z` format (where `x`, `y`, `z` are integers).
* Mostly, we follow [the semantic versioning scheme](https://semver.org/).
* `x.y` is a release branch name.
* `x.y.z` is a release tag name.
* When releasing `x.y.0`:
  - Create a new `x.y` branch, do all bugfix/hotfix there, and make `x.y.z` releases there.
  - All fixes in the `x.y` branch must be merged back to `master` and `develop`.
    - Use `git merge --no-ff --no-commit master` to inspect the changes before commits.
    - When merging back, you would encounter merge conflicts on the version number (e.g., `ai/backend/manager/__init__.py`) if you are doing it after releasing `x.y.z` patch builds: then resolve it by *preserving the version number of the `master` branch.* ([example here](https://github.com/lablup/backend.ai-manager/commit/8a498ad4a24e4e074d683a3e2fc177647eb17a9a))
    - It is recommeded to use "merge" but you may use "cherry-pick" as well, to keep the history clean if `master` has deviated too much.
  - Change the version number of `master` to `x.(y+1).0a1`
  - There is no strict rules about alpha/beta/rc builds yet. We will elaborate as we scale up.  
    Once used, alpha versions will have `aN` suffixes, beta versions `bN` suffixes, and RC versions `rcN` suffixes where `N` is an integer.
* New development should go on `master` and `develop` branches.
  - `master`: commit here directly if your changes are a self-complete one as a single commit.
  - `develop`: for long-running incomplete development.
  - Use both short-lived and long-running feature branches freely, but ensure there names differ from release branches and tags.
* The major/minor (`x.y`) version of Backend.AI subprojects will go together to indicate compatibility.  Currently manager/agent/common versions progress this way, while client SDKs have their own version numbers and the API specification has a different `vN.yyyymmdd` version format.
  - `backend.ai-manager 1.2.p` is guaranteed to be compatible with `backend.ai-agent 1.2.q` (where `p` and `q` are same or different integers)
  - The client is guaranteed to be backward-compatible with the server they share the same API specification version.

## Upgrading

You can upgrade the installed Python packages using `pip install -U ...` command along with dependencies.

If you have cloned the stable version of source code from git, then pull and check out the next `x.y` release branch.
It is recommended to re-run `pip install -U -r requirements.txt` as dependencies might be updated.

For the manager, ensure that your database schema is up-to-date by running `alembic upgrade head`.
Also check if any manual etcd configuration scheme change is required, though we will try to keep it compatible and automatically upgrade when first executed.