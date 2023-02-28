import click
from loguru import logger

from odoo_openupgrade_wizard.cli.cli_options import (
    database_option_required,
    first_step_option,
    get_migration_steps_from_options,
    last_step_option,
)
from odoo_openupgrade_wizard.tools.tools_odoo import (
    execute_click_odoo_python_files,
    kill_odoo,
    run_odoo,
)
from odoo_openupgrade_wizard.tools.tools_postgres import (
    execute_sql_files_pre_migration,
)


@click.command()
@first_step_option
@last_step_option
@database_option_required
@click.pass_context
def upgrade(ctx, first_step, last_step, database):

    migration_steps = get_migration_steps_from_options(
        ctx, first_step, last_step
    )
    for migration_step in migration_steps:
        execute_sql_files_pre_migration(ctx, database, migration_step)
        try:
            run_odoo(
                ctx,
                migration_step,
                database=database,
                detached_container=False,
                update="all",
                stop_after_init=True,
            )
        except (KeyboardInterrupt, SystemExit):
            logger.info("Received Keyboard Interrupt or System Exiting...")
        finally:
            kill_odoo(ctx, migration_step)
        execute_click_odoo_python_files(ctx, database, migration_step)
