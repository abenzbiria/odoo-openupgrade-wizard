from pathlib import Path

from odoo_openupgrade_wizard.tools_docker import get_docker_client

from . import cli_runner_invoke


def test_cli_run():
    output_folder_path = Path("./tests/output_B")

    db_name = "database_test_cli_run__step_1"
    cli_runner_invoke(
        [
            "--env-folder=%s" % output_folder_path,
            "run",
            "--step=1",
            "--database=%s" % db_name,
            "--init-modules=base",
            "--stop-after-init",
        ]
    )

    # Ensure that a subfolder filestore/DB_NAME has been created
    db_filestore_path = output_folder_path / Path(
        "./filestore/filestore/%s" % db_name
    )
    assert db_filestore_path.exists()

    # Ensure that all the containers are removed
    docker_client = get_docker_client()
    assert not docker_client.containers.list(
        all=True, filters={"name": "odoo-openupgrade-wizard"}
    )
