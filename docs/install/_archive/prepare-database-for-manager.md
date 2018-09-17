## Guide variables

⚠️ Prepare the values of the following variables before working with this page and replace their occurrences with the values when you follow the guide.

<table>
<tr><td><code>{NS}</code></td><td>The etcd namespace</td></tr>
<tr><td><code>{ETCDADDR}</code></td><td>The etcd cluster address (<code>{ETCDHOST}:{ETCDPORT}</code>, <code>localhost:8120</code> for development setup)</td></tr>
<tr><td><code>{DBADDR}</code></td><td>The PostgreSQL server address (<code>{DBHOST}:{DBPORT}</code>, <code>localhost:8100</code> for development setup)</td></tr>
<tr><td><code>{DBUSER}</code></td><td>The database username (e.g., <code>postgres</code> for development setup)</td></tr>
<tr><td><code>{DBPASS}</code></td><td>The database password (e.g., <code>develove</code> for development setup)</td></tr>
<tr><td><code>{STRGMOUNT}</code></td><td>The path to a directory that the manager and all agents share together (e.g., a network-shared storage mountpoint). Note that the path must be same across all the nodes that run the manager and agents.<br><br>
Development setup: Use an arbitrary empty directory where Docker containers can also mount as volumes — e.g., <a href="https://docs.docker.com/docker-for-mac/#file-sharing">Docker for Mac requires explicit configuration for mountable parent folders.</a></td></tr>
</table>

## Load initial etcd data

[![asciicast](https://asciinema.org/a/8vM2cEHEHQzCMaOummV4ruDAm.png)](https://asciinema.org/a/8vM2cEHEHQzCMaOummV4ruDAm)

```console
$ cd backend.ai-manager
```

Copy `sample-configs/image-metadata.yml` and `sample-configs/image-aliases.yml` and edit according to your setup.

```console
$ cp sample-configs/image-metadata.yml image-metadata.yml
$ cp sample-configs/image-aliases.yml image-aliases.yml
```

By default you can pull the images listed in the sample via `docker pull lablup/kernel-xxxx:tag`(e.g. `docker pull lablup/kernel-python-tensorflow:latest` for the latest tensorflow) as they are hosted on the public Docker registry.

### Load image registry metadata

(Instead of manually specifying environment variables, you may use `scripts/run-with-halfstack.sh` script in a development setup.)

```console
$ BACKEND_NAMESPACE={NS} BACKEND_ETCD_ADDR={ETCDADDR} \
> python -m ai.backend.manager.cli etcd update-images \
>        -f image-metadata.yml
```

### Load image aliases

```console
$ BACKEND_NAMESPACE={NS} BACKEND_ETCD_ADDR={ETCDADDR} \
> python -m ai.backend.manager.cli etcd update-aliases \
>        -f image-aliases.yml
```

### Set the default storage mount for virtual folders

```console
$ BACKEND_NAMESPACE={NS} BACKEND_ETCD_ADDR={ETCDADDR} \
> python -m ai.backend.manager.cli etcd put \
>        volumes/_vfroot {STRGMOUNT}
```

## Database Setup

### Create a new database

In docker-compose based configurations, you may skip this step.

```console
$ psql -h {DBHOST} -p {DBPORT} -U {DBUSER}
```

```
postgres=# CREATE DATABASE backend;
postgres=# \q
```

### Install database schema

Backend.AI uses [alembic](http://alembic.zzzcomputing.com/en/latest/) to manage database schema and its migration during version upgrades.
First, localize the sample config:

```console
$ cp alembic.ini.sample alembic.ini
```

Modify the line where `sqlalchemy.url` is set.
You may use the following shell command:
(ensure that special characters in your password are properly escaped)

```console
$ sed -i'' -e 's!^sqlalchemy.url = .*$!sqlalchemy.url = postgresql://{DBUSER}:{DBPASS}@{DBHOST}:{DBPORT}/backend!' alembic.ini
```

```console
$ python -m ai.backend.manager.cli schema oneshot head
```

example execution result
```console
201x-xx-xx xx:xx:xx INFO alembic.runtime.migration [MainProcess] Context impl PostgresqlImpl.
201x-xx-xx xx:xx:xx INFO alembic.runtime.migration [MainProcess] Will assume transactional DDL.
201x-xx-xx xx:xx:xx INFO ai.backend.manager.cli.dbschema [MainProcess] Detected a fresh new database.
201x-xx-xx xx:xx:xx INFO ai.backend.manager.cli.dbschema [MainProcess] Creating tables...
201x-xx-xx xx:xx:xx INFO ai.backend.manager.cli.dbschema [MainProcess] Stamping alembic version to head...
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running stamp_revision  -> f9971fbb34d9
```

NOTE: All sub-commands under "schema" uses alembic.ini to establish database connections.

### Load initial fixtures

Edit `ai/backend/manager/models/fixtures.py` so that you have a randomized admin keypair.

<span style="color:red">**(TODO: automate here!)**</span>

Then pour it to the database:

```console
$ python -m ai.backend.manager.cli \
>   --db-addr={DBHOST}:{DBPORT} \
>   --db-user={DBUSER} \
>   --db-password={DBPASS} 
>   --db-name=backend \
>   fixture populate example_keypair
```
example execution result
```console
201x-xx-xx xx:xx:xx INFO ai.backend.manager.cli.fixture [MainProcess] populating fixture 'example_keypair'
```