from pathlib import Path

import docker
from click.testing import CliRunner

from odoo_openupgrade_wizard.cli import main


def test_cli_run():
    output_folder_path = Path("./tests/output_B")

    result = CliRunner().invoke(
        main,
        [
            "--env-folder=%s" % output_folder_path,
            "run",
            "--step=1",
            "--duration=2",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0

    # Ensure that all the containers are removed
    docker_client = docker.from_env()
    assert not docker_client.containers.list(
        all=True, filters={"name": "odoo-openupgrade-wizard"}
    )
