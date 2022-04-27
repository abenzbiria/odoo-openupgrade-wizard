from pathlib import Path

from odoo_openupgrade_wizard.tools_docker import get_docker_client

from . import cli_runner_invoke


def test_cli_docker_build():
    output_folder_path = Path("./tests/output_B")

    cli_runner_invoke(
        [
            "--env-folder=%s" % output_folder_path,
            "docker-build",
            "--releases=14.0",
        ]
    )

    docker_client = get_docker_client()

    assert docker_client.images.get(
        "odoo-openupgrade-wizard-image__test-cli__14.0"
    )
