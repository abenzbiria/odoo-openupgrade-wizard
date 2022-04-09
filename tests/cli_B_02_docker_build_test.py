from pathlib import Path

# import docker
from click.testing import CliRunner

from odoo_openupgrade_wizard.cli import main


def test_cli_docker_build():
    return
    # TODO, FIXME
    # call docker command inside tests doesn't seems to work
    output_folder_path = Path("./tests/output_B")

    result = CliRunner().invoke(
        main,
        [
            "--env-folder=%s" % output_folder_path / "src/env_14.0",
            "docker-build",
        ],
    )
    assert result.exit_code == 0

    # TODO, add test to see if image exists
    # docker_client = docker.from_env()
