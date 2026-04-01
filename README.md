# Framework Config Manager

A Python library for managing multi-environment YAML configurations with built-in validation, a plugin lifecycle system, environment variable overrides, and a CLI.

---

## Features

| Feature | Description |
| --- | --- |
| **Multi-environment configs** | Base YAML + per-environment overrides (`dev`, `prod`, …) |
| **Deep merge** | Nested dicts merged recursively; lists replaced entirely |
| **Validation** | Structural checks with clear error messages |
| **Plugin manager** | Register and activate plugins from configuration |
| **Env var overrides** | Override any config value via `FRAMEWORK__` environment variables |
| **CLI** | `validate`, `show`, and `export` commands |

---

## Installation

```bash
pip install -r requirements.txt
```

**Requirements:** Python 3.12+, PyYAML, pytest, pytest-html

---

## Quick Start

```python
from framework import load_config, validate_config, apply_env_overrides, PluginManager

# Load config for an environment
config = load_config(env="prod")

# Optionally apply environment variable overrides on top
config = apply_env_overrides(config)

# Validate
errors = validate_config(config)
if errors:
    for err in errors:
        print(f"  Error: {err}")

# Use the plugin system
pm = PluginManager()
pm.register("auth", lambda opts: {"token_expiry": opts.get("token_expiry", 3600)})
pm.load_from_config(config)

auth = pm.get("auth")
print(pm.list_active())
```

---

## Configuration

Configs live in `config/`:

```
config/
  framework.yaml   ← base (always loaded)
  dev.yaml         ← overrides for dev
  prod.yaml        ← overrides for prod
```

Example `config/framework.yaml`:

```yaml
framework:
  name: MyFramework
  version: "1.0.0"
  debug: false
  log_level: INFO

plugins:
  - name: auth
    enabled: true
    options:
      secret_key: change-me
      token_expiry: 3600

services:
  database:
    host: localhost
    port: 5432
    name: mydb
    pool_size: 5
  api:
    host: 0.0.0.0
    port: 8000
    workers: 4
```

Environment-specific files only need to include the keys that differ:

```yaml
# config/dev.yaml
framework:
  debug: true
  log_level: DEBUG

services:
  api:
    workers: 1
```

---

## Environment Variable Overrides

Override any config value at runtime using environment variables. This follows the [12-factor app](https://12factor.net/config) methodology.

**Format:** `FRAMEWORK__<SECTION>__<KEY>=<value>`

- Prefix: `FRAMEWORK__` (double underscore)
- Hierarchy separator: `__` (double underscore)
- Single underscores in key names are preserved

```bash
# Override database host
export FRAMEWORK__SERVICES__DATABASE__HOST=prod-db.example.com

# Toggle debug mode
export FRAMEWORK__FRAMEWORK__DEBUG=false

# Set worker count
export FRAMEWORK__SERVICES__API__WORKERS=8
```

**Type coercion** happens automatically:

| Env value | Python type |
| --- | --- |
| `true`, `yes`, `1` | `True` (bool) |
| `false`, `no`, `0` | `False` (bool) |
| `"42"` | `42` (int) |
| `"3.14"` | `3.14` (float) |
| anything else | str |

Apply overrides in code:

```python
from framework import load_config, apply_env_overrides

config = load_config(env="prod")
config = apply_env_overrides(config)   # reads os.environ
```

---

## CLI

```bash
# Validate a config (exit code 0 = valid, 1 = errors)
python -m framework.cli validate --env dev
python -m framework.cli validate --env prod --with-env

# Print merged config
python -m framework.cli show --env dev
python -m framework.cli show --env prod --format json

# Export as shell variable assignments
python -m framework.cli export --env prod
python -m framework.cli export --env prod --prefix APP_
eval $(python -m framework.cli export --env prod --prefix APP_)
```

---

## Validation Rules

`validate_config(config)` checks:

- Required sections: `framework`, `services.database`, `services.api`
- Required fields per section (e.g. `name`, `version`, `debug`, `log_level`)
- `log_level` must be one of: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- Ports must be positive integers
- `workers` must be an integer ≥ 1
- Each plugin must have `name` and `enabled` fields

Returns a list of error strings — empty means valid.

---

## Plugin System

```python
from framework import PluginManager, load_config

pm = PluginManager()

# Register handlers before loading config
pm.register("auth", lambda opts: MyAuthPlugin(secret=opts["secret_key"]))
pm.register("cache", lambda opts: MyCachePlugin(backend=opts.get("backend", "memory")))

config = load_config(env="prod")
pm.load_from_config(config)   # activates plugins with enabled: true

auth_plugin = pm.get("auth")
print(pm.list_active())       # ["auth", "cache"]
print(pm.is_active("cors"))   # False
```

Plugins without a registered handler are silently skipped.

---

## Testing

```bash
# Run all tests
pytest

# Verbose output
pytest -v

# Single module
pytest tests/test_env_override.py -v

# Generate HTML report
pytest --html=report.html --self-contained-html
```

---

## Project Structure

```text
framework/
  __init__.py          Public API
  config_loader.py     YAML loading & deep merge
  validator.py         Configuration validation
  plugin_manager.py    Plugin registry & lifecycle
  env_override.py      Environment variable overrides
  cli.py               Command-line interface

config/
  framework.yaml       Base configuration
  dev.yaml             Development overrides
  prod.yaml            Production overrides

tests/
  test_config_loader.py
  test_validator.py
  test_plugin_manager.py
  test_env_override.py
  test_cli.py

scripts/
  check_yaml.py        YAML syntax validation (CI)
  check_python.py      Python syntax validation (CI)
```

---

## CI/CD

GitHub Actions pipeline (`.github/workflows/ci.yml`):

1. **pre-check** — validates YAML and Python syntax
2. **test** — runs pytest, saves JUnit XML artifact
3. **report** — generates HTML test report artifact

Triggers on push and pull requests to `main`.

---

## License

MIT
