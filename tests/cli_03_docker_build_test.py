from odoo_openupgrade_wizard.tools.tools_docker import get_docker_client

from . import (
    build_ctx_from_config_file,
    cli_runner_invoke,
    move_to_test_folder,
)


def test_cli_docker_build():
    move_to_test_folder()
    ctx = build_ctx_from_config_file()

    cli_runner_invoke(
        ctx,
        [
            "--log-level=DEBUG",
            "docker-build",
            "--versions=14.0,15.0",
        ],
    )

    docker_client = get_docker_client()

    assert docker_client.images.get(
        "odoo-openupgrade-wizard-image__test-cli__14.0"
    )

    assert docker_client.images.get(
        "odoo-openupgrade-wizard-image__test-cli__15.0"
    )
