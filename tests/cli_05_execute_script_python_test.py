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


def test_cli_execute_script_python():
    move_to_test_folder()
    ctx = build_ctx_from_config_file()

    extra_script_path = Path("../extra_script/click_odoo_test.py").absolute()
    cp(
        extra_script_path,
        Path("click_odoo_test.py"),
    )

    db_name = "database_test_cli___execute_script_python"
    ensure_database(ctx, db_name, state="absent")

    # Install Odoo on V13 with base installed
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

    # Compute partners quantity
    request = "SELECT count(*)" " FROM res_partner;"
    partner_quantity_before = int(
        execute_sql_request(ctx, request, database=db_name)[0][0]
    )

    # Execute Custom Python Script
    cli_runner_invoke(
        [
            "--log-level=DEBUG",
            "execute-script-python",
            "--step=1",
            "--database=%s" % db_name,
            "--script-file-path=click_odoo_test.py",
        ]
    )
    partner_quantity_after = int(
        execute_sql_request(ctx, request, database=db_name)[0][0]
    )

    # Ensure that partners have been created by click_odoo_test.py
    assert partner_quantity_after == (partner_quantity_before + 10)
