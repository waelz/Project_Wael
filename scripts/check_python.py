"""
check_python.py — Vérifie la syntaxe de tous les fichiers Python du projet.
Utilisé dans le stage pre-check du pipeline CI.
"""

import sys
import ast
from pathlib import Path

ROOT = Path(__file__).parent.parent
EXCLUDE_DIRS = {".git", "__pycache__", ".pytest_cache", "venv", ".venv"}


def check_python_file(path: Path) -> list[str]:
    errors = []
    try:
        source = path.read_text(encoding="utf-8")
        ast.parse(source, filename=str(path))
        print(f"  [OK] {path.relative_to(ROOT)}")
    except SyntaxError as e:
        errors.append(
            f"  [ERREUR] {path.relative_to(ROOT)} "
            f"(ligne {e.lineno}): {e.msg}"
        )
    return errors


def collect_python_files(root: Path) -> list[Path]:
    files = []
    for path in root.rglob("*.py"):
        if not any(part in EXCLUDE_DIRS for part in path.parts):
            files.append(path)
    return sorted(files)


def main():
    print("=== Validation syntaxe Python ===")
    all_errors = []

    python_files = collect_python_files(ROOT)

    if not python_files:
        print("  Aucun fichier Python trouvé.")
        sys.exit(1)

    for py_file in python_files:
        all_errors.extend(check_python_file(py_file))

    print(f"\n{len(python_files)} fichier(s) vérifié(s).")

    if all_errors:
        print("\nErreurs détectées :")
        for err in all_errors:
            print(err)
        sys.exit(1)

    print("Tous les fichiers Python sont syntaxiquement valides.")


if __name__ == "__main__":
    main()
