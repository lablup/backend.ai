
from ..kernel import AbstractCodeRunner, AbstractKernel


class DummyKernel(AbstractKernel):
    async def close(self) -> None:
        pass

    async def create_code_runner(
        self,
        *,
        client_features: FrozenSet[str],
        api_version: int,
    ) -> "AbstractCodeRunner":
        pass

    async def check_status(self):
        pass

    async def get_completions(self, text, opts):
        pass

    async def get_logs(self):
        pass

    async def interrupt_kernel(self):
        pass


    async def start_service(self, service, opts):
        pass


    async def shutdown_service(self, service):
        pass


    async def check_duplicate_commit(self, kernel_id, subdir) -> CommitStatus:
        pass


    async def commit(self, kernel_id, subdir, filename):
        pass


    async def get_service_apps(self):
        pass


    async def accept_file(self, filename, filedata):
        pass


    async def download_file(self, filepath):
        pass


    async def download_single(self, filepath):
        pass


    async def list_files(self, path: str):
        pass

class DummyCodeRunner(AbstractCodeRunner):
    async def get_repl_in_addr(self) -> str:
        pass

    async def get_repl_out_addr(self) -> str:
        pass

    