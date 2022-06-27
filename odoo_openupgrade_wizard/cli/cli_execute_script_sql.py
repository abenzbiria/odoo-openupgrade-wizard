from pathlib import Path

import click

from odoo_openupgrade_wizard.cli.cli_options import (
    database_option_required,
    get_migration_step_from_options,
    step_option,
)
from odoo_openupgrade_wizard.tools.tools_postgres import (
    execute_sql_files_pre_migration,
)


@click.command()
@step_option
@database_option_required
@click.option(
    "--script-file-path",
    multiple=True,
    type=click.Path(
        exists=True,
        dir_okay=False,
    ),
    help="List of SQL files that will be executed, replacing the default"
    " scripts placed in the migration step folder.",
)
@click.pass_context
def execute_script_sql(ctx, step, database, script_file_path):
    migration_step = get_migration_step_from_options(ctx, step)

    execute_sql_files_pre_migration(
        ctx, database, migration_step, [Path(x) for x in script_file_path]
    )
