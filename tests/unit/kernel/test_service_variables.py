from pathlib import Path

import pytest

from ai.backend.kernel.service import (
    ServiceDefinition,
    ServiceOptions,
    ServiceParser,
)


class TestModelServiceStringCommand:
    @pytest.fixture
    def service_parser(self) -> ServiceParser:
        return ServiceParser({})

    @pytest.mark.parametrize("shell", [None, ""])
    async def test_without_shell_is_split(
        self,
        service_parser: ServiceParser,
        shell: str | None,
    ) -> None:
        service_parser.add_model_service(
            "model",
            {
                "start_command": "python service.py --flag 'a b'",
                "shell": shell,
                "pre_start_actions": [],
            },
        )

        cmdargs, env = await service_parser.start_service("model", set(), {})

        assert cmdargs == ["python", "service.py", "--flag", "a b"]
        assert env == {}

    async def test_with_shell_uses_shell_c(self, service_parser: ServiceParser) -> None:
        service_parser.add_model_service(
            "model",
            {
                "start_command": "python service.py && echo ok",
                "shell": "/bin/bash",
                "pre_start_actions": [],
            },
        )

        cmdargs, env = await service_parser.start_service("model", set(), {})

        assert cmdargs == ["/bin/bash", "-c", "python service.py && echo ok"]
        assert env == {}


_JSON_ARG = """'{"method":"mtp","num_speculative_tokens":3}'"""
_JINJA_OPTS: ServiceOptions = {
    "interpolation": {"delimiters": [{"start": "{{", "end": "}}"}]},
}


class TestServiceParserInterpolation:
    @pytest.fixture
    def service_parser(self, tmp_path: Path) -> ServiceParser:
        return ServiceParser({"runtime_path": "/usr/bin/python3", "out_dir": str(tmp_path)})

    @pytest.mark.parametrize(
        ("opts", "command", "expected"),
        [
            pytest.param({}, "{runtime_path}", "/usr/bin/python3", id="unset-uses-legacy"),
            pytest.param(
                _JINJA_OPTS, "{runtime_path}", "{runtime_path}", id="delimiter-skips-legacy"
            ),
            pytest.param(_JINJA_OPTS, "{{ runtime_path }}", "/usr/bin/python3", id="delimiter"),
        ],
    )
    async def test_command(
        self, service_parser: ServiceParser, opts: ServiceOptions, command: str, expected: str
    ) -> None:
        service_parser.services["app"] = ServiceDefinition(command=[command])

        cmdargs, _ = await service_parser.start_service("app", set(), opts)

        assert cmdargs == [expected]

    async def test_model_service_keeps_json_in_delimiter_mode(
        self, service_parser: ServiceParser
    ) -> None:
        service_parser.add_model_service(
            "model",
            {
                "start_command": f"exec {{{{ runtime_path }}}} server.py {_JSON_ARG}",
                "shell": "/bin/bash",
                "pre_start_actions": [],
            },
        )

        cmdargs, _ = await service_parser.start_service("model", set(), _JINJA_OPTS)

        assert cmdargs == ["/bin/bash", "-c", f"exec /usr/bin/python3 server.py {_JSON_ARG}"]

    @pytest.mark.parametrize(
        ("opts", "filename", "line", "expected"),
        [
            pytest.param(
                {},
                "{out_dir}/cfg",
                "c.settings = {{'python': '{runtime_path}'}}",
                "c.settings = {'python': '/usr/bin/python3'}\n",
                id="legacy",
            ),
            pytest.param(
                _JINJA_OPTS,
                "{{ out_dir }}/cfg",
                '{"python": "{{ runtime_path }}", "port": {port}}',
                '{"python": "/usr/bin/python3", "port": {port}}\n',
                id="delimiter",
            ),
        ],
    )
    async def test_prestart_args(
        self,
        service_parser: ServiceParser,
        tmp_path: Path,
        opts: ServiceOptions,
        filename: str,
        line: str,
        expected: str,
    ) -> None:
        service_parser.services["app"] = ServiceDefinition(
            command=["true"],
            prestart_actions=[
                {
                    "action": "write_file",
                    "args": {"filename": filename, "body": [line]},
                    "ref": None,
                },
            ],
        )

        await service_parser.start_service("app", set(), opts)

        assert (tmp_path / "cfg").read_text() == expected
