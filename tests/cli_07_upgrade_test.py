from odoo_openupgrade_wizard.tools.tools_postgres import (
    ensure_database,
    execute_sql_request,
)

from . import (
    build_ctx_from_config_file,
    cli_runner_invoke,
    move_to_test_folder,
)


def test_cli_upgrade():
    move_to_test_folder()

    # Initialize database
    db_name = "database_test_cli___upgrade"
    ctx = build_ctx_from_config_file()
    ensure_database(ctx, db_name, state="absent")

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

    # Ensure that 'base' module is installed at 14.0
    request = (
        "SELECT latest_version"
        " FROM ir_module_module"
        " WHERE state ='installed'"
        " AND name='base';"
    )
    latest_version = execute_sql_request(ctx, request, database=db_name)

    assert latest_version[0][0].startswith("14.")

    cli_runner_invoke(
        [
            "--log-level=DEBUG",
            "upgrade",
            "--database=%s" % db_name,
            "--first-step=1",
            "--last-step=3",
        ]
    )

    # Ensure that 'base' module is installed at 15.0
    request = (
        "SELECT latest_version"
        " FROM ir_module_module"
        " WHERE state ='installed'"
        " AND name='base';"
    )
    latest_version = execute_sql_request(ctx, request, database=db_name)

    assert latest_version[0][0].startswith("15.")
