import json
import sys
from pathlib import Path


def extract_dotfiles():
    try:
        with open("/home/config/dotfiles.json") as fr:
            dotfiles = json.loads(fr.read())
    except FileNotFoundError:
        return
    work_dir = Path("/home/work")
    for dotfile in dotfiles:
        file_path = work_dir / dotfile["path"]
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(dotfile["data"])
        except IOError:
            print(f"failed to write dotfile: {file_path}", file=sys.stderr)
        try:
            tmp = Path(file_path)
            while tmp != work_dir:
                tmp.chmod(int(dotfile["perm"], 8))
                tmp = tmp.parent
        except IOError:
            print(f"failed to chmod dotfile: {file_path}", file=sys.stderr)


if __name__ == "__main__":
    extract_dotfiles()
