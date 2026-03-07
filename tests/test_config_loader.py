"""Tests pour config_loader.py"""

import pytest
from framework.config_loader import load_config, deep_merge, load_yaml


class TestDeepMerge:
    def test_merge_simple_values(self):
        base = {"a": 1, "b": 2}
        override = {"b": 99, "c": 3}
        result = deep_merge(base, override)
        assert result == {"a": 1, "b": 99, "c": 3}

    def test_merge_nested_dicts(self):
        base = {"framework": {"debug": False, "log_level": "INFO"}}
        override = {"framework": {"debug": True}}
        result = deep_merge(base, override)
        assert result["framework"]["debug"] is True
        assert result["framework"]["log_level"] == "INFO"

    def test_lists_are_replaced(self):
        base = {"plugins": ["auth", "cache"]}
        override = {"plugins": ["cors"]}
        result = deep_merge(base, override)
        assert result["plugins"] == ["cors"]

    def test_base_not_mutated(self):
        base = {"a": {"x": 1}}
        override = {"a": {"x": 99}}
        deep_merge(base, override)
        assert base["a"]["x"] == 1


class TestLoadConfig:
    def test_load_dev_config(self):
        config = load_config(env="dev")
        assert config["framework"]["debug"] is True
        assert config["framework"]["log_level"] == "DEBUG"
        assert config["_env"] == "dev"

    def test_load_prod_config(self):
        config = load_config(env="prod")
        assert config["framework"]["debug"] is False
        assert config["_env"] == "prod"

    def test_dev_overrides_base_secret_key(self):
        config = load_config(env="dev")
        auth_plugin = next(
            (p for p in config["plugins"] if p["name"] == "auth"), None
        )
        assert auth_plugin is not None
        assert auth_plugin["options"]["secret_key"] == "dev-secret-key"

    def test_base_services_present(self):
        config = load_config(env="dev")
        assert "database" in config["services"]
        assert "api" in config["services"]

    def test_unknown_env_uses_base_only(self):
        config = load_config(env="staging")
        assert config["framework"]["name"] == "MyFramework"
        assert config["_env"] == "staging"

    def test_missing_base_config_raises(self, tmp_path, monkeypatch):
        import framework.config_loader as cl
        monkeypatch.setattr(cl, "CONFIG_DIR", tmp_path)
        with pytest.raises(FileNotFoundError):
            load_config(env="dev")
