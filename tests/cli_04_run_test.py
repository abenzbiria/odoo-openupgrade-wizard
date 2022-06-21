from pathlib import Path

from odoo_openupgrade_wizard.tools_docker import get_docker_client
from odoo_openupgrade_wizard.tools_postgres import execute_sql_request

from . import (
    build_ctx_from_config_file,
    cli_runner_invoke,
    move_to_test_folder,
)


def test_cli_run():
    move_to_test_folder()
    db_name = "database_test_cli___run"
    cli_runner_invoke(
        [
            "--log-level=DEBUG",
            "run",
            "--step=1",
            "--database=%s" % db_name,
            "--init-modules=base",
            "--stop-after-init",
        ]
    )

    # Ensure that a subfolder filestore/DB_NAME has been created
    db_filestore_path = Path("./filestore/filestore/%s" % db_name)
    assert db_filestore_path.exists()

    # Ensure that 'base' module is installed
    ctx = build_ctx_from_config_file()
    request = (
        "SELECT id"
        " FROM ir_module_module"
        " WHERE state ='installed'"
        " AND name='base';"
    )
    assert execute_sql_request(ctx, request, database=db_name)

    # Ensure that 'point_of_sale' module is not installed
    request = (
        "SELECT id"
        " FROM ir_module_module"
        " WHERE state ='installed'"
        " AND name='point_of_sale';"
    )
    assert not execute_sql_request(ctx, request, database=db_name)

    # Ensure that all the containers are removed
    docker_client = get_docker_client()
    assert not docker_client.containers.list(
        all=True, filters={"name": "odoo-openupgrade-wizard"}
    )