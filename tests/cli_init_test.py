import filecmp
from pathlib import Path

from click.testing import CliRunner
from plumbum.cmd import mkdir

from odoo_openupgrade_wizard.cli import main


def test_cli_init():
    output_folder_path = Path("./tests/output")
    expected_folder_path = Path("./tests/output_expected")
    mkdir([output_folder_path, "--parents"])
    result = CliRunner().invoke(
        main,
        [
            "--env-folder=%s" % output_folder_path,
            "init",
            "--initial-version=9.0",
            "--final-version=12.0",
            "--extra-repository="
            "OCA/web,OCA/server-tools,GRAP/grap-odoo-incubator",
        ],
    )
    assert result.exit_code == 0

    assert filecmp.cmp(
        output_folder_path / Path("config.yml"),
        expected_folder_path / Path("config.yml"),
    )
