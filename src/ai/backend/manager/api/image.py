import base64
import secrets
from typing import (
    Any,
    Iterable,
    TYPE_CHECKING,
    Tuple,
)

from aiohttp import web
import aiohttp_cors
import jinja2
import sqlalchemy as sa
import trafaret as t

from ai.backend.common import validators as tx
from ai.backend.common.docker import ImageRef
from ai.backend.common.etcd import (
    quote as etcd_quote,
)
from ai.backend.common.types import (
    SessionTypes,
)

from ..defs import DEFAULT_IMAGE_ARCH, DEFAULT_ROLE
from ..models import (
    domains, groups, query_allowed_sgroups,
    association_groups_users as agus,
)
from ..types import UserScope
from .auth import admin_required
from .exceptions import InvalidAPIParameters
from .manager import ALL_ALLOWED, READ_ALLOWED, server_status_required
from .types import CORSOptions, WebMiddleware
from .utils import (
    check_api_params,
)

if TYPE_CHECKING:
    from .context import RootContext


DOCKERFILE_TEMPLATE = r"""# syntax = docker/dockerfile:1.0-experimental
FROM {{ src }}
MAINTAINER Backend.AI Manager

USER root

{% if runtime_type == 'python' -%}
ENV PYTHONUNBUFFERED=1 \
    LANG=C.UTF-8

RUN --mount=type=bind,source=wheelhouse,target=/root/wheelhouse \
    PIP_OPTS="--no-cache-dir --no-index --find-links=/root/wheelhouse" && \
    {{ runtime_path }} -m pip install ${PIP_OPTS} -U pip setuptools && \
    {{ runtime_path }} -m pip install ${PIP_OPTS} Pillow && \
    {{ runtime_path }} -m pip install ${PIP_OPTS} h5py && \
    {{ runtime_path }} -m pip install ${PIP_OPTS} ipython && \
    {{ runtime_path }} -m pip install ${PIP_OPTS} jupyter && \
    {{ runtime_path }} -m pip install ${PIP_OPTS} jupyterlab

# Install ipython kernelspec
RUN {{ runtime_path }} -m ipykernel install \
    --prefix={{ runtime_path.parent.parent }} \
    --display-name "{{ brand }} on Backend.AI"
{%- endif %}

LABEL ai.backend.kernelspec="1" \
      ai.backend.envs.corecount="{{ cpucount_envvars | join(',') }}" \
      ai.backend.features="{% if has_ipykernel %}query batch {% endif %}uid-match" \
      ai.backend.resource.min.cpu="{{ min_cpu }}" \
      ai.backend.resource.min.mem="{{ min_mem }}" \
      ai.backend.resource.preferred.shmem="{{ pref_shmem }}" \
      ai.backend.accelerators="{{ accelerators | join(',') }}" \
{%- if 'cuda' is in accelerators %}
      ai.backend.resource.min.cuda.device=1 \
      ai.backend.resource.min.cuda.shares=0.1 \
{%- endif %}
      ai.backend.base-distro="{{ base_distro }}" \
{%- if service_ports %}
      ai.backend.service-ports="{% for item in service_ports -%}
          {{- item['name'] }}:
          {{- item['protocol'] }}:
          {%- if (item['ports'] | length) > 1 -%}
              [{{ item['ports'] | join(',') }}]
          {%- else -%}
              {{ item['ports'][0] }}
          {%- endif -%}
          {{- ',' if not loop.last }}
      {%- endfor %}" \
{%- endif %}
      ai.backend.runtime-type="{{ runtime_type }}" \
      ai.backend.runtime-path="{{ runtime_path }}"
"""  # noqa


@server_status_required(READ_ALLOWED)
@admin_required
async def get_import_image_form(request: web.Request) -> web.Response:
    root_ctx: RootContext = request.app['_root.context']
    async with root_ctx.db.begin() as conn:
        query = (
            sa.select([groups.c.name])
            .select_from(
                sa.join(
                    groups, domains,
                    groups.c.domain_name == domains.c.name,
                ),
            )
            .where(
                (domains.c.name == request['user']['domain_name']) &
                (domains.c.is_active) &
                (groups.c.is_active),
            )
        )
        result = await conn.execute(query)
        rows = result.fetchall()
        accessible_groups = [row['name'] for row in rows]

        # FIXME: Currently this only consider domain-level scaling group associations,
        #        thus ignoring the group name query.
        rows = await query_allowed_sgroups(
            conn, request['user']['domain_name'], '', request['keypair']['access_key'],
        )
        accessible_scaling_groups = [row['name'] for row in rows]

    return web.json_response({
        'fieldGroups': [
            {
                'name': 'Import options',
                'fields': [
                    {
                        'name': 'src',
                        'type': 'string',
                        'label': 'Source Docker image',
                        'placeholder': 'index.docker.io/lablup/tensorflow:2.0-source',
                        'help': 'The full Docker image name to import from. '
                                'The registry must be accessible by the client.',
                    },
                    {
                        'name': 'target',
                        'type': 'string',
                        'label': 'Target Docker image',
                        'placeholder': 'index.docker.io/lablup/tensorflow:2.0-target',
                        'help': 'The full Docker image name of the imported image.'
                                'The registry must be accessible by the client.',
                    },
                    {
                        'name': 'brand',
                        'type': 'string',
                        'label': 'Name of Jupyter kernel',
                        'placeholder': 'TensorFlow 2.0',
                        'help': 'The name of kernel to be shown in the Jupyter\'s kernel menu. '
                                'This will be suffixed with "on Backend.AI".',
                    },
                    {
                        'name': 'baseDistro',
                        'type': 'choice',
                        'choices': ['ubuntu', 'centos'],
                        'default': 'ubuntu',
                        'label': 'Base LINUX distribution',
                        'help': 'The base Linux distribution used by the source image',
                    },
                    {
                        'name': 'minCPU',
                        'type': 'number',
                        'min': 1,
                        'max': None,
                        'label': 'Minimum required CPU core(s)',
                        'help': 'The minimum number of CPU cores required by the image',
                    },
                    {
                        'name': 'minMemory',
                        'type': 'binarysize',
                        'min': '64m',
                        'max': None,
                        'label': 'Minimum required memory size',
                        'help': 'The minimum size of the main memory required by the image',
                    },
                    {
                        'name': 'preferredSharedMemory',
                        'type': 'binarysize',
                        'min': '64m',
                        'max': None,
                        'label': 'Preferred shared memory size',
                        'help': 'The preferred (default) size of the shared memory',
                    },
                    {
                        'name': 'supportedAccelerators',
                        'type': 'multichoice[str]',
                        'choices': ['cuda'],
                        'default': 'cuda',
                        'label': 'Supported accelerators',
                        'help': 'The list of accelerators supported by the image',
                    },
                    {
                        'name': 'runtimeType',
                        'type': 'choice',
                        'choices': ['python'],
                        'default': 'python',
                        'label': 'Runtime type of the image',
                        'help': 'The runtime type of the image. '
                                'Currently, the source image must have installed Python 2.7, 3.5, 3.6, '
                                'or 3.7 at least to import. '
                                'This will be used as the kernel of Jupyter service in this image.',
                    },
                    {
                        'name': 'runtimePath',
                        'type': 'string',
                        'default': '/usr/local/bin/python',
                        'label': 'Path of the runtime',
                        'placeholder': '/usr/local/bin/python',
                        'help': 'The path to the main executalbe of runtime language of the image. '
                                'Even for the same "python"-based images, this may differ significantly '
                                'image by image. (e.g., /usr/bin/python, /usr/local/bin/python, '
                                '/opt/something/bin/python, ...) '
                                'Please check this carefully not to get confused with OS-default ones '
                                'and custom-installed ones.',
                    },
                    {
                        'name': 'CPUCountEnvs',
                        'type': 'list[string]',
                        'default': ['NPROC', 'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS'],
                        'label': 'CPU count environment variables',
                        'help': 'The name of environment variables to be overriden to the number of CPU '
                                'cores actually allocated to the container. Required for legacy '
                                'computation libraries.',
                    },
                    {
                        'name': 'servicePorts',
                        'type': 'multichoice[template]',
                        'templates': [
                            {'name': 'jupyter', 'protocol': 'http', 'ports': [8080]},
                            {'name': 'jupyterlab', 'protocol': 'http', 'ports': [8090]},
                            {'name': 'tensorboard', 'protocol': 'http', 'ports': [6006]},
                            {'name': 'digits', 'protocol': 'http', 'ports': [5000]},
                            {'name': 'vscode', 'protocol': 'http', 'ports': [8180]},
                            {'name': 'h2o-dai', 'protocol': 'http', 'ports': [12345]},
                        ],
                        'label': 'Supported service ports',
                        'help': 'The list of service ports supported by this image. '
                                'Note that sshd (port 2200) and ttyd (port 7681) are intrinsic; '
                                'they are always included regardless of the source image. '
                                'The port number 2000-2003 are reserved by Backend.AI, and '
                                'all port numbers must be larger than 1024 and smaller than 65535.',
                    },
                ],
            },
            {
                'name': 'Import Task Options',
                'help': 'The import task uses 1 CPU core and 2 GiB of memory.',
                'fields': [
                    {
                        'name': 'group',
                        'type': 'choice',
                        'choices': accessible_groups,
                        'label': 'Group to build image',
                        'help': 'The user group where the import task will be executed.',
                    },
                    {
                        'name': 'scalingGroup',
                        'type': 'choice',
                        'choices': accessible_scaling_groups,
                        'label': 'Scaling group to build image',
                        'help': 'The scaling group where the import task will take resources from.',
                    },
                ],
            },
        ],
    })


@server_status_required(ALL_ALLOWED)
@admin_required
@check_api_params(
    t.Dict({
        t.Key('src'): t.String,
        t.Key('target'): t.String,
        t.Key('architecture', default=DEFAULT_IMAGE_ARCH): t.String,
        t.Key('launchOptions', default={}): t.Dict({
            t.Key('scalingGroup', default='default'): t.String,
            t.Key('group', default='default'): t.String,
        }).allow_extra('*'),
        t.Key('brand'): t.String,
        t.Key('baseDistro'): t.Enum('ubuntu', 'centos'),
        t.Key('minCPU', default=1): t.Int[1:],
        t.Key('minMemory', default='64m'): tx.BinarySize,
        t.Key('preferredSharedMemory', default='64m'): tx.BinarySize,
        t.Key('supportedAccelerators'): t.List(t.String),
        t.Key('runtimeType'): t.Enum('python'),
        t.Key('runtimePath'): tx.Path(type='file', allow_nonexisting=True, resolve=False),
        t.Key('CPUCountEnvs'): t.List(t.String),
        t.Key('servicePorts', default=[]): t.List(t.Dict({
            t.Key('name'): t.String,
            t.Key('protocol'): t.Enum('http', 'tcp', 'pty'),
            t.Key('ports'): t.List(t.Int[1:65535], min_length=1),
        })),
    }).allow_extra('*'))
async def import_image(request: web.Request, params: Any) -> web.Response:
    """
    Import a docker image and convert it to a Backend.AI-compatible one,
    by automatically installing a few packages and adding image labels.

    Currently we only support auto-conversion of Python-based kernels (e.g.,
    NGC images) which has its own Python version installed.

    Internally, it launches a temporary kernel in an arbitrary agent within
    the client's domain, the "default" group, and the "default" scaling group.
    (The client may change the group and scaling group using *launchOptions.*
    If the client is a super-admin, it uses the "default" domain.)

    This temporary kernel occupies only 1 CPU core and 1 GiB memory.
    The kernel concurrency limit is not applied here, but we choose an agent
    based on their resource availability.
    The owner of this kernel is always the client that makes the API request.

    This API returns immediately after launching the temporary kernel.
    The client may check the progress of the import task using session logs.
    """

    tpl = jinja2.Template(DOCKERFILE_TEMPLATE)
    root_ctx: RootContext = request.app['_root.context']

    async with root_ctx.db.begin() as conn:
        query = (
            sa.select([domains.c.allowed_docker_registries])
            .select_from(domains)
            .where(domains.c.name == request['user']['domain_name'])
        )
        result = await conn.execute(query)
        allowed_docker_registries = result.scalar()

    # TODO: select agent to run image builder based on image architecture
    source_image = ImageRef(params['src'], allowed_docker_registries, params['architecture'])
    target_image = ImageRef(params['target'], allowed_docker_registries, params['architecture'])

    # TODO: validate and convert arguments to template variables
    dockerfile_content = tpl.render({
        'base_distro': params['baseDistro'],
        'cpucount_envvars': ['NPROC', 'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS'],
        'runtime_type': params['runtimeType'],
        'runtime_path': params['runtimePath'],
        'service_ports': params['servicePorts'],
        'min_cpu': params['minCPU'],
        'min_mem': params['minMemory'],
        'pref_shmem': params['preferredSharedMemory'],
        'accelerators': params['supportedAccelerators'],
        'src': params['src'],
        'brand': params['brand'],
        'has_ipykernel': True,  # TODO: in the future, we may allow import of service-port only kernels.
    })

    session_creation_id = secrets.token_urlsafe(32)
    session_id = f'image-import-{secrets.token_urlsafe(8)}'
    access_key = request['keypair']['access_key']
    resource_policy = request['keypair']['resource_policy']

    async with root_ctx.db.begin() as conn:
        query = (
            sa.select([groups.c.id])
            .select_from(
                sa.join(
                    groups, domains,
                    groups.c.domain_name == domains.c.name,
                ),
            )
            .where(
                (domains.c.name == request['user']['domain_name']) &
                (groups.c.name == params['launchOptions']['group']) &
                (domains.c.is_active) &
                (groups.c.is_active),
            )
        )
        result = await conn.execute(query)
        group_id = result.scalar()
        if group_id is None:
            raise InvalidAPIParameters("Invalid domain or group.")

        query = (
            sa.select([agus])
            .select_from(agus)
            .where(
                (agus.c.user_id == request['user']['uuid']) &
                (agus.c.group_id == group_id),
            )
        )
        result = await conn.execute(query)
        row = result.first()
        if row is None:
            raise InvalidAPIParameters("You do not belong to the given group.")

    importer_image = ImageRef(
        root_ctx.local_config['manager']['importer-image'],
        allowed_docker_registries,
        params['architecture'],
    )

    docker_creds = {}
    for img_ref in (source_image, target_image):
        registry_info = await root_ctx.shared_config.etcd.get_prefix_dict(
            f'config/docker/registry/{etcd_quote(img_ref.registry)}')
        docker_creds[img_ref.registry] = {
            'username': registry_info.get('username'),
            'password': registry_info.get('password'),
        }

    kernel_id = await root_ctx.registry.enqueue_session(
        session_creation_id,
        session_id,
        access_key,
        [{
            'image_ref': importer_image,
            'cluster_role': DEFAULT_ROLE,
            'cluster_idx': 1,
            'cluster_hostname': f"{DEFAULT_ROLE}1",
            'creation_config': {
                'resources': {'cpu': '1', 'mem': '2g'},
                'scaling_group': params['launchOptions']['scalingGroup'],
                'environ': {
                    'SRC_IMAGE': source_image.canonical,
                    'TARGET_IMAGE': target_image.canonical,
                    'RUNTIME_PATH': params['runtimePath'],
                    'BUILD_SCRIPT': (
                        base64.b64encode(dockerfile_content.encode('utf8')).decode('ascii')
                    ),
                },
            },
            'startup_command': '/root/build-image.sh',
            'bootstrap_script': '',
        }],
        None,
        SessionTypes.BATCH,
        resource_policy,
        user_scope=UserScope(
            domain_name=request['user']['domain_name'],
            group_id=group_id,
            user_uuid=request['user']['uuid'],
            user_role=request['user']['role'],
        ),
        internal_data={
            'domain_socket_proxies': ['/var/run/docker.sock'],
            'docker_credentials': docker_creds,
            'prevent_vfolder_mounts': True,
            'block_service_ports': True,
        },
    )
    return web.json_response({
        'importTask': {
            'sessionId': session_id,
            'taskId': str(kernel_id),
        },
    }, status=200)


async def init(app: web.Application) -> None:
    pass


async def shutdown(app: web.Application) -> None:
    pass


def create_app(default_cors_options: CORSOptions) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    app['prefix'] = 'image'
    app['api_versions'] = (4,)
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    cors.add(app.router.add_route('GET', '/import', get_import_image_form))
    cors.add(app.router.add_route('POST', '/import', import_image))
    return app, []
