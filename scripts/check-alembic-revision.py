import sys
import os
import ast


def check_alembic_file_for_pass(file_path):
    if not os.path.isfile(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, "r") as file:
        tree = ast.parse(file.read(), filename=file_path)

    upgrade_has_pass = False
    downgrade_has_pass = False

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if node.name == "upgrade":
                for stmt in node.body:
                    if isinstance(stmt, ast.Pass):
                        upgrade_has_pass = True
            elif node.name == "downgrade":
                for stmt in node.body:
                    if isinstance(stmt, ast.Pass):
                        downgrade_has_pass = True

    print(f"Upgrade function {'contains' if upgrade_has_pass else 'does not contain'} 'pass'.")
    print(f"Downgrade function {'contains' if downgrade_has_pass else 'does not contain'} 'pass'.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_alembic_file_for_pass.py <path_to_alembic_file>")
    else:
        check_alembic_file_for_pass(sys.argv[1])
