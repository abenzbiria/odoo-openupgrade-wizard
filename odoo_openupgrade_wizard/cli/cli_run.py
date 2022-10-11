import click
from loguru import logger

from odoo_openupgrade_wizard.cli.cli_options import (
    database_option,
    get_migration_step_from_options,
    step_option,
)
from odoo_openupgrade_wizard.tools.tools_odoo import kill_odoo, run_odoo
from odoo_openupgrade_wizard.tools.tools_postgres import ensure_database


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
    "-i",
    "--init-modules",
    type=str,
    help="List of modules to install. Equivalent to -i odoo options.",
)
@click.option(
    "-e",
    "--execution-context",
    type=click.Choice(["regular", "openupgrade"]),
    help="Force to use an openupgrade (OCA/openupgrade)"
    " or a regular (odoo/odoo or OCA/OCB) base code when running odoo."
    " Let empty to use the defaut execution of the migration step.",
)
@click.pass_context
def run(ctx, step, database, stop_after_init, init_modules, execution_context):
    migration_step = get_migration_step_from_options(ctx, step)
    ensure_database(ctx, database, state="present")
    try:
        run_odoo(
            ctx,
            migration_step,
            database=database,
            detached_container=not stop_after_init,
            init=init_modules,
            stop_after_init=stop_after_init,
            execution_context=execution_context,
        )
        if not stop_after_init:
            logger.info(
                "Odoo is available on your host at"
                " http://localhost:%s"
                % ctx.obj["config"]["odoo_host_xmlrpc_port"]
            )
            input("Press 'Enter' to kill the odoo container and exit ...")
    except (KeyboardInterrupt, SystemExit):
        logger.info("Received Keyboard Interrupt or System Exiting...")
    finally:
        kill_odoo(ctx, migration_step)
