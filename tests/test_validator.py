"""Tests pour validator.py"""

import pytest
from framework.validator import validate_config
from framework.config_loader import load_config


def minimal_config() -> dict:
    return {
        "framework": {
            "name": "TestFW",
            "version": "1.0.0",
            "debug": False,
            "log_level": "INFO",
        },
        "plugins": [],
        "services": {
            "database": {"host": "localhost", "port": 5432, "name": "testdb"},
            "api": {"host": "0.0.0.0", "port": 8000, "workers": 2},
        },
    }


class TestValidateConfig:
    def test_valid_config_has_no_errors(self):
        errors = validate_config(minimal_config())
        assert errors == []

    def test_missing_framework_section(self):
        config = minimal_config()
        del config["framework"]
        errors = validate_config(config)
        assert any("framework" in e for e in errors)

    def test_missing_required_field(self):
        config = minimal_config()
        del config["framework"]["version"]
        errors = validate_config(config)
        assert any("framework.version" in e for e in errors)

    def test_invalid_log_level(self):
        config = minimal_config()
        config["framework"]["log_level"] = "VERBOSE"
        errors = validate_config(config)
        assert any("log_level" in e for e in errors)

    def test_invalid_port_string(self):
        config = minimal_config()
        config["services"]["api"]["port"] = "not-a-port"
        errors = validate_config(config)
        assert any("services.api.port" in e for e in errors)

    def test_invalid_workers_zero(self):
        config = minimal_config()
        config["services"]["api"]["workers"] = 0
        errors = validate_config(config)
        assert any("workers" in e for e in errors)

    def test_plugin_missing_name(self):
        config = minimal_config()
        config["plugins"] = [{"enabled": True}]
        errors = validate_config(config)
        assert any("name" in e for e in errors)

    def test_plugin_missing_enabled(self):
        config = minimal_config()
        config["plugins"] = [{"name": "auth"}]
        errors = validate_config(config)
        assert any("enabled" in e for e in errors)

    def test_real_dev_config_is_valid(self):
        config = load_config(env="dev")
        errors = validate_config(config)
        assert errors == []

    def test_real_prod_config_is_valid(self):
        config = load_config(env="prod")
        errors = validate_config(config)
        assert errors == []
