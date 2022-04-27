import logging

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
