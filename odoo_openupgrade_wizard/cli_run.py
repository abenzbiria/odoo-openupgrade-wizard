import click
from loguru import logger

from odoo_openupgrade_wizard.cli_options import (
    database_option,
    get_migration_step_from_options,
    step_option,
)
from odoo_openupgrade_wizard.tools_odoo import kill_odoo, run_odoo


@click.command()
@step_option
@database_option
@click.option(
    "--stop-after-init",
    is_flag=True,
    default=False,
    help="Stop after init. Mainly used"
    " for test purpose, for commands that are using input()"
    " function to stop.",
)
@click.option(
    "--init-modules",
    type=str,
    help="List of modules to install. Equivalent to -i odoo options.",
)
@click.pass_context
def run(ctx, step, database, stop_after_init, init_modules):

    migration_step = get_migration_step_from_options(ctx, step)
    try:
        run_odoo(
            ctx,
            migration_step,
            database=database,
            detached_container=not stop_after_init,
            init=init_modules,
            stop_after_init=stop_after_init,
        )
        if not stop_after_init:
            input("Press 'Enter' to kill the odoo container and exit ...")
    except (KeyboardInterrupt, SystemExit):
        logger.info("Received Keyboard Interrupt or System Exiting...")
    finally:
        kill_odoo(ctx, migration_step)
