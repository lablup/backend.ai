import shutil
import time

from .loader import load_entry_points

main = load_entry_points()
# main object is called by the console script.

if __name__ == "__main__":
    # Execute right away if the module is directly called from CLI.
    try:
        main(max_content_width=shutil.get_terminal_size().columns - 2)
    finally:
        # Workaround for tokio/pyo3-async-runtimes shutdown race (BA-1976)
        time.sleep(0.1)
