import textwrap

from pyinfra import host
from pyinfra.facts.server import Command


def get_docker_compose_cmd() -> str:
    """Return the available Docker Compose command on the remote system."""
    script = textwrap.dedent(
        """\
    docker compose version >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "docker compose"
    else
        echo "docker-compose"
    fi
    """
    )
    result = host.get_fact(Command, script)
    return result.strip()
