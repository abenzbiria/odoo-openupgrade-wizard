import datetime
import logging
import sys
from pathlib import Path

import click
import yaml
from click_loglevel import LogLevel
from loguru import logger

import odoo_openupgrade_wizard
from odoo_openupgrade_wizard.cli_docker_build import docker_build
from odoo_openupgrade_wizard.cli_execute_script import execute_script
from odoo_openupgrade_wizard.cli_get_code import get_code
from odoo_openupgrade_wizard.cli_init import init
from odoo_openupgrade_wizard.cli_run import run
from odoo_openupgrade_wizard.cli_test_dev import test_dev
from odoo_openupgrade_wizard.cli_upgrade import upgrade
from odoo_openupgrade_wizard.tools_system import ensure_folder_exists


@click.group()
@click.version_option(version=odoo_openupgrade_wizard.__version__)
@click.option(
    "--env-folder",
    default="./",
    type=click.Path(
        exists=True,
        file_okay=False,
        writable=True,
        resolve_path=True,
    ),
    help="Folder that will contains all the configuration of the wizard"
    " and all the Odoo code required to make the migrations. Let empty to"
    " use current folder (./).",
)
@click.option(
    "--filestore-folder",
    type=click.Path(
        exists=True, file_okay=False, writable=True, resolve_path=True
    ),
    help="Folder that contains the Odoo filestore of the database(s)"
    " to migrate. Let empty to use the subfolder 'filestore' of the"
    " environment folder.",
)
@click.option("-l", "--log-level", type=LogLevel(), default=logging.INFO)
@click.pass_context
def main(ctx, env_folder, filestore_folder, log_level):
    """
    Provides a command set to perform odoo Community Edition migrations.
    """
    date_begin = datetime.datetime.now()
    logger.remove()
    logger.add(sys.stderr, level=log_level)
    logger.debug("Beginning script '%s' ..." % (ctx.invoked_subcommand))
    if not isinstance(ctx.obj, dict):
        ctx.obj = {}

    # Define all the folder required by the tools
    env_folder_path = Path(env_folder)
    src_folder_path = env_folder_path / Path("./src/")
    script_folder_path = env_folder_path / Path("./scripts/")
    log_folder_path = env_folder_path / Path("./log/")
    if not filestore_folder:
        filestore_folder_path = env_folder_path / Path("./filestore/")
    else:
        filestore_folder_path = Path(filestore_folder)

    # ensure log folder exists
    ensure_folder_exists(log_folder_path, mode="777", git_ignore_content=True)

    # Create log file
    log_prefix = "{}__{}".format(
        date_begin.strftime("%Y_%m_%d__%H_%M_%S"), ctx.invoked_subcommand
    )
    log_file_path = log_folder_path / Path(log_prefix + ".log")
    logger.add(log_file_path)

    config_file_path = env_folder_path / Path("config.yml")
    module_file_path = env_folder_path / Path("modules.csv")

    # Add all global values in the context
    ctx.obj["env_folder_path"] = env_folder_path
    ctx.obj["src_folder_path"] = src_folder_path
    ctx.obj["script_folder_path"] = script_folder_path
    ctx.obj["log_folder_path"] = log_folder_path
    ctx.obj["log_prefix"] = log_prefix
    ctx.obj["filestore_folder_path"] = filestore_folder_path

    ctx.obj["config_file_path"] = config_file_path
    ctx.obj["module_file_path"] = module_file_path

    # Load the main configuration file
    if config_file_path.exists():
        with open(config_file_path) as file:
            config = yaml.safe_load(file)
            ctx.obj["config"] = config
            file.close()
    elif ctx.invoked_subcommand != "init":
        raise

    logger.debug("context %s: " % ctx.obj)


main.add_command(init)
main.add_command(get_code)
main.add_command(docker_build)
main.add_command(run)
main.add_command(upgrade)
main.add_command(execute_script)
main.add_command(test_dev)
