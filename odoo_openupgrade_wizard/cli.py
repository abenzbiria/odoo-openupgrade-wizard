import datetime
from pathlib import Path

import click
import yaml
from loguru import logger
from plumbum.cmd import mkdir

import odoo_openupgrade_wizard
from odoo_openupgrade_wizard.cli_build import build
from odoo_openupgrade_wizard.cli_init import init


@click.group()
@click.version_option(version=odoo_openupgrade_wizard.__version__)
@click.option(
    "-ef",
    "--env-folder",
    default="./",
    type=click.Path(
        exists=True,
        dir_okay=True,
        file_okay=False,
        writable=True,
        resolve_path=True,
    ),
    help="Folder that will contains all the configuration of the wizard"
    " and all the Odoo code required to make the migrations. Let empty to"
    " use current folder (./).",
)
@click.option(
    "-fs",
    "--filestore-folder",
    type=click.Path(dir_okay=True, file_okay=False, resolve_path=True),
    help="Folder that contains the Odoo filestore of the database(s)"
    " to migrate. Let empty to use the subfolder 'filestore' of the"
    " environment folder.",
)
@click.pass_context
def main(ctx, env_folder, filestore_folder):
    """
    Provides a command set to perform odoo Community Edition migrations.
    """
    date_begin = datetime.datetime.now()
    logger.debug("Beginning script '%s' ..." % (ctx.invoked_subcommand))
    if not isinstance(ctx.obj, dict):
        ctx.obj = {}

    env_folder_path = Path(env_folder)
    src_folder_path = env_folder_path / Path("./src/")
    repo_folder_path = env_folder_path / Path("./repos/")
    requirement_folder_path = env_folder_path / Path("./requirements/")
    script_folder_path = env_folder_path / Path("./scripts/")

    if not filestore_folder:
        filestore_folder_path = env_folder_path / Path("./filestore/")
    else:
        filestore_folder_path = Path(filestore_folder)

    config_file_path = env_folder_path / Path("config.yml")

    # ###
    # Handle log
    # ###
    log_folder_path = env_folder_path / Path("./log/")

    # create log directory if not exists
    if not log_folder_path.exists():
        logger.info("Creating folder '%s' ..." % (log_folder_path))
        mkdir(["--mode", "777", log_folder_path])

    # Create log file
    log_file_path = log_folder_path / Path(
        "{}__{}.log".format(
            date_begin.strftime("%Y_%m_%d__%H_%M_%S"), ctx.invoked_subcommand
        )
    )
    logger.add(log_file_path)
    ctx.obj["env_folder_path"] = env_folder_path
    ctx.obj["src_folder_path"] = src_folder_path
    ctx.obj["repo_folder_path"] = repo_folder_path
    ctx.obj["script_folder_path"] = script_folder_path
    ctx.obj["filestore_folder_path"] = filestore_folder_path
    ctx.obj["config_file_path"] = config_file_path
    ctx.obj["requirement_folder_path"] = requirement_folder_path

    if config_file_path.exists():
        with open(config_file_path) as file:
            config = yaml.safe_load(file)
            for step in config["migration_steps"]:
                step["local_path"] = src_folder_path / Path(
                    "env_%s" % step["version"]
                )
            ctx.obj["config"] = config
    elif ctx.invoked_subcommand != "init":
        raise


main.add_command(init)
main.add_command(build)
