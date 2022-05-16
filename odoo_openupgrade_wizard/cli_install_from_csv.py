import csv

import click
from loguru import logger

from odoo_openupgrade_wizard.cli_options import (
    database_option,
    get_migration_step_from_options,
)
from odoo_openupgrade_wizard.tools_odoo import kill_odoo, run_odoo
from odoo_openupgrade_wizard.tools_odoo_instance import OdooInstance
from odoo_openupgrade_wizard.tools_postgres import ensure_database


@click.command()
@database_option
@click.pass_context
def install_from_csv(ctx, database):
    migration_step = get_migration_step_from_options(ctx, 1)
    ensure_database(ctx, database, state="present")

    # Get modules list from the CSV file
    csv_path = ctx.obj["module_file_path"]
    logger.info("Reading '%s' file ..." % csv_path)
    module_names = []
    csvfile = open(csv_path, "r")
    spamreader = csv.reader(csvfile, delimiter=",", quotechar='"')
    for row in spamreader:
        # Try to guess that a line is not correct
        if not row:
            continue
        if not row[0]:
            continue
        if " " in row[0]:
            continue
        if any([x.isupper() for x in row[0]]):
            continue
        module_names.append(row[0])

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

        default_country_code = ctx.obj["config"].get(
            "odoo_default_country_code", False
        )
        if "account" in module_names and default_country_code:
            # Then, set correct country to the company of the current user
            # Otherwise, due to poor design of Odoo, when installing account
            # the US localization will be installed.
            # (l10n_us + l10n_generic_coa)

            countries = odoo_instance.browse_by_search(
                "res.country",
                [("code", "=", default_country_code)],
            )
            if len(countries) != 1:
                raise Exception(
                    "Unable to find a country, based on the code %s."
                    " countries found : %s "
                    % (
                        default_country_code,
                        ", ".join([x.name for x in countries]),
                    )
                )
            logger.info(
                "Configuring country of the main company with #%d - %s"
                % (countries[0].id, countries[0].name)
            )
            odoo_instance.env.user.company_id.country_id = countries[0].id

        # Install modules
        odoo_instance.install_modules(module_names)

    except (KeyboardInterrupt, SystemExit):
        logger.info("Received Keyboard Interrupt or System Exiting...")
    finally:
        kill_odoo(ctx, migration_step)
