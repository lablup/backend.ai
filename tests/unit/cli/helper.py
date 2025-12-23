import sys


def check_module_loaded(module_path: str) -> bool:
    for name, mod in sys.modules.items():
        if mod.__spec__ is None:
            continue
        if module_path in (mod.__spec__.origin or ""):
            print(name, mod)
            return True
    return False
