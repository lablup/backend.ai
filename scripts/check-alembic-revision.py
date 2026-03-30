import sys
import os
import ast


def check_alembic_file_for_pass(file_path):
    if not os.path.isfile(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, "r") as file:
        tree = ast.parse(file.read(), filename=file_path)

    upgrade_is_empty = True
    downgrade_is_empty = True

    for node in ast.walk(tree):
      if isinstance(node, ast.FunctionDef):
          if node.name == "upgrade":
              upgrade_is_empty = all(isinstance(stmt, ast.Pass) for stmt in node.body)
          elif node.name == "downgrade":
              downgrade_is_empty = all(isinstance(stmt, ast.Pass) for stmt in node.body)

    print(f"Upgrade function {'is empty' if upgrade_is_empty else 'is not empty'}.")
    print(f"Downgrade function {'is empty' if downgrade_is_empty else 'is not empty'}.")

    if upgrade_is_empty and downgrade_is_empty:
        return 0
    else:
        return 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_alembic_file_for_pass.py <path_to_alembic_file>")
        sys.exit(1)
    else:
        exit_code = check_alembic_file_for_pass(sys.argv[1])
        sys.exit(exit_code)
