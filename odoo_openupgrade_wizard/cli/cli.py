import datetime
import logging
import sys
from pathlib import Path

import click
import yaml
from click_loglevel import LogLevel
from loguru import logger

import odoo_openupgrade_wizard
from odoo_openupgrade_wizard.cli.cli_docker_build import docker_build
from odoo_openupgrade_wizard.cli.cli_estimate_workload import estimate_workload
from odoo_openupgrade_wizard.cli.cli_execute_script_python import (
    execute_script_python,
)
from odoo_openupgrade_wizard.cli.cli_execute_script_sql import (
    execute_script_sql,
)
from odoo_openupgrade_wizard.cli.cli_generate_module_analysis import (
    generate_module_analysis,
)
from odoo_openupgrade_wizard.cli.cli_get_code import get_code
from odoo_openupgrade_wizard.cli.cli_init import init
from odoo_openupgrade_wizard.cli.cli_install_from_csv import install_from_csv
from odoo_openupgrade_wizard.cli.cli_run import run
from odoo_openupgrade_wizard.cli.cli_upgrade import upgrade
from odoo_openupgrade_wizard.tools.tools_system import ensure_folder_exists


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
    # Note: postgres folder should be a subfolder, because
    # the parent folder will contain a .gitignore file
    # that the postgres docker image doesn't like
    postgres_folder_path = env_folder_path / Path("./postgres_data/data")
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
    ctx.obj["postgres_folder_path"] = postgres_folder_path
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
    elif ctx.invoked_subcommand != "init":
        raise


main.add_command(docker_build)
main.add_command(estimate_workload)
main.add_command(execute_script_python)
main.add_command(execute_script_sql)
main.add_command(generate_module_analysis)
main.add_command(get_code)
main.add_command(init)
main.add_command(install_from_csv)
main.add_command(run)
main.add_command(upgrade)
