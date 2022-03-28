from pathlib import Path

from click.testing import CliRunner
from plumbum.cmd import mkdir

from odoo_openupgrade_wizard.cli import main


def test_cli_build():
    output_folder_path = Path("./tests/output")
    mkdir([output_folder_path, "--parents"])

    # We initialize an env with only one version to avoid to git clone
    # large data
    CliRunner().invoke(
        main,
        [
            "--env-folder=%s" % output_folder_path,
            "init",
            "--initial-version=14.0",
            "--final-version=14.0",
            "--extra-repository=OCA/web",
        ],
    )

    result = CliRunner().invoke(
        main,
        [
            "--env-folder=%s" % output_folder_path,
            "build",
        ],
    )
    assert result.exit_code == 0

    openupgrade_path = Path("./tests/output/src/env_14.0/src/openupgrade")

    assert openupgrade_path.exists()

    assert (openupgrade_path / Path("openupgrade_framework")).exists()
