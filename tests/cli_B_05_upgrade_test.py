from pathlib import Path

from odoo_openupgrade_wizard.tools_postgres import (
    ensure_database,
    execute_sql_request,
)

from . import cli_runner_invoke


def test_cli_upgrade():
    output_folder_path = Path("./tests/output_B").absolute()

    db_name = "database_test_cli_upgrade"

    ensure_database(db_name, state="absent")

    cli_runner_invoke(
        [
            "--log-level=DEBUG",
            "--env-folder=%s" % output_folder_path,
            "run",
            "--step=1",
            "--database=%s" % db_name,
            "--init-modules=base",
            "--stop-after-init",
        ]
    )

    # Ensure that 'base' module is installed at 13.0
    request = (
        "SELECT latest_version"
        " FROM ir_module_module"
        " WHERE state ='installed'"
        " AND name='base';"
    )
    latest_version = execute_sql_request(request, database=db_name)

    assert latest_version[0][0].startswith("13.")

    cli_runner_invoke(
        [
            "--log-level=DEBUG",
            "--env-folder=%s" % output_folder_path,
            "upgrade",
            "--database=%s" % db_name,
            "--first-step=1",
            "--last-step=3",
        ]
    )

    # Ensure that 'base' module is installed at 14.0
    request = (
        "SELECT latest_version"
        " FROM ir_module_module"
        " WHERE state ='installed'"
        " AND name='base';"
    )
    latest_version = execute_sql_request(request, database=db_name)

    assert latest_version[0][0].startswith("14.")
