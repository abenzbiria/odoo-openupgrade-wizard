from time import sleep

import click
from loguru import logger

from odoo_openupgrade_wizard.cli_options import (
    get_migration_step_from_options,
    step_options,
)
from odoo_openupgrade_wizard.tools_odoo import kill_odoo, run_odoo


@click.command()
@step_options
@click.option(
    "--duration",
    type=float,
    default=False,
    help="Duration of the execution of the script. Mainly used"
    " for test purpose, for commands that are using input()"
    " function to stop.",
)
@click.pass_context
def run(ctx, step, duration):

    migration_step = get_migration_step_from_options(ctx, step)
    try:
        run_odoo(ctx, migration_step)
        if duration:
            sleep(duration)
        else:
            input("Press 'Enter' to kill the odoo container and exit ...")
    except (KeyboardInterrupt, SystemExit):
        logger.info("Received Keyboard Interrupt or System Exiting...")
    finally:
        kill_odoo(ctx, migration_step)
