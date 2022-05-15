# import asyncio

# import pytest

# from ai.backend.agent.server import (
#     AgentRPCServer,
# )


# TODO: rewrite
'''
@pytest.fixture
async def agent(request, tmpdir, event_loop):
    config = argparse.Namespace()
    config.namespace = os.environ.get('BACKEND_NAMESPACE', 'testing')
    config.agent_host = '127.0.0.1'
    config.agent_port = 6001  # default 6001
    config.stat_port = 6002
    config.kernel_host_override = '127.0.0.1'
    etcd_addr = os.environ.get('BACKEND_ETCD_ADDR', '127.0.0.1:2379')
    redis_addr = os.environ.get('BACKEND_REDIS_ADDR', '127.0.0.1:6379')
    config.etcd_addr = host_port_pair(etcd_addr)
    config.redis_addr = host_port_pair(redis_addr)
    config.event_addr = '127.0.0.1:5000'  # dummy value
    config.docker_registry = 'lablup'
    config.debug = True
    config.debug_kernel = None
    config.kernel_aliases = None
    config.scratch_root = Path(tmpdir)
    config.limit_cpus = None
    config.limit_gpus = None
    config.debug_kernel = None
    config.debug_hook = None
    config.debug_jail = None
    config.debug_skip_container_deletion = False

    agent = None

    config.instance_id = await identity.get_instance_id()
    config.inst_type = await identity.get_instance_type()
    config.region = await identity.get_instance_region()
    print(f'serving test agent: {config.instance_id} ({config.inst_type}),'
          f' ip: {config.agent_host}')
    agent = AgentRPCServer(config, loop=event_loop)
    await agent.init(skip_detect_manager=True)
    await asyncio.sleep(0)

    yield agent

    print('shutting down test agent...')
    if agent:
        await agent.shutdown()
    await asyncio.sleep(3)


@pytest.mark.asyncio
async def test_get_extra_volumes(docker):
    # No extra volumes
    mnt_list = await get_extra_volumes(docker, 'python:latest')
    assert len(mnt_list) == 0

    # Create fake deeplearning sample volume and check it will be returned
    vol = None
    try:
        config = {'Name': 'deeplearning-samples'}
        vol = await docker.volumes.create(config)
        mnt_list = await get_extra_volumes(docker, 'python-tensorflow:latest')
    finally:
        if vol:
            await vol.delete()

    assert len(mnt_list) == 1
    assert mnt_list[0].name == 'deeplearning-samples'


@pytest.mark.asyncio
async def test_get_kernel_id_from_container(docker, container):
    container_list = await docker.containers.list()
    kid = await get_kernel_id_from_container(container_list[0])

    assert kid == 'test-container'  # defined as in the fixture


@pytest.fixture
async def kernel_info(agent, docker):
    kernel_id = str(uuid.uuid4())
    config = {
        'lang': 'lua:5.3-alpine',
        'limits': {'cpu_slot': 1, 'gpu_slot': 0, 'mem_slot': 1, 'tpu_slot': 0},
        'mounts': [],
        'environ': {},
    }
    kernel_info = await agent.create_kernel(kernel_id, config)

    try:
        yield kernel_info
    finally:
        if kernel_info['id'] in agent.container_registry:
            # Container id may be changed (e.g. restarting kernel), so we
            # should not rely on the initial value of the container_id.
            container_info = agent.container_registry[kernel_info['id']]
            container_id = container_info['container_id']
        else:
            # If fallback to initial container_id if kernel is deleted.
            container_id = kernel_info['container_id']
        try:
            container = docker.containers.container(container_id)
            cinfo = await container.show() if container else None
        except aiodocker.exceptions.DockerError:
            cinfo = None
        if cinfo and cinfo['State']['Status'] != 'removing':
            await container.delete(force=True)


@pytest.mark.integration
def test_ping(agent):
    ret = agent.ping('ping~')
    assert ret == 'ping~'


@pytest.mark.integration
@pytest.mark.asyncio
async def test_scan_running_containers(agent, kernel_info, docker):
    agent.container_registry.clear()
    assert kernel_info['id'] not in agent.container_registry
    await agent.scan_running_containers()
    assert agent.container_registry[kernel_info['id']]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_kernel(agent, docker):
    kernel_id = str(uuid.uuid4())
    config = {
        'lang': 'lablup/lua:5.3-alpine',
        'limits': {'cpu_slot': 1, 'gpu_slot': 0, 'mem_slot': 1, 'tpu_slot': 0},
        'mounts': [],
        'environ': {},
    }

    kernel_info = container_info = None
    try:
        kernel_info = await agent.create_kernel(kernel_id, config)
        container_info = agent.container_registry[kernel_id]
    finally:
        container = docker.containers.container(kernel_info['container_id'])
        await container.delete(force=True)

    assert kernel_info
    assert container_info
    assert kernel_info['id'] == kernel_id
    # TODO: rewrite using resource_spec:
    #   assert len(kernel_info['cpu_set']) == 1
    assert container_info['lang'] == config['lang']
    assert container_info['container_id'] == kernel_info['container_id']
    # TODO: rewrite using resource_spec:
    #   assert container_info['limits'] == config['limits']
    #   assert container_info['mounts'] == config['mounts']


@pytest.mark.integration
@pytest.mark.asyncio
async def test_destroy_kernel(agent, kernel_info):
    stat = await agent.destroy_kernel(kernel_info['id'])

    assert stat
    assert 'cpu_used' in stat
    assert 'mem_max_bytes' in stat
    assert 'mem_cur_bytes' in stat
    assert 'net_rx_bytes' in stat
    assert 'net_tx_bytes' in stat
    assert 'io_read_bytes' in stat
    assert 'io_write_bytes' in stat
    assert 'io_max_scratch_size' in stat
    assert 'io_cur_scratch_size' in stat


@pytest.mark.integration
@pytest.mark.asyncio
async def test_restart_kernel(agent, kernel_info):
    kernel_id = kernel_info['id']
    container_id = kernel_info['container_id']
    new_config = {
        'lang': 'lablup/lua:5.3-alpine',
        'limits': {'cpu_slot': 1, 'gpu_slot': 0, 'mem_slot': 1, 'tpu_slot': 0},
        'mounts': [],
    }

    ret = await agent.restart_kernel(kernel_id, new_config)

    assert container_id != ret['container_id']


@pytest.mark.integration
@pytest.mark.asyncio
async def test_restart_kernel_cancel_code_execution(
        agent, kernel_info, event_loop):
    async def execute_code():
        nonlocal kernel_info
        api_ver = 2
        kid = kernel_info['id']
        runid = 'test-run-id'
        mode = 'query'
        code = ('local clock = os.clock\n'
                'function sleep(n)\n'
                '  local t0 = clock()\n'
                '  while clock() - t0 <= n do end\n'
                'end\n'
                'sleep(10)\nprint("code executed")')
        while True:
            ret = await agent.execute(api_ver, kid, runid, mode, code, {})
            if ret is None:
                break
            elif ret['status'] == 'finished':
                break
            elif ret['status'] == 'continued':
                mode = 'continue',
                code = ''
            else:
                raise Exception('Invalid execution status')
        return ret

    async def restart_kernel():
        nonlocal kernel_info
        kernel_id = kernel_info['id']
        new_config = {
            'lang': 'lablup/lua:5.3-alpine',
            'limits': {'cpu_slot': 1, 'gpu_slot': 0, 'mem_slot': 1, 'tpu_slot': 0},
            'mounts': [],
        }
        await agent.restart_kernel(kernel_id, new_config)

    t1 = asyncio.ensure_future(execute_code(), loop=event_loop)
    start = datetime.now()
    await asyncio.sleep(1)
    t2 = asyncio.ensure_future(restart_kernel(), loop=event_loop)
    results = await asyncio.gather(t1, t2)
    end = datetime.now()

    assert results[0] is None  # no execution result
    assert (end - start).total_seconds() < 10


@pytest.mark.integration
@pytest.mark.asyncio
async def test_execute(agent, kernel_info):
    # Test with lua:5.3-alpine image only
    api_ver = 2
    kid = kernel_info['id']
    runid = 'test-run-id'
    mode = 'query'
    code = 'print(17)'

    while True:
        ret = await agent.execute(api_ver, kid, runid, mode, code, {})
        if ret['status'] == 'finished':
            break
        elif ret['status'] == 'continued':
            mode = 'continue',
            code = ''
        else:
            raise Exception('Invalid execution status')

    assert ret['console'][0][0] == 'stdout'
    assert ret['console'][0][1] == '17\n'


@pytest.mark.integration
@pytest.mark.asyncio
async def test_execute_batch_mode(agent, kernel_info):
    # Test with lua:5.3-alpine image only
    api_ver = 2
    kid = kernel_info['id']
    runid = 'test-run-id'
    mode = 'batch'
    code = ''
    opt = {'clean': '*',
           'build': '*',
           'exec': '*'}

    # clean_finished = False
    build_finished = False

    await agent.upload_file(kid, 'main.lua', b'print(17)')
    while True:
        ret = await agent.execute(api_ver, kid, runid, mode, code, opt)
        if ret['status'] == 'finished':
            # assert clean_finished and build_finished
            assert build_finished
            break
        # elif ret['status'] == 'clean-finished':
        #     assert not clean_finished and not build_finished
        #     clean_finished = True
        #     mode = 'continue'
        elif ret['status'] == 'build-finished':
            # assert clean_finished and not build_finished
            assert not build_finished
            build_finished = True
            mode = 'continue'
        elif ret['status'] == 'continued':
            mode = 'continue'
        else:
            raise Exception('Invalid execution status')

    assert ret['console'][0][0] == 'stdout'
    assert ret['console'][0][1] == '17\n'


@pytest.mark.integration
@pytest.mark.asyncio
async def test_upload_file(agent, kernel_info):
    fname = 'test.txt'
    await agent.upload_file(kernel_info['id'], fname, b'test content')
    uploaded_to = agent.config.scratch_root / kernel_info['id'] / '.work' / fname
    assert uploaded_to.exists()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_reset(agent, docker):
    kernel_ids = []
    container_ids = []
    config = {
        'lang': 'lablup/lua:5.3-alpine',
        'limits': {'cpu_slot': 1, 'gpu_slot': 0, 'mem_slot': 1, 'tpu_slot': 0},
        'mounts': [],
    }

    try:
        # Create two kernels
        for i in range(2):
            kid = str(uuid.uuid4())
            kernel_ids.append(kid)
            info = await agent.create_kernel(kid, config)
            container_ids.append(info['container_id'])

        # 2 containers are created
        assert docker.containers.container(container_ids[0])
        assert docker.containers.container(container_ids[1])

        await agent.reset()

        # Containers are destroyed
        with pytest.raises(aiodocker.exceptions.DockerError):
            c1 = docker.containers.container(container_ids[0])
            c1info = await c1.show()
            if c1info['State']['Status'] == 'removing':
                raise aiodocker.exceptions.DockerError(
                    404, {'message': 'success'})
        with pytest.raises(aiodocker.exceptions.DockerError):
            c2 = docker.containers.container(container_ids[1])
            c2info = await c2.show()
            if c2info['State']['Status'] == 'removing':
                raise aiodocker.exceptions.DockerError(
                    404, {'message': 'success'})
    finally:
        for cid in container_ids:
            try:
                container = docker.containers.container(cid)
                cinfo = await container.show() if container else None
            except aiodocker.exceptions.DockerError:
                cinfo = None
            if cinfo and cinfo['State']['Status'] != 'removing':
                await container.delete(force=True)
'''
