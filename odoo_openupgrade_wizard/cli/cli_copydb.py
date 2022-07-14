import click

from odoo_openupgrade_wizard.tools import (
    tools_click_odoo_contrib as click_odoo_contrib,
)


@click.command()
@click.option(
    "-s",
    "--source",
    type=str,
    help="Name of the database to copy",
)
@click.option(
    "-d",
    "--dest",
    type=str,
    help="Name of the new database",
)
@click.pass_context
def copydb(ctx, source, dest):
    """Create an Odoo database by copying an existing one.
    it will copy the postgres database and the filestore.
    """
    click_odoo_contrib.copydb(ctx, source, dest)
