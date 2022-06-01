from odoo_openupgrade_wizard.tools_docker import get_docker_client

from . import cli_runner_invoke, move_to_test_folder


def test_cli_docker_build():
    move_to_test_folder()
    cli_runner_invoke(
        [
            "--log-level=DEBUG",
            "docker-build",
            "--releases=13.0,14.0",
        ]
    )

    docker_client = get_docker_client()

    assert docker_client.images.get(
        "odoo-openupgrade-wizard-image__test-cli__13.0"
    )

    assert docker_client.images.get(
        "odoo-openupgrade-wizard-image__test-cli__14.0"
    )
