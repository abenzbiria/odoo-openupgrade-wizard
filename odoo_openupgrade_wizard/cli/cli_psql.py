import click

from odoo_openupgrade_wizard.cli.cli_options import database_option
from odoo_openupgrade_wizard.tools.tools_postgres import execute_psql_command


@click.command(context_settings={"ignore_unknown_options": True})
@database_option
@click.option("-c", "--command", "request")
@click.option("--pager/--no-pager", default=True)
@click.argument("psql_args", nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def psql(ctx, request, database, pager, psql_args):
    """Run psql in the postgres container. Fill any parameters of psql
    as PSQLARGS.
    """
    result = execute_psql_command(ctx, request, database, psql_args)
    if pager:
        click.echo_via_pager(result)
    else:
        click.echo(result)
