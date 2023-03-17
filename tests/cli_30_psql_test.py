from pytest import raises

from odoo_openupgrade_wizard.tools.tools_postgres import (
    ensure_database,
    execute_psql_command,
)

from . import (
    build_ctx_from_config_file,
    cli_runner_invoke,
    move_to_test_folder,
)


def test_cli_psql():
    move_to_test_folder()
    ctx = build_ctx_from_config_file()

    db_name = "database_test_cli___psql"
    ensure_database(ctx, db_name, state="absent")

    # initialize database
    cli_runner_invoke(
        [
            "--log-level=DEBUG",
            "run",
            "--step=1",
            "--database=%s" % db_name,
            "--init-modules=base",
            "--stop-after-init",
        ],
    )

    # Test requests from lib
    request = (
        "SELECT name"
        " FROM ir_module_module"
        " WHERE state ='installed'"
        " AND name='base';"
    )
    output = execute_psql_command(
        ctx,
        request,
        database=db_name,
        psql_args=("--tuples-only",),
    )
    assert output.strip() == "base"

    # test via cli ok
    cli_runner_invoke(
        [
            "--log-level=DEBUG",
            "psql",
            "--database=%s" % db_name,
            '--command "%s"' % request,
            "--no-pager",
            "--tuples-only",
        ],
    )

    # test that cli fails with wrong parameters
    with raises(Exception):
        cli_runner_invoke(
            [
                "--log-level=DEBUG",
                "psql",
                "--database=%s" % db_name,
                '--command "%s"' % request,
                "--no-pager",
                "--tuples-only",
                "---unknwon-argument",
            ],
        )
