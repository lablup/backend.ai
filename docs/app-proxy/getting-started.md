# Getting started

## Daily Development Workflows
Follows most of Backend.AI Core monorepo's convention (but without the documentation side). Check out Backend.AI's [Daily Development Workflow](https://docs.backend.ai/en/latest/dev/daily-workflows.html) for more.

## Setting up a AppProxy working set for development
- This guide assumes you have already set up a Backend.AI cluster with `install-dev.sh` method.

### Setting up the database
1. Generate password for new database account and replace with the placeholder (referenced as <Database Password>) on consequent steps. Make sure to avoid certain special characters, like # or %, which collides with postgres' URI separators.
2. Create a new account and database at the Backend.AI halfstack:
```sh
# from backend.ai repository directory
$ ./backend.ai mgr dbshell
```

```
backend# CREATE ROLE appproxy WITH LOGIN PASSWORD '<Database Password>';
backend# CREATE DATABASE appproxy;
backend# GRANT ALL PRIVILEGES ON DATABASE appproxy TO appproxy;
backend# \c appproxy
appproxy# GRANT ALL ON SCHEMA public TO appproxy;
```

3. Now get back to appproxy repository. Make a copy of `alembic.ini.template` file and save it as `alembic.ini`. Replace value of `[alembic].sqlalchemy.url` config as:
```
sqlalchemy.url = postgresql+asyncpg://appproxy:<Database Password>@localhost:8101/appproxy
```

4. Run `./py -m alembic upgrade head` to inject table structures to database.

### Preparing configuration files
1. Generate a new API secret and replace with the placeholder (referenced as <API Secret>) on consequent steps.
2. Copy `halfstack.toml` from both `configs/proxy-coordinator` and `configs/proxy-worker` and save as `proxy-coordinator.toml` and `proxy-worker.toml`.
3. Update `proxy-coordinator.toml`'s `[db]` block to match with the database connection info prepared before.
4. Update both configuration file's `[secrets].api_secret` to match with the string generated at step 1.
5. Update Backend.AI core database with new API secret:
```sh
# from backend.ai repository directory
$ ./backend.ai mgr dbshell
```

```
backend# UPDATE scaling_groups SET wsproxy_api_token = '<API Secret>', wsproxy_addr = 'http://localhost:10200';
```

### Finalizing
1. Start the coordinator first (`./backend.ai coordinator start-server --log-level debug`) and then load the worker (`./backend.ai worker start-server --log-level debug`).

## Additional steps for remote access
When you are trying to spawn a working AppProxy set on a remote place, like our development VM farm, some extra touches are required in order to properly recoginze both components.

### Terminologies
- local node (or just **node**): A server laying out of your workstation where AppProxy will be installed - development VMs, customer servers, ...
- remote / client: Where you physically pour your effort for the jobs - Your laptop, Desktop, ...

### Updating AppProxy configuration files
1. Find out the IP address of your node (where your AppProxy is installed). If you have multiple IPs assigned to the node, you have to choose one that the remote can establish the connection. If you are working on the development VM farm, this will be the IP starting with `10.82.`.
2. Update `proxy-coordinator.toml`'s `[proxy_coordinator].bind_addr.host`, `proxy-worker.toml`'s `[proxy_worker].api_bind_addr.host` and `[proxy_worker].port_proxy.bind_host` with the address discovered at step 1.
3. Update Backend.AI core database with the new IP address:
```sh
# from backend.ai repository directory
$ ./backend.ai mgr dbshell
```

```
backend# UPDATE scaling_groups SET wsproxy_addr = 'http://<IP found at step 1>:10200';
```
