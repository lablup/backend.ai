import asyncio
import json
import logging
import os
import re
import subprocess
from pathlib import Path

from .. import BaseRunner, Terminal

# import pygit2
# from pygit2 import GIT_SORT_TOPOLOGICAL, GIT_SORT_REVERSE


log = logging.getLogger()


class Runner(BaseRunner):
    log_prefix = "shell-kernel"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def init_with_loop(self):
        self.user_input_queue = asyncio.Queue()
        self.term = Terminal(
            "/bin/bash",
            self.stopped,
            self.outsock,
            auto_restart=True,
        )

        parser_show = self.term.subparsers.add_parser("show")
        parser_show.add_argument("target", choices=("graph",), default="graph")
        parser_show.add_argument("path", type=str)
        parser_show.set_defaults(func=self.do_show)

        await self.term.start()

    async def build_heuristic(self) -> int:
        raise NotImplementedError

    async def execute_heuristic(self) -> int:
        raise NotImplementedError

    async def query(self, code_text) -> int:
        return await self.term.handle_command(code_text)

    async def complete(self, data):
        return []

    async def interrupt(self):
        # subproc interrupt is already handled by BaseRunner
        pass

    async def shutdown(self):
        await self.term.shutdown()

    def do_show(self, args):
        if args.target == "graph":
            commit_branch_table = {}
            commit_info = []

            if args.path in [".", None]:
                current_dir = Path(f"/proc/{self.term.pid}/cwd").resolve()
            else:
                current_dir = Path(args.path).resolve()
            os.chdir(current_dir)

            # Create commit-branch matching table.
            tree_cmd = ["git", "log", "--pretty=oneline", "--graph", "--source", "--branches"]
            run_res = subprocess.run(tree_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout = run_res.stdout.decode("utf-8")
            stderr = run_res.stderr.decode("utf-8")
            prog = re.compile(r"([a-z0-9]+)\s+(\S+).*")
            if stderr:
                self.outsock.send_multipart([b"stderr", stderr.encode("utf-8")])
                return

            for line in stdout.split("\n"):
                r = prog.search(line)
                if r and hasattr(r, "group") and r.group(1) and r.group(2):
                    oid = r.group(1)[:7]  # short oid
                    branch = r.group(2)
                    commit_branch_table[oid] = branch

            # Gather commit info w/ branch name.
            log_cmd = [
                "git",
                "log",
                "--pretty=format:%h||%p||%s||%cn",
                "--all",
                "--topo-order",
                "--reverse",
            ]
            run_res = subprocess.run(log_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout = run_res.stdout.decode("utf-8")
            for gitlog in stdout.split("\n"):
                items = gitlog.split("||")
                oid = items[0]
                parent_ids = items[1].split(" ")
                message = items[2]
                author = items[3]
                branch = commit_branch_table.get(oid, None)
                parent_branches = [commit_branch_table.get(pid, None) for pid in parent_ids]
                info = dict(
                    oid=oid,
                    parent_ids=parent_ids,
                    author=author,
                    message=message,
                    branch=branch,
                    parent_branches=parent_branches,
                )
                commit_info.append(info)

            self.outsock.send_multipart([
                b"media",
                json.dumps({
                    "type": "application/vnd.sorna.gitgraph",
                    "data": commit_info,
                }).encode("utf-8"),
            ])
        else:
            raise ValueError("Unsupported show target", args.target)

    async def start_service(self, service_info):
        return None, {}
