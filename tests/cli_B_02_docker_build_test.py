from pathlib import Path

import docker
from click.testing import CliRunner

from odoo_openupgrade_wizard.cli import main


def test_cli_docker_build():
    output_folder_path = Path("./tests/output_B")

    result = CliRunner().invoke(
        main,
        [
            "--env-folder=%s" % output_folder_path,
            "docker-build",
            "--releases=14.0",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0

    # TODO, add test to see if image exists
    docker_client = docker.from_env()

    assert docker_client.images.get(
        "odoo-openupgrade-wizard-image-test-cli-14.0"
    )
