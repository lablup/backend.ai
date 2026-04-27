"""Write 4 KiB of deterministic content to stdout (binary)."""
import sys

data = (b"hello-scenario-fileio\n" * 200)[:4096]
sys.stdout.buffer.write(data)
