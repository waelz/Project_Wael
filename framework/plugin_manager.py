"""
plugin_manager.py — Gère l'enregistrement et le chargement des plugins depuis la config.

Usage:
    pm = PluginManager()
    pm.register("auth", my_auth_handler)
    pm.load_from_config(config)
    plugin = pm.get("auth")
"""

from typing import Any, Callable


class PluginManager:
    """
    Gère les plugins du framework.

    Un plugin est une fonction ou un objet enregistré sous un nom.
    La configuration YAML détermine quels plugins sont activés et
    avec quelles options ils sont initialisés.
    """

    def __init__(self):
        self._registry: dict[str, Callable] = {}
        self._active: dict[str, Any] = {}

    def register(self, name: str, handler: Callable) -> None:
        """
        Enregistre un handler pour un plugin donné.

        Args:
            name: Nom du plugin (doit correspondre au nom dans le YAML).
            handler: Callable appelé avec les options du plugin.
        """
        self._registry[name] = handler

    def load_from_config(self, config: dict) -> None:
        """
        Active les plugins listés dans la configuration.
        Seuls les plugins avec `enabled: true` ET un handler enregistré sont chargés.

        Args:
            config: Dictionnaire de configuration (issu de load_config()).
        """
        plugins = config.get("plugins", [])
        for plugin in plugins:
            name = plugin.get("name")
            enabled = plugin.get("enabled", False)
            options = plugin.get("options", {})

            if not enabled:
                continue

            if name not in self._registry:
                continue

            handler = self._registry[name]
            self._active[name] = handler(options)

    def get(self, name: str) -> Any:
        """
        Retourne l'instance active d'un plugin.

        Args:
            name: Nom du plugin.

        Returns:
            Instance du plugin ou None s'il n'est pas actif.
        """
        return self._active.get(name)

    def list_active(self) -> list[str]:
        """Retourne la liste des noms de plugins actifs."""
        return list(self._active.keys())

    def is_active(self, name: str) -> bool:
        """Vérifie si un plugin est actif."""
        return name in self._active
