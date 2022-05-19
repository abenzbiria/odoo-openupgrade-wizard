import shutil
from pathlib import Path

from odoo_openupgrade_wizard.tools_postgres import (
    ensure_database,
    execute_sql_request,
)

from . import build_ctx_from_config_file, cli_runner_invoke


def test_cli_execute_script_sql():
    output_folder_path = Path("./tests/output").absolute()

    extra_script_path = Path(
        "./tests/extra_script/pre-migration-custom_test.sql"
    ).absolute()

    destination_path = output_folder_path / "scripts/step_01__update__13.0"
    shutil.copy(extra_script_path, destination_path)
    ctx = build_ctx_from_config_file(output_folder_path)
    db_name = "database_test_cli_execute_script_sql"
    ensure_database(ctx, db_name, state="absent")
    ensure_database(ctx, db_name, state="present")

    cli_runner_invoke(
        [
            "--log-level=DEBUG",
            "--env-folder=%s" % output_folder_path,
            "execute-script-sql",
            "--step=1",
            "--database=%s" % db_name,
        ]
    )

    # Ensure that the request has been done correctly
    request = "SELECT name from city order by id;"
    result = execute_sql_request(ctx, request, database=db_name)

    assert result == [["Chicago"], ["Cavalaire Sur Mer"]]
