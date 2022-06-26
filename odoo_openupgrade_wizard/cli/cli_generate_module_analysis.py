import click
from loguru import logger

from odoo_openupgrade_wizard.cli.cli_options import (
    database_option,
    get_migration_steps_from_options,
    step_option,
)
from odoo_openupgrade_wizard.configuration_version_dependant import (
    generate_analysis_files,
    generate_records,
    get_installable_odoo_modules,
    get_upgrade_analysis_module,
)
from odoo_openupgrade_wizard.tools.tools_odoo import (
    get_odoo_env_path,
    kill_odoo,
    run_odoo,
)
from odoo_openupgrade_wizard.tools.tools_odoo_instance import OdooInstance
from odoo_openupgrade_wizard.tools.tools_system import ensure_folder_writable


@click.command()
@step_option
@database_option
@click.option(
    "-m",
    "--modules",
    type=str,
    help="Coma-separated list of modules to analysis."
    " Let empty to analyse all the Odoo modules.",
)
@click.pass_context
def generate_module_analysis(ctx, step, database, modules):

    migration_steps = get_migration_steps_from_options(ctx, step - 1, step)

    initial_step = migration_steps[0].copy()
    final_step = migration_steps[1].copy()

    alternative_xml_rpc_port = ctx.obj["config"]["odoo_host_xmlrpc_port"] + 10

    if not database:
        database = "%s__analysis__" % (
            ctx.obj["config"]["project_name"].replace("-", "_"),
        )

    initial_database = "%s_%s" % (
        database,
        str(initial_step["version"]).replace(".", ""),
    )
    final_database = "%s_%s" % (
        database,
        str(final_step["version"]).replace(".", ""),
    )

    modules = modules and modules.split(",") or []

    try:
        # INITIAL : Run odoo and install analysis module
        run_odoo(
            ctx,
            initial_step,
            database=initial_database,
            detached_container=False,
            stop_after_init=True,
            execution_context="openupgrade",
            init=get_upgrade_analysis_module(initial_step),
        )

        # INITIAL : Run odoo for odoorpc
        initial_container = run_odoo(
            ctx,
            initial_step,
            database=initial_database,
            execution_context="openupgrade",
            detached_container=True,
        )
        # INITIAL : install modules to analyse and generate records
        initial_instance = OdooInstance(ctx, initial_database)
        initial_modules = (
            modules
            and modules
            or get_installable_odoo_modules(initial_instance, initial_step)
        )
        initial_instance.install_modules(initial_modules)
        generate_records(initial_instance, initial_step)

        # FINAL : Run odoo and install analysis module
        run_odoo(
            ctx,
            final_step,
            database=final_database,
            detached_container=False,
            stop_after_init=True,
            init=get_upgrade_analysis_module(final_step),
            execution_context="openupgrade",
            alternative_xml_rpc_port=alternative_xml_rpc_port,
        )

        # name of the first odoo instance inside the second odoo instance
        odoo_initial_host_name = "odoo_initial_instance"

        # FINAL : Run odoo for odoorpc and install modules to analyse
        run_odoo(
            ctx,
            final_step,
            database=final_database,
            detached_container=True,
            alternative_xml_rpc_port=alternative_xml_rpc_port,
            execution_context="openupgrade",
            links={initial_container.name: odoo_initial_host_name},
        )

        # FINAL : install modules to analyse and generate records
        final_instance = OdooInstance(
            ctx,
            final_database,
            alternative_xml_rpc_port=alternative_xml_rpc_port,
        )
        final_modules = (
            modules
            and modules
            or get_installable_odoo_modules(final_instance, final_step)
        )
        final_instance.install_modules(final_modules)
        generate_records(final_instance, final_step)

        # Make writable files and directories for "other"
        # group to make possible to write analysis files
        # for docker container user
        ensure_folder_writable(
            get_odoo_env_path(ctx, final_step["version"]) / "src"
        )

        generate_analysis_files(
            final_instance,
            final_step,
            odoo_initial_host_name,
            initial_database,
        )

    except (KeyboardInterrupt, SystemExit):
        logger.info("Received Keyboard Interrupt or System Exiting...")
    finally:
        kill_odoo(ctx, initial_step)
        kill_odoo(ctx, final_step)
