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
    "interpolation": {"mode": "delimiter", "delimiter": {"start": "{{", "end": "}}"}},
}


class TestServiceParserInterpolatorSelection:
    @pytest.fixture
    def service_parser(self) -> ServiceParser:
        service_parser = ServiceParser({"runtime_path": "/usr/bin/python3"})
        service_parser.services["app"] = ServiceDefinition(command=["{runtime_path}"])
        return service_parser

    @pytest.mark.parametrize(
        ("opts", "expected"),
        [
            pytest.param({}, "/usr/bin/python3", id="unset"),
            pytest.param(_JINJA_OPTS, "{runtime_path}", id="delimiter"),
        ],
    )
    async def test_selects_interpolator_from_options(
        self, service_parser: ServiceParser, opts: ServiceOptions, expected: str
    ) -> None:
        cmdargs, _ = await service_parser.start_service("app", set(), opts)

        assert cmdargs == [expected]


class TestDelimiterServiceParser:
    @pytest.fixture
    def service_parser(self, tmp_path: Path) -> ServiceParser:
        service_parser = ServiceParser({
            "runtime_path": "/usr/bin/python3",
            "out_dir": str(tmp_path),
        })
        service_parser.services["prestart"] = ServiceDefinition(
            command=["true"],
            prestart_actions=[
                {
                    "action": "write_file",
                    "args": {
                        "filename": "{{ out_dir }}/cfg.json",
                        "body": ['{"python": "{{ runtime_path }}", "port": {port}}'],
                    },
                    "ref": None,
                },
            ],
        )
        return service_parser

    async def test_model_service_fills_only_delimited_variables(
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

    async def test_prestart_args_use_delimiter(
        self, service_parser: ServiceParser, tmp_path: Path
    ) -> None:
        await service_parser.start_service("prestart", set(), _JINJA_OPTS)

        assert (tmp_path / "cfg.json").read_text() == (
            '{"python": "/usr/bin/python3", "port": {port}}\n'
        )


class TestLegacyServiceParser:
    @pytest.fixture
    def service_parser(self, tmp_path: Path) -> ServiceParser:
        service_parser = ServiceParser({
            "runtime_path": "/usr/bin/python3",
            "out_dir": str(tmp_path),
        })
        service_parser.services["prestart"] = ServiceDefinition(
            command=["{runtime_path}", "-m", "app"],
            prestart_actions=[
                {
                    "action": "write_file",
                    "args": {
                        "filename": "{out_dir}/cfg.py",
                        "body": ["c.settings = {{'python': '{runtime_path}'}}"],
                    },
                    "ref": None,
                },
            ],
        )
        return service_parser

    async def test_command_and_prestart_args_keep_legacy_syntax(
        self, service_parser: ServiceParser, tmp_path: Path
    ) -> None:
        cmdargs, _ = await service_parser.start_service("prestart", set(), {})

        assert cmdargs == ["/usr/bin/python3", "-m", "app"]
        assert (tmp_path / "cfg.py").read_text() == "c.settings = {'python': '/usr/bin/python3'}\n"
