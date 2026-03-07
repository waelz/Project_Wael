"""
config_loader.py — Charge et fusionne les configurations YAML par environnement.

Usage:
    config = load_config(env="dev")
    config = load_config(env="prod")
"""

import os
import yaml
from pathlib import Path

CONFIG_DIR = Path(__file__).parent.parent / "config"


def load_yaml(path: Path) -> dict:
    """Charge un fichier YAML et retourne un dictionnaire."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def deep_merge(base: dict, override: dict) -> dict:
    """
    Fusionne récursivement `override` dans `base`.
    Les valeurs de `override` écrasent celles de `base`.
    Les listes sont remplacées entièrement (pas concaténées).
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(env: str = "dev") -> dict:
    """
    Charge la configuration de base (framework.yaml) puis applique
    les overrides de l'environnement spécifié (dev.yaml / prod.yaml).

    Args:
        env: Nom de l'environnement ("dev", "prod", etc.)

    Returns:
        Dictionnaire de configuration fusionné.

    Raises:
        FileNotFoundError: Si framework.yaml ou le fichier d'env est introuvable.
    """
    base_path = CONFIG_DIR / "framework.yaml"
    env_path = CONFIG_DIR / f"{env}.yaml"

    if not base_path.exists():
        raise FileNotFoundError(f"Config de base introuvable : {base_path}")

    config = load_yaml(base_path)

    if env_path.exists():
        env_config = load_yaml(env_path)
        config = deep_merge(config, env_config)

    config["_env"] = env
    return config
