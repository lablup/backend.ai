import ast
import graphlib
import sys
from pathlib import Path


def build_revision_map():
    rev_map = {}
    current_rev = None
    for p in Path("src/ai/backend/manager/models/alembic/versions").glob("*.py"):
        src = p.read_text()
        tree = ast.parse(src, filename=p)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                target = node.targets[0]
                if isinstance(target, ast.Name) and target.id in ("revision", "down_revision"):
                    values = []
                    assigned_value = node.value
                    match assigned_value:
                        case ast.Constant():
                            values.append(assigned_value.value)
                        case ast.Tuple():
                            for el in assigned_value.elts:
                                if isinstance(el, ast.Constant):
                                    values.append(el.value)
                    match target.id:
                        case "revision":
                            current_rev = values[0]
                            rev_map[current_rev] = {}
                        case "down_revision":
                            rev_map[current_rev] = {*values}
    return rev_map


def find_heads(rev_map):
    sorter = graphlib.TopologicalSorter(rev_map)
    heads = {*rev_map.keys()}
    for rev in reversed([*sorter.static_order()]):
        for down_rev in rev_map.get(rev, []):
            heads.discard(down_rev)
    return heads


def main():
    rev_map = build_revision_map()
    heads = find_heads(rev_map)
    print(f"Detected head revisions: {', '.join(heads)}")
    if len(heads) > 1:
        sys.exit(1)


if __name__ == "__main__":
    main()
