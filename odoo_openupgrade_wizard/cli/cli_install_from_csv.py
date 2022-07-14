import click
from loguru import logger

from odoo_openupgrade_wizard.cli.cli_options import (
    database_option,
    get_migration_step_from_options,
)
from odoo_openupgrade_wizard.tools.tools_odoo import (
    get_odoo_modules_from_csv,
    kill_odoo,
    run_odoo,
)
from odoo_openupgrade_wizard.tools.tools_odoo_instance import OdooInstance
from odoo_openupgrade_wizard.tools.tools_postgres import ensure_database


@click.command()
@database_option
@click.pass_context
def install_from_csv(ctx, database):
    migration_step = get_migration_step_from_options(ctx, 1)
    ensure_database(ctx, database, state="present")

    # Get modules list from the CSV file
    module_names = get_odoo_modules_from_csv(ctx.obj["module_file_path"])
    module_names.sort()
    logger.info("Found %d modules." % (len(module_names)))
    logger.debug(module_names)

    try:
        logger.info("Install 'base' module on %s database ..." % (database))
        run_odoo(
            ctx,
            migration_step,
            database=database,
            detached_container=True,
            init="base",
        )
        odoo_instance = OdooInstance(ctx, database)
        odoo_default_company = ctx.obj["config"].get(
            "odoo_default_company", False
        )
        if odoo_default_company:
            # Then, set correct country to the company of the current user
            # Otherwise, due to poor design of Odoo, when installing account
            # the US localization will be installed.
            # (l10n_us + l10n_generic_coa)

            countries = odoo_instance.browse_by_search(
                "res.country",
                [("code", "=", odoo_default_company["country_code"])],
            )
            if len(countries) != 1:
                raise Exception(
                    "Unable to find a country, based on the code %s."
                    " countries found : %s "
                    % (
                        odoo_default_company["country_code"],
                        ", ".join([x.name for x in countries]),
                    )
                )
            vals = {
                "country_id": countries[0].id,
                "currency_id": countries[0].currency_id.id,
                "phone": odoo_default_company.get("phone"),
                "email": odoo_default_company.get("email"),
            }
            logger.info(
                f"Configuring main company with values {vals}"
                f" (country {countries[0].name}"
            )

            odoo_instance.env.user.company_id.write(vals)

        # Install modules
        odoo_instance.install_modules(module_names)

    except (KeyboardInterrupt, SystemExit):
        logger.info("Received Keyboard Interrupt or System Exiting...")
    finally:
        kill_odoo(ctx, migration_step)
