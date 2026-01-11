import shutil

from .loader import load_entry_points

main = load_entry_points()
# main object is called by the console script.

if __name__ == "__main__":
    # Execute right away if the module is directly called from CLI.
    main(max_content_width=shutil.get_terminal_size().columns - 2)
