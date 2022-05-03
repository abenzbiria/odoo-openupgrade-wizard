import click

from odoo_openupgrade_wizard.cli_options import (
    database_option_required,
    get_migration_step_from_options,
    step_option,
)
from odoo_openupgrade_wizard.tools_odoo import (
    execute_python_files_post_migration,
)


@click.command()
@step_option
@database_option_required
@click.pass_context
def execute_script(ctx, step, database):

    migration_step = get_migration_step_from_options(ctx, step)

    execute_python_files_post_migration(ctx, database, migration_step)
