Changes
=======

<!--
    You should *NOT* be adding new change log entries to this file, this
    file is managed by towncrier. You *may* edit previous change logs to
    fix problems like typo corrections or such.

    To add a new change log entry, please refer
    https://pip.pypa.io/en/latest/development/contributing/#news-entries

    We named the news folder "changes".

    WARNING: Don't drop the last line!
-->

<!-- towncrier release notes start -->

## 23.03.1 (2023-05-04)

### Features
* Add --recursive option to cancel all the dependent sessions to session terminate API ([#893](https://github.com/lablup/backend.ai/issues/893))
* The new `mock-accelerator` plugin supsedes the `cuda-mock` plugin.  It may be set to have arbitrary accelerator resource slots.  Existing developers who use the cuda-mock plugin should update their mockup device list configuration (`cuda-mock.toml`) to follow the new format (`mock-accelerator.toml`). ([#1158](https://github.com/lablup/backend.ai/issues/1158))
* Utilization checker returns `thresholds_check_operator`. ([#1202](https://github.com/lablup/backend.ai/issues/1202))
* Fix SCP/SFTP not working ([#1225](https://github.com/lablup/backend.ai/issues/1225))
* Add support for idle checking ATOM accelerators ([#1234](https://github.com/lablup/backend.ai/issues/1234))
* Add `is_public` field to scaling_group table. ([#1236](https://github.com/lablup/backend.ai/issues/1236))
* Add agent `public-host` config option and impl manager API to fetch direct access info of `SYSTEM` kernel. ([#1238](https://github.com/lablup/backend.ai/issues/1238))
* Make image scanner handle OCI image metadata formats ([#1241](https://github.com/lablup/backend.ai/issues/1241))
* Do not count stakes of `SYSTEM` role kernels when calculating resource occupancy ([#1243](https://github.com/lablup/backend.ai/issues/1243))
* Update `/folder/_/list-hosts` API to expose client scaling groups designated only for SSH connection apps ([#1246](https://github.com/lablup/backend.ai/issues/1246))
* Add `system_SSH_image` config to webserver so that system-role ssh image used to support fast scp and sftp in file browser dialog can be specified. ([#1250](https://github.com/lablup/backend.ai/issues/1250))
* Fix destroying session on behalf of other user by providing owner_access_key not working ([#1255](https://github.com/lablup/backend.ai/issues/1255))

### Improvements
* Improve `status_data` generation when the debug mode is enabled ([#1203](https://github.com/lablup/backend.ai/issues/1203))

### Fixes
* Calculate idle checker's remaining time to expire correctly. ([#1205](https://github.com/lablup/backend.ai/issues/1205))
* Fix relative path computation in the NetApp storage backend and disable cross-volume vfolder cloning until we have explicit export/import abstractions for the storage backends ([#1208](https://github.com/lablup/backend.ai/issues/1208))
* Optimize monthly stat API by reducing the number of iteration and fetch to Redis. ([#1214](https://github.com/lablup/backend.ai/issues/1214))
* Remove `DoSyncKernelStatsEvent` events since it is deprecated and adjust the interval of agent heart-beat event through configuration. ([#1223](https://github.com/lablup/backend.ai/issues/1223))
* Consume kernel lifecycle events and remove `manager.registry.kernel_creation_tracker`. ([#1224](https://github.com/lablup/backend.ai/issues/1224))
* Disable collecting per-container statistics on macOS backend until #1230 is resolved ([#1231](https://github.com/lablup/backend.ai/issues/1231))
* fix minor typo error in mock-accelerator config ([#1240](https://github.com/lablup/backend.ai/issues/1240))
* Fix logical errors in the fallback process for cpuset detection in agents when the docker API is not available ([#1248](https://github.com/lablup/backend.ai/issues/1248))
* Upgrade aiotools to 1.6.1 for potential memory leak fix when there are unhandled exceptions inside persistent task groups ([#1256](https://github.com/lablup/backend.ai/issues/1256))

### Miscellaneous
* Bump base Python version from 3.11.2 to 3.11.3 to resolve potential bugs. ([#1227](https://github.com/lablup/backend.ai/issues/1227))
* Replace `./pants` with the scie-pants project so that developers could use a much faster version of `pants` binary bootstrapper that auto-installs the required Python interpreter using a static build ([#1237](https://github.com/lablup/backend.ai/issues/1237))


## 23.03.0 (2023-03-30)

### Features
* Dispatch session related events to an external service when manager plugin with `PUBLISH_EVENT` implement exists ([#1094](https://github.com/lablup/backend.ai/issues/1094))
* Report idle checker their idle remaining time and utilization to `Redis` and let Gql fetch the report. ([#1160](https://github.com/lablup/backend.ai/issues/1160))
* Provide status information about usage, capacity of storage volume to `list-hosts` API ([#1170](https://github.com/lablup/backend.ai/issues/1170))
* Query agent list with multiple statuses. For example, CLI query like this is now possible: `backend.ai admin agent list -s "TERMINATED,LOST"`. ([#1174](https://github.com/lablup/backend.ai/issues/1174))
* Return `status_info` in session usage statistics API. ([#1176](https://github.com/lablup/backend.ai/issues/1176))
* Add a `allow_preferred_port` config on webserver to hide/show Try preferred port. ([#1178](https://github.com/lablup/backend.ai/issues/1178))
* Gather per-container network statistics. ([#1179](https://github.com/lablup/backend.ai/issues/1179))
* Support to change the owner of (user) vfolder to only among users with an access to the vfolder's storage host ([#1182](https://github.com/lablup/backend.ai/issues/1182))
* Add possible expire time of utilization checker to idle check result. ([#1185](https://github.com/lablup/backend.ai/issues/1185))
* Add `[storage-proxy].ipc-base-path` configuration option to the storage proxy like other service daemons ([#1189](https://github.com/lablup/backend.ai/issues/1189))
* Automatically mount `.linuxbrew` dot-folder, if exists, at `/home/linuxbrew/.linuxbrew` inside a container to support OS package installation with Homebrew. ([#1195](https://github.com/lablup/backend.ai/issues/1195))
* Add a step to idle checkers to determine the initial grace period, which is calculated by the user's creation time. ([#1199](https://github.com/lablup/backend.ai/issues/1199))
* Update libbaihook to latest version which includes fix to resolve fastertransformer crashing ([#1200](https://github.com/lablup/backend.ai/issues/1200))

### Improvements
* Automatically set the proper webui build artifact path in `webserver.conf` when installed with `--editable-webui` and document it in the sample configuration ([#1190](https://github.com/lablup/backend.ai/issues/1190))

### Fixes
* Fix session ls not working bug ([#1100](https://github.com/lablup/backend.ai/issues/1100))
* Add delete transactions vfolder_invitations and vfolder_permissions table when new owner and invitee of vfolder are same ([#1186](https://github.com/lablup/backend.ai/issues/1186))
* Make pipeline related configuration fields to be optional ([#1187](https://github.com/lablup/backend.ai/issues/1187))
* Change input field of change vfolder ownership from `user_id` to `user_email` ([#1188](https://github.com/lablup/backend.ai/issues/1188))


## 23.03.0a4 (2023-03-16)

### Features
* Replace `username` in the `compute_session` (and `compute_session_list`) GQL query with `full_name` and expose `full_name` to `get_container_stats_for_period` so that administrators can easily recognize users. ([#1167](https://github.com/lablup/backend.ai/issues/1167))
* Add new inference_metrics column to compute_session GQL query ([#1168](https://github.com/lablup/backend.ai/issues/1168))


## 23.03.0a3 (2023-03-15)
No significant changes.


## 23.03.0a3 (2023-03-15)

### Fixes
* Use SI bytesize unit where it is not mem size. ([#1098](https://github.com/lablup/backend.ai/issues/1098))


## 23.03.0a2 (2023-03-15)

### Features
* Report commit status through redis rather direct RPC call. ([#1015](https://github.com/lablup/backend.ai/issues/1015))
* Add an `enable_2FA` option to enable/disable 2-Factor-Authenticaiton feature. ([#1126](https://github.com/lablup/backend.ai/issues/1126))
* Apply the `totp_activated` field in creating/updating user for admins to set the 2FA activation status. ([#1142](https://github.com/lablup/backend.ai/issues/1142))
* Add support for OTP based 2FA login on Backend.AI CLI ([#1147](https://github.com/lablup/backend.ai/issues/1147))
* Expose `user_name` field to `compute_session` (and also `compute_session_list`) GQL query. ([#1149](https://github.com/lablup/backend.ai/issues/1149))
* Expand accelerator plugin interface to show richer information about itself and add new `/config/resource-slots/details` API to show information collected by new interface ([#1153](https://github.com/lablup/backend.ai/issues/1153))
* Increased the manager API version to `v6.20230315` ([#1154](https://github.com/lablup/backend.ai/issues/1154))
* Allow setting the maximum concurrency of container creation tasks in the agent per RPC call ([#1159](https://github.com/lablup/backend.ai/issues/1159))
* Add a `force_2FA` option to force the use of 2-Factor-Authenticaiton. ([#1161](https://github.com/lablup/backend.ai/issues/1161))

### Fixes
* ssh-add not working bug due to permission issue ([#1141](https://github.com/lablup/backend.ai/issues/1141))
* Update vfolder clone status by vfolder id rather vfolder name. ([#1145](https://github.com/lablup/backend.ai/issues/1145))

### External Dependency Updates
* Replace `netifaces` (now unmaintained) with `ifaddr` in favor of better maintained one with a pure Python implementation ([#1155](https://github.com/lablup/backend.ai/issues/1155))


## 23.03.0a1 (2023-03-02)

### Breaking Changes
* Now the mono-repo is updated to use Pants 2.16.0.dev5. Check out the PR description for the migration guide. ([#998](https://github.com/lablup/backend.ai/issues/998))
* Now the main branch (for 23.03) requires Python 3.11.2 to run ([#1012](https://github.com/lablup/backend.ai/issues/1012))

### Features
* Introduce plugin based metadata server architecture ([#448](https://github.com/lablup/backend.ai/issues/448))
* Refactor session managing process by adding session db table and migrating to sqlalchemy ORM partially. ([#576](https://github.com/lablup/backend.ai/issues/576))
* Added `BACKENDAI_SERVICE_PORTS` and `BACKENDAI_PREOPEN_PORTS` to the session env as there is no way for the user to check the port inside the container. ([#648](https://github.com/lablup/backend.ai/issues/648))
* Support IBM Spectrum Scale storage ([#744](https://github.com/lablup/backend.ai/issues/744))
* Support local vscode using remote ssh mode to session container ([#751](https://github.com/lablup/backend.ai/issues/751))
* Add support for Ceph file system in Storage Proxy. ([#760](https://github.com/lablup/backend.ai/issues/760))
* Add `architecture` argument and options to the client SDK's session creation functions and commands ([#881](https://github.com/lablup/backend.ai/issues/881))
* Create human-friendly session name randomly when it's not given. ([#885](https://github.com/lablup/backend.ai/issues/885))
* Gather process list in container and measure their resource usage. ([#916](https://github.com/lablup/backend.ai/issues/916))
* Add DELETABLE status for VFolderAccessStatus to distinguish from UPDATABLE status. ([#919](https://github.com/lablup/backend.ai/issues/919))
* When rescanning container image registries, skip misformatted image names and tag names instead of failing the entire process. ([#933](https://github.com/lablup/backend.ai/issues/933))
* Add `custom-auth` endpoint in Webserver to support custom authentication logic with Manager plugin. ([#936](https://github.com/lablup/backend.ai/issues/936))
* Support setting the `use_host_network` option of scaling group in the client-py. ([#941](https://github.com/lablup/backend.ai/issues/941))
* Remove the `Server` HTTP response header from the web server since it could potentially expose more attack surfaces to crackers ([#947](https://github.com/lablup/backend.ai/issues/947))
* Add the `session_id` and `cluster_mode` columns to `get_container_stats_for_period` API to provide container statistics in response to multi-node sessions. ([#949](https://github.com/lablup/backend.ai/issues/949))
* Add support for Ubuntu 22.04-based kernels and enhance selecting kernel runner binary's target version. ([#956](https://github.com/lablup/backend.ai/issues/956))
* Make jail as a usable container sandbox option ([#960](https://github.com/lablup/backend.ai/issues/960))
* Define a new recursive type to represent a nested dictionary. ([#981](https://github.com/lablup/backend.ai/issues/981))
* Add fish shell support to `install-dev.sh` script ([#987](https://github.com/lablup/backend.ai/issues/987))
* Refactor the data structure of background task event client from a set of queues to defaultdict of a set of queues to prevent handling unnecessary event ([#991](https://github.com/lablup/backend.ai/issues/991))
* Support cgroup v2 on get_available_cores ([#992](https://github.com/lablup/backend.ai/issues/992))
* Support using systemd cgroup driver for Docker ([#1000](https://github.com/lablup/backend.ai/issues/1000))
* Stop using pids cgroup controller ([#1005](https://github.com/lablup/backend.ai/issues/1005))
* Supports cgroup v2 for measuring container stats (cpu, mem, io) ([#1006](https://github.com/lablup/backend.ai/issues/1006))
* Apply a hook `VERIFY_PASSWORD_FORMAT` for signup API handler to enforce the password policy for new users. ([#1008](https://github.com/lablup/backend.ai/issues/1008))
* Create new `/folders/_/used-bytes` API ([#1013](https://github.com/lablup/backend.ai/issues/1013))
* Add vfolder status in api response and update vfolder cli `list`, `info` commands to show vfolder's status. ([#1017](https://github.com/lablup/backend.ai/issues/1017))
* Return API response right after starting vFolder removal instead of waiting until deletion process completes ([#1018](https://github.com/lablup/backend.ai/issues/1018))
* Upgrade the mypy version to 1.0.0 ([#1021](https://github.com/lablup/backend.ai/issues/1021))
* Update backend.ai-hook build for supporting cgroup v2 ([#1023](https://github.com/lablup/backend.ai/issues/1023))
* Make group_id optional in list_shared_vfolders and add a command to list shared vfolders from client-py. ([#1026](https://github.com/lablup/backend.ai/issues/1026))
* add POST `/ssh/keypair` API to let user use their own SSH keypair instead of randomly generated one ([#1032](https://github.com/lablup/backend.ai/issues/1032))
* Add spinner on client for long background task ([#1033](https://github.com/lablup/backend.ai/issues/1033))
* Adds `~/.ssh/id_rsa` in addition to `id_container`, so ease users not to specify the SSH private key always, for example, in cloning a GitHub private repository from terminal. ([#1038](https://github.com/lablup/backend.ai/issues/1038))
* Add ProgressViewer for the progress background tasks which support both spinner and tqdm progress bar. ([#1049](https://github.com/lablup/backend.ai/issues/1049))
* Add the phase-1 implementation of model serving, introducing a new 'inference' session type, `backend.ai {model,service}` commands, and the endpoint and routing database tables ([#1057](https://github.com/lablup/backend.ai/issues/1057))
* Make the dev-setup installer to preserve a full dump of the initial etcd configuration as `./dev.etcd.installed.json` for easier restoration of etcd if corrupted during development ([#1061](https://github.com/lablup/backend.ai/issues/1061))
* Auto-start SSH agent upon session startup ([#1067](https://github.com/lablup/backend.ai/issues/1067))
* Update `image_list` query resolver to resolve image list faster ([#1073](https://github.com/lablup/backend.ai/issues/1073))
* Add more HTTP forwarding headers in the webserver for the manager and webapp plugins: `X-Forwarded-Host` and `X-Forwarded-Proto` ([#1075](https://github.com/lablup/backend.ai/issues/1075))
* Add validation of inference session labels when rescanning images ([#1087](https://github.com/lablup/backend.ai/issues/1087))
* Avoid inadvertent killing (e.g., by `killall python`) of the kernel runner daemon inside user containers by changing the process title not to include "python" ([#1090](https://github.com/lablup/backend.ai/issues/1090))
* Add `--local` option to `mgr image rescan` command to directly scan the local Docker daemon's image list for all-in-one development setups ([#1097](https://github.com/lablup/backend.ai/issues/1097))

### Fixes
* Add missing `await` for a jupyter-client API when shutting down the kernel runner, as a follow-up fix to #873 ([#915](https://github.com/lablup/backend.ai/issues/915))
* Improve scriptability of the `session events` CLI command by ensuring stdout flush and providing well-formatted JSON outputs of event data ([#925](https://github.com/lablup/backend.ai/issues/925))
* Continue the server operation with a warning even when the aiomonitor thread could not be started and adjust the default aiomonitor ports out of the ephemeral port range ([#928](https://github.com/lablup/backend.ai/issues/928))
* Fill the request payload with the plain-text request body when the web login handler is called without encryption.  This was a regression after introducing the login payload encryption. ([#929](https://github.com/lablup/backend.ai/issues/929))
* Apply vfolder_host_permission to vfolder api. ([#946](https://github.com/lablup/backend.ai/issues/946))
* Change the setting position of the `resp` to avoid AttributeError that occurs during converting from str to hex. ([#954](https://github.com/lablup/backend.ai/issues/954))
* Add comment out on gpfs sample volume when setting up the development environment with ./script/install-dev.sh ([#965](https://github.com/lablup/backend.ai/issues/965))
* Add command line logging option to manager, agent and storage ([#971](https://github.com/lablup/backend.ai/issues/971))
* Disable the socket-relay container on macOS to avoid UNIX socket bind-mount compatibility issue in for macOS + virtiofs setups ([#986](https://github.com/lablup/backend.ai/issues/986))
* Disable the socket-relay container mount on macOS to avoid UNIX socket bind-mount compatibility issue in for macOS + virtiofs setups ([#993](https://github.com/lablup/backend.ai/issues/993))
* Fix `mpirun` failing to run when trying to specify mutlple hosts on multi-container session ([#995](https://github.com/lablup/backend.ai/issues/995))
* Handle vary docker container creation fail. ([#1002](https://github.com/lablup/backend.ai/issues/1002))
* Fix `--limit` option being treated as `str` instead of `int` ([#1003](https://github.com/lablup/backend.ai/issues/1003))
* Rollback predicate mutations early when there is no candidate agent for a given image architecture. ([#1004](https://github.com/lablup/backend.ai/issues/1004))
* Remove unused loop in CLI generate_paginated_results function, remove some vars of the function and rename the function. ([#1007](https://github.com/lablup/backend.ai/issues/1007))
* Update `concurrency_used` per access key by number of sessions rather kernels. ([#1029](https://github.com/lablup/backend.ai/issues/1029))
* Unable to delete a data folder (vfolder) when its host directory or intermediate parent directories were not exist. ([#1040](https://github.com/lablup/backend.ai/issues/1040))
* Replace accessing non-existent `ImageRow.installed` with direct Redis queries in the `mgr image list --installed` command ([#1063](https://github.com/lablup/backend.ai/issues/1063))
* Fix the agent logs partially missing depending on how the `ai.backend.agent.server` module is executed ([#1064](https://github.com/lablup/backend.ai/issues/1064))
* Update agent's resource usage strictly after kernel creation, cancel and termination. ([#1069](https://github.com/lablup/backend.ai/issues/1069))
* Add a new line in SSH keypairs to prevent possible errors for some keys in registering them to `ssh-agent`. ([#1071](https://github.com/lablup/backend.ai/issues/1071))
* Removed no more used parameter with download_file and download_single from AgentRegistry ([#1076](https://github.com/lablup/backend.ai/issues/1076))
* Update session-related events, introducing the `SessionTerminating` event and using proper session IDs instead of kernel IDs ([#1083](https://github.com/lablup/backend.ai/issues/1083))
* Preserve the `PYTHONPATH` environment variable if defined by user-provided container images ([#1096](https://github.com/lablup/backend.ai/issues/1096))
* Fix typos and add proper whitespace in the comment and CLI help strings ([#1099](https://github.com/lablup/backend.ai/issues/1099))
* Fix `backend.ai ssh` CLI command in development setups ([#1101](https://github.com/lablup/backend.ai/issues/1101))
* Fix a regression bug in `session watch` command ([#1103](https://github.com/lablup/backend.ai/issues/1103))
* Resolve an error from `backend.ai admin group info` by taking the first returned group item ([#1104](https://github.com/lablup/backend.ai/issues/1104))
* Assign variables before the inner function which attempts to access them. ([#1112](https://github.com/lablup/backend.ai/issues/1112))
* When the session is in the PENDING, PREPARING state, assign the initial value to 'requested_slots' to know 'occupied_slots'. ([#1115](https://github.com/lablup/backend.ai/issues/1115))

### Documentation Updates
* Guide to install Backend.AI with package (wheel). ([#939](https://github.com/lablup/backend.ai/issues/939))

### External Dependency Updates
* Remove dependency to `python-snappy` ([#1010](https://github.com/lablup/backend.ai/issues/1010))
* Upgrade the hiredis version to 2.2.2, which was hold back to 1.x due to unexpected segfaults in its early 2.x versions ([#1025](https://github.com/lablup/backend.ai/issues/1025))

### Miscellaneous
* Upgrade the mypy version to 0.991 ([#972](https://github.com/lablup/backend.ai/issues/972))
* More explicit log for webserver's `login_handler` to filter and save the authentication logs only. ([#984](https://github.com/lablup/backend.ai/issues/984))
* Update the socket-relay container's base distro (Alpine) version to 3.17 to enable support for `AF_VSOCK` in the latest socat 1.7.4 package ([#988](https://github.com/lablup/backend.ai/issues/988))
* Add function that automate making news fragement process ([#989](https://github.com/lablup/backend.ai/issues/989))
* Bump base Python version from 3.10.8 to 3.10.9 to reduce potential bugs. ([#997](https://github.com/lablup/backend.ai/issues/997))


## 22.09 and earlier

Please refer the following per-package changelogs.

* [Unified changelog for the core components](https://github.com/lablup/backend.ai/blob/22.09/CHANGELOG.md)
