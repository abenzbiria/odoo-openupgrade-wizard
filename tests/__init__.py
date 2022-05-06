import logging
from pathlib import Path

import yaml
from click.testing import CliRunner

from odoo_openupgrade_wizard.cli import main

_logger = logging.getLogger()


def assert_result_cli_invoke(result):
    pass


def cli_runner_invoke(cmd):
    result = CliRunner().invoke(
        main,
        cmd,
        catch_exceptions=False,
    )
    if not result.exit_code == 0:
        _logger.error("exit_code: %s" % result.exit_code)
        _logger.error("output: %s" % result.output)
    assert result.exit_code == 0


def build_ctx_from_config_file(env_folder_path) -> dict:
    class context:
        pass

    ctx = context()
    setattr(ctx, "obj", {})
    config_file_path = env_folder_path / "config.yml"
    if not config_file_path.exists():
        raise Exception("Configuration file not found %s" % config_file_path)
    with open(config_file_path) as file:
        config = yaml.safe_load(file)
        ctx.obj["config"] = config
        file.close()

    ctx.obj["env_folder_path"] = env_folder_path
    ctx.obj["src_folder_path"] = env_folder_path / Path("src")
    ctx.obj["postgres_folder_path"] = env_folder_path / Path(
        "postgres_data/data"
    )
    return ctx
