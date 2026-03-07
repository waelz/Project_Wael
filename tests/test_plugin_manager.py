"""Tests pour plugin_manager.py"""

import pytest
from framework.plugin_manager import PluginManager
from framework.config_loader import load_config


def make_handler(label: str):
    """Crée un handler de test qui retourne ses options avec un label."""
    def handler(options: dict):
        return {"label": label, **options}
    return handler


class TestPluginManager:
    def setup_method(self):
        self.pm = PluginManager()

    def test_register_and_get(self):
        self.pm.register("auth", make_handler("auth"))
        config = {
            "plugins": [{"name": "auth", "enabled": True, "options": {"key": "abc"}}]
        }
        self.pm.load_from_config(config)
        plugin = self.pm.get("auth")
        assert plugin["label"] == "auth"
        assert plugin["key"] == "abc"

    def test_disabled_plugin_not_loaded(self):
        self.pm.register("cache", make_handler("cache"))
        config = {
            "plugins": [{"name": "cache", "enabled": False, "options": {}}]
        }
        self.pm.load_from_config(config)
        assert self.pm.get("cache") is None

    def test_unregistered_plugin_not_loaded(self):
        config = {
            "plugins": [{"name": "unknown", "enabled": True, "options": {}}]
        }
        self.pm.load_from_config(config)
        assert self.pm.get("unknown") is None

    def test_list_active_plugins(self):
        self.pm.register("auth", make_handler("auth"))
        self.pm.register("cache", make_handler("cache"))
        config = {
            "plugins": [
                {"name": "auth", "enabled": True, "options": {}},
                {"name": "cache", "enabled": False, "options": {}},
            ]
        }
        self.pm.load_from_config(config)
        assert self.pm.list_active() == ["auth"]

    def test_is_active(self):
        self.pm.register("cors", make_handler("cors"))
        config = {
            "plugins": [{"name": "cors", "enabled": True, "options": {}}]
        }
        self.pm.load_from_config(config)
        assert self.pm.is_active("cors") is True
        assert self.pm.is_active("auth") is False

    def test_get_nonexistent_returns_none(self):
        assert self.pm.get("nope") is None

    def test_load_from_real_dev_config(self):
        config = load_config(env="dev")
        self.pm.register("auth", make_handler("auth"))
        self.pm.register("cache", make_handler("cache"))
        self.pm.load_from_config(config)
        assert self.pm.is_active("auth") is True
