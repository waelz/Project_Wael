"""
cli.py — Command-line interface for the Framework Config Manager.

Commands:
    validate   Validate a configuration and report errors.
    show       Print the merged configuration (YAML or JSON).
    export     Print config as shell environment variable assignments.

Usage:
    python -m framework.cli validate --env dev
    python -m framework.cli show --env prod --format json
    python -m framework.cli show --env dev --format yaml
    python -m framework.cli export --env prod
    python -m framework.cli export --env dev --prefix APP_
"""

import argparse
import json
import sys

import yaml

from .config_loader import load_config
from .env_override import apply_env_overrides, list_active_overrides
from .validator import validate_config


def _flatten(data: dict, prefix: str = "") -> list[tuple[str, str]]:
    """Recursively flatten a nested dict into KEY=VALUE pairs."""
    items = []
    for key, value in data.items():
        full_key = f"{prefix}{key.upper()}" if prefix else key.upper()
        if isinstance(value, dict):
            items.extend(_flatten(value, f"{full_key}_"))
        else:
            items.append((full_key, str(value)))
    return items


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate the config for a given environment. Returns exit code."""
    try:
        config = load_config(env=args.env)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.with_env:
        config = apply_env_overrides(config)

    errors = validate_config(config)

    if not errors:
        print(f"Config '{args.env}' is valid.")
        return 0

    print(f"Config '{args.env}' has {len(errors)} error(s):", file=sys.stderr)
    for error in errors:
        print(f"  - {error}", file=sys.stderr)
    return 1


def cmd_show(args: argparse.Namespace) -> int:
    """Print the merged config. Returns exit code."""
    try:
        config = load_config(env=args.env)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.with_env:
        overrides = list_active_overrides()
        if overrides and args.format == "yaml":
            print(f"# Applying {len(overrides)} environment variable override(s)\n")
        config = apply_env_overrides(config)

    if args.format == "json":
        print(json.dumps(config, indent=2, default=str))
    else:
        print(yaml.dump(config, default_flow_style=False, allow_unicode=True), end="")

    return 0


def cmd_export(args: argparse.Namespace) -> int:
    """Print config as shell export statements. Returns exit code."""
    try:
        config = load_config(env=args.env)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.with_env:
        config = apply_env_overrides(config)

    # Remove internal metadata key before exporting
    config.pop("_env", None)

    pairs = _flatten(config, prefix=args.prefix)
    for key, value in sorted(pairs):
        # Escape single quotes in the value
        safe_value = value.replace("'", "'\\''")
        print(f"export {key}='{safe_value}'")

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m framework.cli",
        description="Framework Config Manager CLI",
    )
    env_arg = dict(
        metavar="ENV",
        default="dev",
        help="Environment name (default: dev)",
    )
    with_env_arg = dict(
        action="store_true",
        help="Apply FRAMEWORK__ environment variable overrides",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # validate
    p_validate = subparsers.add_parser("validate", help="Validate a configuration")
    p_validate.add_argument("--env", **env_arg)
    p_validate.add_argument("--with-env", **with_env_arg)

    # show
    p_show = subparsers.add_parser("show", help="Print the merged configuration")
    p_show.add_argument("--env", **env_arg)
    p_show.add_argument(
        "--format",
        choices=["yaml", "json"],
        default="yaml",
        help="Output format (default: yaml)",
    )
    p_show.add_argument("--with-env", **with_env_arg)

    # export
    p_export = subparsers.add_parser(
        "export", help="Print config as shell environment variables"
    )
    p_export.add_argument("--env", **env_arg)
    p_export.add_argument(
        "--prefix",
        default="",
        metavar="PREFIX",
        help="Optional prefix for variable names (e.g. APP_)",
    )
    p_export.add_argument("--with-env", **with_env_arg)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    dispatch = {
        "validate": cmd_validate,
        "show": cmd_show,
        "export": cmd_export,
    }

    handler = dispatch[args.command]
    sys.exit(handler(args))


if __name__ == "__main__":
    main()
