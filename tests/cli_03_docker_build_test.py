from odoo_openupgrade_wizard.tools.tools_docker import (
    get_docker_client,
    kill_container,
)

from . import (
    build_ctx_from_config_file,
    cli_runner_invoke,
    move_to_test_folder,
)


def test_cli_docker_build():
    move_to_test_folder()
    ctx = build_ctx_from_config_file()

    # Drop postgresql container if exist
    #   (we ensure that the postgres container is removed to
    #   be sure that the call (environment, etc...) is correct now.)
    kill_container(ctx.obj["config"]["postgres_container_name"])

    cli_runner_invoke(
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
