"""Tests for cli.py"""

import json
import sys

import pytest
import yaml

from framework.cli import build_parser, cmd_export, cmd_show, cmd_validate


def make_args(**kwargs):
    """Build a namespace simulating parsed CLI args."""
    defaults = {"env": "dev", "with_env": False}
    defaults.update(kwargs)
    return type("Namespace", (), defaults)()


class TestCmdValidate:
    def test_valid_dev_config(self, capsys):
        args = make_args(env="dev")
        code = cmd_validate(args)
        assert code == 0
        out = capsys.readouterr().out
        assert "valid" in out

    def test_valid_prod_config(self, capsys):
        args = make_args(env="prod")
        code = cmd_validate(args)
        assert code == 0

    def test_unknown_env_still_valid(self, capsys):
        # 'staging' falls back to base config, which is valid
        args = make_args(env="staging")
        code = cmd_validate(args)
        assert code == 0

    def test_missing_base_config_returns_1(self, monkeypatch, tmp_path, capsys):
        import framework.config_loader as cl
        monkeypatch.setattr(cl, "CONFIG_DIR", tmp_path)
        args = make_args(env="dev")
        code = cmd_validate(args)
        assert code == 1
        assert "Error" in capsys.readouterr().err

    def test_with_env_override(self, monkeypatch, capsys):
        monkeypatch.setenv("FRAMEWORK__FRAMEWORK__LOG_LEVEL", "DEBUG")
        args = make_args(env="dev", with_env=True)
        code = cmd_validate(args)
        assert code == 0


class TestCmdShow:
    def test_show_yaml_format(self, capsys):
        args = make_args(env="dev", format="yaml")
        code = cmd_show(args)
        assert code == 0
        out = capsys.readouterr().out
        parsed = yaml.safe_load(out)
        assert parsed["framework"]["name"] == "MyFramework"

    def test_show_json_format(self, capsys):
        args = make_args(env="dev", format="json")
        code = cmd_show(args)
        assert code == 0
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert parsed["_env"] == "dev"

    def test_show_prod_config(self, capsys):
        args = make_args(env="prod", format="json")
        code = cmd_show(args)
        assert code == 0
        parsed = json.loads(capsys.readouterr().out)
        assert parsed["_env"] == "prod"

    def test_show_with_env_override(self, monkeypatch, capsys):
        monkeypatch.setenv("FRAMEWORK__SERVICES__DATABASE__HOST", "override-host")
        args = make_args(env="dev", format="json", with_env=True)
        code = cmd_show(args)
        assert code == 0
        parsed = json.loads(capsys.readouterr().out)
        assert parsed["services"]["database"]["host"] == "override-host"

    def test_missing_config_returns_1(self, monkeypatch, tmp_path, capsys):
        import framework.config_loader as cl
        monkeypatch.setattr(cl, "CONFIG_DIR", tmp_path)
        args = make_args(env="dev", format="yaml")
        code = cmd_show(args)
        assert code == 1


class TestCmdExport:
    def test_export_contains_key_value_pairs(self, capsys):
        args = make_args(env="dev", prefix="")
        code = cmd_export(args)
        assert code == 0
        out = capsys.readouterr().out
        assert "export " in out
        assert "=" in out

    def test_export_with_prefix(self, capsys):
        args = make_args(env="dev", prefix="APP_")
        code = cmd_export(args)
        assert code == 0
        out = capsys.readouterr().out
        lines = [l for l in out.splitlines() if l.startswith("export ")]
        assert all("APP_" in l for l in lines)

    def test_export_env_key_not_present(self, capsys):
        """The internal _env metadata key must not appear in export output."""
        args = make_args(env="dev", prefix="")
        cmd_export(args)
        out = capsys.readouterr().out
        assert "_ENV=" not in out

    def test_export_missing_config_returns_1(self, monkeypatch, tmp_path, capsys):
        import framework.config_loader as cl
        monkeypatch.setattr(cl, "CONFIG_DIR", tmp_path)
        args = make_args(env="dev", prefix="")
        code = cmd_export(args)
        assert code == 1


class TestBuildParser:
    def test_validate_command(self):
        parser = build_parser()
        args = parser.parse_args(["validate", "--env", "prod"])
        assert args.command == "validate"
        assert args.env == "prod"

    def test_show_default_format(self):
        parser = build_parser()
        args = parser.parse_args(["show"])
        assert args.format == "yaml"
        assert args.env == "dev"

    def test_show_json_format(self):
        parser = build_parser()
        args = parser.parse_args(["show", "--format", "json", "--env", "prod"])
        assert args.format == "json"
        assert args.env == "prod"

    def test_export_prefix(self):
        parser = build_parser()
        args = parser.parse_args(["export", "--prefix", "MY_"])
        assert args.prefix == "MY_"

    def test_with_env_flag(self):
        parser = build_parser()
        args = parser.parse_args(["validate", "--with-env"])
        assert args.with_env is True

    def test_no_command_exits(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])
