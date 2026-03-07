"""
validator.py — Valide la structure d'une configuration de framework.

Usage:
    errors = validate_config(config)
    if errors:
        for err in errors:
            print(err)
"""

from typing import Any


REQUIRED_FIELDS = {
    "framework": ["name", "version", "debug", "log_level"],
    "services.database": ["host", "port", "name"],
    "services.api": ["host", "port", "workers"],
}

VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


def _get_nested(data: dict, path: str) -> Any:
    """Accède à une valeur imbriquée via un chemin 'a.b.c'."""
    keys = path.split(".")
    current = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def validate_config(config: dict) -> list[str]:
    """
    Valide la configuration et retourne une liste d'erreurs.
    Une liste vide signifie que la config est valide.

    Args:
        config: Dictionnaire de configuration chargé depuis YAML.

    Returns:
        Liste de messages d'erreur (vide si tout est OK).
    """
    errors = []

    # Vérification des champs requis
    for section, fields in REQUIRED_FIELDS.items():
        section_data = _get_nested(config, section)
        if section_data is None:
            errors.append(f"Section manquante : '{section}'")
            continue
        for field in fields:
            if field not in section_data:
                errors.append(f"Champ manquant : '{section}.{field}'")

    # Validation du log_level
    log_level = _get_nested(config, "framework.log_level")
    if log_level and log_level not in VALID_LOG_LEVELS:
        errors.append(
            f"log_level invalide : '{log_level}'. "
            f"Valeurs acceptées : {', '.join(VALID_LOG_LEVELS)}"
        )

    # Validation des ports (entiers positifs)
    for port_path in ["services.database.port", "services.api.port"]:
        port = _get_nested(config, port_path)
        if port is not None and (not isinstance(port, int) or port <= 0):
            errors.append(f"Port invalide pour '{port_path}' : {port}")

    # Validation des workers (entier >= 1)
    workers = _get_nested(config, "services.api.workers")
    if workers is not None and (not isinstance(workers, int) or workers < 1):
        errors.append(f"'services.api.workers' doit être un entier >= 1, reçu : {workers}")

    # Validation des plugins
    plugins = config.get("plugins", [])
    for plugin in plugins:
        if "name" not in plugin:
            errors.append("Un plugin est défini sans champ 'name'")
        if "enabled" not in plugin:
            errors.append(f"Plugin '{plugin.get('name', '?')}' manque le champ 'enabled'")

    return errors
