from pathlib import Path

from plumbum.cmd import cp

from odoo_openupgrade_wizard.tools.tools_postgres import (
    ensure_database,
    execute_sql_request,
)

from . import (
    build_ctx_from_config_file,
    cli_runner_invoke,
    move_to_test_folder,
)


def test_cli_execute_script_sql():
    move_to_test_folder()
    ctx = build_ctx_from_config_file()

    extra_script_path = Path(
        "../extra_script/pre-migration-custom_test.sql"
    ).absolute()

    # Deploy SQL Script
    destination_path = Path("scripts/step_01__update__14.0")
    cp([extra_script_path, destination_path])

    # Reset database
    db_name = "database_test_cli___execute_script_sql"
    ensure_database(ctx, db_name, state="absent")
    ensure_database(ctx, db_name, state="present")

    # TODO call with script-file-path
    # to avoid to copy file in scripts/step_xxx folder
    cli_runner_invoke(
        ctx,
        [
            "--log-level=DEBUG",
            "execute-script-sql",
            "--step=1",
            "--database=%s" % db_name,
        ],
    )

    # Ensure that the request has been done correctly
    request = "SELECT name from city order by id;"
    result = execute_sql_request(ctx, request, database=db_name)

    assert result == [["Chicago"], ["Cavalaire Sur Mer"]]
