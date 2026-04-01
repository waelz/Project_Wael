"""Tests for env_override.py"""

import pytest
from framework.env_override import apply_env_overrides, list_active_overrides


BASE_CONFIG = {
    "framework": {
        "name": "MyFramework",
        "version": "1.0.0",
        "debug": False,
        "log_level": "INFO",
    },
    "services": {
        "database": {
            "host": "localhost",
            "port": 5432,
            "pool_size": 5,
        },
        "api": {
            "host": "0.0.0.0",
            "port": 8000,
            "workers": 4,
        },
    },
    "_env": "dev",
}


class TestApplyEnvOverrides:
    def test_no_env_vars_returns_deep_copy(self, monkeypatch):
        monkeypatch.delenv("FRAMEWORK__FRAMEWORK__DEBUG", raising=False)
        result = apply_env_overrides(BASE_CONFIG)
        assert result == BASE_CONFIG
        assert result is not BASE_CONFIG

    def test_override_string_value(self, monkeypatch):
        monkeypatch.setenv("FRAMEWORK__SERVICES__DATABASE__HOST", "prod-db.example.com")
        result = apply_env_overrides(BASE_CONFIG)
        assert result["services"]["database"]["host"] == "prod-db.example.com"

    def test_override_does_not_mutate_original(self, monkeypatch):
        monkeypatch.setenv("FRAMEWORK__SERVICES__DATABASE__HOST", "other-host")
        apply_env_overrides(BASE_CONFIG)
        assert BASE_CONFIG["services"]["database"]["host"] == "localhost"

    def test_coerce_bool_true(self, monkeypatch):
        for val in ("true", "True", "TRUE", "yes", "YES", "1"):
            monkeypatch.setenv("FRAMEWORK__FRAMEWORK__DEBUG", val)
            result = apply_env_overrides(BASE_CONFIG)
            assert result["framework"]["debug"] is True, f"Failed for value: {val}"

    def test_coerce_bool_false(self, monkeypatch):
        for val in ("false", "False", "FALSE", "no", "NO", "0"):
            monkeypatch.setenv("FRAMEWORK__FRAMEWORK__DEBUG", val)
            result = apply_env_overrides(BASE_CONFIG)
            assert result["framework"]["debug"] is False, f"Failed for value: {val}"

    def test_coerce_int(self, monkeypatch):
        monkeypatch.setenv("FRAMEWORK__SERVICES__API__WORKERS", "16")
        result = apply_env_overrides(BASE_CONFIG)
        assert result["services"]["api"]["workers"] == 16
        assert isinstance(result["services"]["api"]["workers"], int)

    def test_coerce_float(self, monkeypatch):
        monkeypatch.setenv("FRAMEWORK__SOME__THRESHOLD", "0.95")
        result = apply_env_overrides(BASE_CONFIG)
        assert result["some"]["threshold"] == pytest.approx(0.95)

    def test_string_not_coerced_to_number(self, monkeypatch):
        monkeypatch.setenv("FRAMEWORK__SERVICES__DATABASE__HOST", "db-01")
        result = apply_env_overrides(BASE_CONFIG)
        assert result["services"]["database"]["host"] == "db-01"

    def test_creates_missing_nested_keys(self, monkeypatch):
        monkeypatch.setenv("FRAMEWORK__NEW__SECTION__KEY", "value")
        result = apply_env_overrides(BASE_CONFIG)
        assert result["new"]["section"]["key"] == "value"

    def test_non_matching_prefix_ignored(self, monkeypatch):
        monkeypatch.setenv("OTHER__SERVICES__DATABASE__HOST", "should-be-ignored")
        result = apply_env_overrides(BASE_CONFIG)
        assert result["services"]["database"]["host"] == "localhost"

    def test_custom_prefix(self, monkeypatch):
        monkeypatch.setenv("MYAPP__FRAMEWORK__LOG_LEVEL", "ERROR")
        result = apply_env_overrides(BASE_CONFIG, prefix="MYAPP__")
        assert result["framework"]["log_level"] == "ERROR"

    def test_multiple_overrides(self, monkeypatch):
        monkeypatch.setenv("FRAMEWORK__FRAMEWORK__LOG_LEVEL", "WARNING")
        monkeypatch.setenv("FRAMEWORK__SERVICES__DATABASE__PORT", "5433")
        monkeypatch.setenv("FRAMEWORK__SERVICES__API__WORKERS", "8")
        result = apply_env_overrides(BASE_CONFIG)
        assert result["framework"]["log_level"] == "WARNING"
        assert result["services"]["database"]["port"] == 5433
        assert result["services"]["api"]["workers"] == 8

    def test_underscore_key_preserved(self, monkeypatch):
        """pool_size contains an underscore — must survive round-trip via env."""
        monkeypatch.setenv("FRAMEWORK__SERVICES__DATABASE__POOL_SIZE", "20")
        result = apply_env_overrides(BASE_CONFIG)
        assert result["services"]["database"]["pool_size"] == 20


class TestListActiveOverrides:
    def test_empty_when_no_vars(self, monkeypatch):
        # Clear any matching vars that might exist
        for key in list(
            k for k in __import__("os").environ if k.startswith("FRAMEWORK__")
        ):
            monkeypatch.delenv(key)
        overrides = list_active_overrides()
        assert overrides == []

    def test_returns_matching_vars(self, monkeypatch):
        monkeypatch.setenv("FRAMEWORK__FRAMEWORK__DEBUG", "true")
        monkeypatch.setenv("FRAMEWORK__SERVICES__DATABASE__HOST", "myhost")
        overrides = list_active_overrides()
        keys = [k for k, _ in overrides]
        assert "FRAMEWORK__FRAMEWORK__DEBUG" in keys
        assert "FRAMEWORK__SERVICES__DATABASE__HOST" in keys

    def test_sorted_output(self, monkeypatch):
        monkeypatch.setenv("FRAMEWORK__Z_KEY", "z")
        monkeypatch.setenv("FRAMEWORK__A_KEY", "a")
        overrides = list_active_overrides()
        keys = [k for k, _ in overrides if k in ("FRAMEWORK__Z_KEY", "FRAMEWORK__A_KEY")]
        assert keys == sorted(keys)
