"""
env_override.py — Apply environment variable overrides to a loaded configuration.

Uses double-underscore (__) as the hierarchy separator to safely handle
config keys that contain single underscores (e.g. pool_size, log_level).

Environment variable format:
    FRAMEWORK__<SECTION>__<KEY> = <value>

Examples:
    FRAMEWORK__SERVICES__DATABASE__HOST=prod-db.example.com
    FRAMEWORK__FRAMEWORK__LOG_LEVEL=WARNING
    FRAMEWORK__SERVICES__API__WORKERS=8
    FRAMEWORK__FRAMEWORK__DEBUG=false

Usage:
    from framework.env_override import apply_env_overrides
    config = load_config(env="prod")
    config = apply_env_overrides(config)
"""

import copy
import os
from typing import Any

ENV_PREFIX = "FRAMEWORK__"


def _coerce(value: str) -> Any:
    """Coerce a string env var value to bool, int, float, or keep as str."""
    if value.lower() in ("true", "yes", "1"):
        return True
    if value.lower() in ("false", "no", "0"):
        return False
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


def _set_nested(data: dict, keys: list[str], value: Any) -> None:
    """Set a value in a nested dict given a list of keys."""
    for key in keys[:-1]:
        if key not in data or not isinstance(data[key], dict):
            data[key] = {}
        data = data[key]
    data[keys[-1]] = value


def apply_env_overrides(config: dict, prefix: str = ENV_PREFIX) -> dict:
    """
    Apply environment variable overrides on top of a config dict.

    Variables must start with `prefix` (default: FRAMEWORK__).
    The remainder of the variable name is split on __ to produce
    the nested key path, which is lowercased before lookup.

    Type coercion is applied automatically:
        "true" / "false" → bool
        "42"             → int
        "3.14"           → float
        anything else    → str

    Args:
        config: Config dict (typically from load_config()).
        prefix: Environment variable prefix to match.

    Returns:
        New config dict with overrides applied (original is not mutated).
    """
    result = copy.deepcopy(config)

    for env_key, raw_value in os.environ.items():
        if not env_key.startswith(prefix):
            continue

        path_str = env_key[len(prefix):]
        keys = [segment.lower() for segment in path_str.split("__") if segment]

        if not keys:
            continue

        _set_nested(result, keys, _coerce(raw_value))

    return result


def list_active_overrides(prefix: str = ENV_PREFIX) -> list[tuple[str, str]]:
    """
    Return all environment variables that match the given prefix.

    Returns:
        List of (env_key, raw_value) tuples, sorted by key.
    """
    return sorted(
        (k, v) for k, v in os.environ.items() if k.startswith(prefix)
    )
