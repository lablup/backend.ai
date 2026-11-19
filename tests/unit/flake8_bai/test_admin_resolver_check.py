from collections.abc import Callable

type Lint = Callable[[str, str], list[tuple[int, str]]]

RESOLVER = "src/ai/backend/manager/api/gql/agent/resolver.py"


class TestAdminResolverCheckRule:
    def test_resolver_without_check_fails(self, lint: Lint) -> None:
        source = """
            @gql_root_field(meta)
            async def admin_agents(info: Info) -> None:
                return await info.context.adapters.agent.admin_search()
        """
        assert lint(RESOLVER, source) == [(3, "BAI402")]

    def test_check_after_other_statement_fails(self, lint: Lint) -> None:
        source = """
            @gql_mutation(meta)
            async def admin_update_agent(info: Info) -> None:
                adapter = info.context.adapters.agent
                check_admin_only()
                return await adapter.update()
        """
        assert lint(RESOLVER, source) == [(3, "BAI402")]

    def test_stub_resolver_fails(self, lint: Lint) -> None:
        source = """
            @gql_root_field(meta)
            async def admin_volumes(info: Info) -> None:
                raise NotImplementedError
        """
        assert lint(RESOLVER, source) == [(3, "BAI402")]

    def test_check_first_passes(self, lint: Lint) -> None:
        source = """
            @gql_root_field(meta)
            async def admin_agents(info: Info) -> None:
                check_admin_only()
                return await info.context.adapters.agent.admin_search()
        """
        assert lint(RESOLVER, source) == []

    def test_check_after_docstring_passes(self, lint: Lint) -> None:
        source = '''
            @gql_mutation(meta)
            async def admin_update_agent(info: Info) -> None:
                """Update an agent."""
                check_admin_only()
                return await info.context.adapters.agent.update()
        '''
        assert lint(RESOLVER, source) == []

    def test_undecorated_admin_helper_passes(self, lint: Lint) -> None:
        source = """
            def admin_filter(value: str) -> str:
                return value
        """
        assert lint(RESOLVER, source) == []

    def test_resolver_outside_gql_passes(self, lint: Lint) -> None:
        source = """
            @gql_root_field(meta)
            async def admin_agents(info: Info) -> None:
                return None
        """
        assert lint("src/ai/backend/manager/api/gql_legacy/agent.py", source) == []
