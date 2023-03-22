from pathlib import Path

import click

from odoo_openupgrade_wizard.cli.cli_options import database_option
from odoo_openupgrade_wizard.tools.tools_postgres import execute_pg_dump
from odoo_openupgrade_wizard.tools.tools_system import copy_filestore


@click.command()
@database_option
@click.option(
    "--database-path",
    type=click.Path(),
    help="Path to the database dump relative project folder.",
)
@click.option(
    "--database-format",
    type=click.Choice(("p", "c", "d", "t")),
    default="c",
    help="Database format (see pg_dump options): plain sql text (p), "
    "custom format compressed (c), directory (d), tar file (t).",
)
@click.option(
    "--filestore-path", type=click.Path(), help="Path to the filestore backup."
)
@click.option(
    "--filestore-format",
    type=click.Choice(("d", "t", "tgz")),
    default="tgz",
    help="Filestore format: directory (d), tar file (t), "
    "tar file compressed with gzip (tgz)",
)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Overwrite file if they already exists.",
)
@click.pass_context
def dumpdb(
    ctx,
    database,
    database_path,
    database_format,
    filestore_path,
    filestore_format,
    force,
):
    """Create an dump of an Odoo database and its filestore."""
    database_path = Path(database_path)
    filestore_path = Path(filestore_path)

    # Fail if dumps already exists and force argument not given
    if not force and database_path.exists():
        ctx.fail(f"{database_path} exists, use --force to overwrite it.")
    if not force and filestore_path.exists():
        ctx.fail(f"{filestore_path} exists, use --force to overwrite it.")

    # Check that database_path is inside the env_folder_path
    absolute_database_path = database_path.resolve().absolute()
    absolute_env_folder_path = ctx.obj["env_folder_path"].resolve().absolute()
    if not str(absolute_database_path).startswith(
        str(absolute_env_folder_path)
    ):
        ctx.fail(
            "database-path should be inside the project path to allow "
            "postgresql to write to it."
        )

    # Normalise database_path
    database_path = absolute_database_path.relative_to(
        absolute_env_folder_path
    )

    # dump the database
    output = execute_pg_dump(
        ctx,
        database=database,
        dumpformat=database_format,
        filename=str(database_path),
    )
    if output:
        click.echo(output)

    # dump the filestore
    copy_filestore(
        ctx,
        database=database,
        destpath=filestore_path,
        copyformat=filestore_format,
    )
