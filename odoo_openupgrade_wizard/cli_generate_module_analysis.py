import click
from loguru import logger

from odoo_openupgrade_wizard.cli_options import (
    database_option,
    get_migration_steps_from_options,
)
from odoo_openupgrade_wizard.configuration_version_dependant import (
    generate_records,
    get_upgrade_analysis_module,
)
from odoo_openupgrade_wizard.tools_odoo import kill_odoo, run_odoo
from odoo_openupgrade_wizard.tools_odoo_instance import OdooInstance


@click.command()
@click.option(
    "--last-step",
    required=True,
    prompt=True,
    type=int,
    help="Last step in witch the analysis will be generated",
)
@click.option(
    "--modules",
    type=str,
    help="Coma-separated list of modules to analysis."
    " Let empty to analyse all the modules.",
)
@database_option
@click.pass_context
def generate_module_analysis(ctx, last_step, database, modules):

    migration_steps = get_migration_steps_from_options(
        ctx, last_step - 1, last_step
    )

    initial_step = migration_steps[0].copy()
    final_step = migration_steps[1].copy()

    if not database:
        database = "%s__analysis__" % (
            ctx.obj["config"]["project_name"].replace("-", "_"),
        )

    initial_database = "%s_%s" % (
        database,
        str(initial_step["release"]).replace(".", ""),
    )
    final_database = "%s_%s" % (
        database,
        str(final_step["release"]).replace(".", ""),
    )

    if not modules:
        modules = "base"

    # Force to be in openupgrade mode
    initial_step["action"] = final_step["action"] = "upgrade"

    try:
        run_odoo(
            ctx,
            initial_step,
            database=initial_database,
            detached_container=False,
            stop_after_init=True,
            init=modules + "," + get_upgrade_analysis_module(initial_step),
        )

        run_odoo(
            ctx,
            initial_step,
            database=initial_database,
            detached_container=True,
        )

        initial_instance = OdooInstance(ctx, initial_database)
        generate_records(initial_instance, initial_step)

        final_database = final_database
    except (KeyboardInterrupt, SystemExit):
        logger.info("Received Keyboard Interrupt or System Exiting...")
    finally:
        kill_odoo(ctx, initial_step)
        kill_odoo(ctx, final_step)
