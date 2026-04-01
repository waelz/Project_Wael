# AGENT.md — Framework Config Manager

This file guides AI agents (Claude Code and similar) working in this repository.

---

## Project Overview

**Framework Config Manager** is a Python library for managing multi-environment YAML configurations with validation, plugin lifecycle management, environment variable overrides, and a CLI interface.

Language: Python 3.12+  
Test runner: `pytest`  
Config format: YAML  

---

## Repository Layout

```
framework/              Core library
  config_loader.py      YAML loading + deep merge
  validator.py          Config structure validation
  plugin_manager.py     Plugin registry and lifecycle
  env_override.py       Environment variable overrides  ← NEW
  cli.py                Command-line interface          ← NEW
  __init__.py           Public API exports

config/
  framework.yaml        Base configuration
  dev.yaml              Development overrides
  prod.yaml             Production overrides

tests/                  pytest test suite
  test_config_loader.py
  test_validator.py
  test_plugin_manager.py
  test_env_override.py  ← NEW
  test_cli.py           ← NEW

scripts/
  check_yaml.py         Validates YAML syntax (used in CI)
  check_python.py       Validates Python syntax (used in CI)

.github/workflows/
  ci.yml                3-stage pipeline: pre-check → test → report
  checklist-ci.yml      PR checklist auto-comment
```

---

## Key Conventions

### Config loading
- `load_config(env)` always starts from `config/framework.yaml` as the base.
- Environment-specific files (`dev.yaml`, `prod.yaml`) are deep-merged on top.
- Unknown environments silently fall back to base config only.
- The `_env` key is injected into the returned dict as metadata — **never** validate or export it as a real config field.

### Deep merge rules
- Nested dicts are merged recursively.
- Lists are **replaced entirely**, not concatenated.
- The base dict is never mutated.

### Environment variable overrides
- Prefix: `FRAMEWORK__` (double underscore)
- Hierarchy separator: `__` (double underscore)
- Example: `FRAMEWORK__SERVICES__DATABASE__HOST=myhost`
- Single underscores within a key name are preserved: `FRAMEWORK__SERVICES__DATABASE__POOL_SIZE=20` → `services.database.pool_size`
- Values are auto-coerced: `"true"/"false"` → bool, numeric strings → int/float

### Validation
- `validate_config(config)` returns a list of error strings. Empty list = valid.
- Required sections: `framework`, `services.database`, `services.api`
- Ports must be positive integers. Workers must be int >= 1.
- Valid log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

### Plugin system
- Plugins are registered with `pm.register(name, handler)` before loading.
- Only plugins with `enabled: true` AND a registered handler are activated.
- Plugins without a registered handler are silently skipped (not an error).

---

## Running Tests

```bash
# All tests
pytest

# Single module
pytest tests/test_env_override.py -v

# With HTML report
pytest --html=report.html --self-contained-html
```

Tests use `monkeypatch` from pytest to set/unset environment variables — never `os.environ` directly in test code.

---

## CLI

```bash
# Validate
python -m framework.cli validate --env dev
python -m framework.cli validate --env prod --with-env

# Inspect
python -m framework.cli show --env dev
python -m framework.cli show --env prod --format json

# Export as shell variables
python -m framework.cli export --env prod
python -m framework.cli export --env prod --prefix APP_
```

---

## Adding a New Feature

1. Add the module under `framework/`.
2. Export from `framework/__init__.py`.
3. Add tests in `tests/test_<module>.py`.
4. If the feature uses new environment variables, document them here.
5. Run `pytest` to confirm nothing is broken.

## Editing Configurations

- Do not add required fields to `REQUIRED_FIELDS` in `validator.py` unless you also update **all three** config files (`framework.yaml`, `dev.yaml`, `prod.yaml`).
- The `dev.yaml` and `prod.yaml` files are **override-only** — they only contain keys that differ from the base.

## CI

The pipeline in `.github/workflows/ci.yml` runs on every push and PR to `main`:
1. **pre-check** — validates YAML and Python syntax
2. **test** — runs pytest, saves JUnit XML
3. **report** — generates HTML test report

Do not skip CI steps or add `continue-on-error` without a strong justification.

---

## Things to Avoid

- Do not write `os.environ["FRAMEWORK__..."] = ...` in library code — env vars are read-only inputs.
- Do not mutate the `config` dict passed to `apply_env_overrides` — always return a deep copy.
- Do not add new required config fields without updating the test fixtures that build minimal valid configs.
- Do not import `framework.cli` from library code — the CLI is a consumer of the library, not part of it.
