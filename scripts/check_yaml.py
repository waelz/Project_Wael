"""
check_yaml.py — Valide la syntaxe de tous les fichiers YAML du projet.
Utilisé dans le stage pre-check du pipeline CI.
"""

import sys
import yaml
from pathlib import Path

ROOT = Path(__file__).parent.parent
YAML_DIRS = [ROOT / "config"]


def check_yaml_file(path: Path) -> list[str]:
    errors = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            yaml.safe_load(f)
        print(f"  [OK] {path.relative_to(ROOT)}")
    except yaml.YAMLError as e:
        errors.append(f"  [ERREUR] {path.relative_to(ROOT)}: {e}")
    return errors


def main():
    print("=== Validation YAML ===")
    all_errors = []

    yaml_files = []
    for directory in YAML_DIRS:
        yaml_files.extend(directory.glob("**/*.yaml"))
        yaml_files.extend(directory.glob("**/*.yml"))

    if not yaml_files:
        print("  Aucun fichier YAML trouvé.")
        sys.exit(1)

    for yaml_file in sorted(yaml_files):
        all_errors.extend(check_yaml_file(yaml_file))

    print(f"\n{len(yaml_files)} fichier(s) vérifié(s).")

    if all_errors:
        print("\nErreurs détectées :")
        for err in all_errors:
            print(err)
        sys.exit(1)

    print("Tous les fichiers YAML sont valides.")


if __name__ == "__main__":
    main()
