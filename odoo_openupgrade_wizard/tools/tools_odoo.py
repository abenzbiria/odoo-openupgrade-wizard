import configparser
import csv
import os
import sys
import traceback
from pathlib import Path

import yaml
from loguru import logger

from odoo_openupgrade_wizard.configuration_version_dependant import (
    get_base_module_folder,
    get_odoo_folder,
    get_odoo_run_command,
    get_server_wide_modules_upgrade,
    skip_addon_path,
)
from odoo_openupgrade_wizard.tools.tools_docker import (
    kill_container,
    run_container,
)
from odoo_openupgrade_wizard.tools.tools_postgres import get_postgres_container
from odoo_openupgrade_wizard.tools.tools_system import (
    get_local_user_id,
    get_script_folder,
)


def get_odoo_addons_path(
    ctx, root_path: Path, migration_step: dict, execution_context: str = False
) -> str:
    repo_file = get_odoo_env_path(ctx, migration_step["version"]) / Path(
        "repos.yml"
    )
    base_module_folder = get_base_module_folder(migration_step)
    stream = open(repo_file, "r")
    data = yaml.safe_load(stream)
    data = data

    addons_path = []
    for key in data.keys():
        path = root_path / Path(key)
        if str(path).endswith(
            get_odoo_folder(migration_step, execution_context)
        ):
            # Add two folder for odoo folder
            addons_path.append(path / Path("addons"))
            addons_path.append(
                path / Path(base_module_folder) / Path("addons")
            )
        elif skip_addon_path(migration_step, path):
            pass
        else:
            addons_path.append(path)

    return addons_path


def get_odoo_env_path(ctx, odoo_version: float) -> Path:
    folder_name = "env_%s" % str(odoo_version).rjust(4, "0")
    return ctx.obj["src_folder_path"] / folder_name


def get_docker_image_tag(ctx, odoo_version: float) -> str:
    """Return a docker image tag, based on project name and odoo version"""
    return "odoo-openupgrade-wizard-image__%s__%s" % (
        ctx.obj["config"]["project_name"],
        str(odoo_version).rjust(4, "0"),
    )


def get_docker_container_name(ctx, migration_step: dict) -> str:
    """Return a docker container name, based on project name,
    odoo version and migration step"""
    return "odoo-openupgrade-wizard-container__%s__%s__step-%s" % (
        ctx.obj["config"]["project_name"],
        str(migration_step["version"]).rjust(4, "0"),
        str(migration_step["name"]).rjust(2, "0"),
    )


def generate_odoo_command(
    ctx,
    migration_step: dict,
    execution_context: str,
    database: str,
    demo: bool = False,
    update: str = False,
    init: str = False,
    stop_after_init: bool = False,
    shell: bool = False,
) -> str:
    database_cmd = database and "--database %s" % database or ""
    update_cmd = update and "--update %s" % update or ""
    init_cmd = init and "--init %s" % init or ""
    stop_after_init_cmd = stop_after_init and "--stop-after-init" or ""
    shell_cmd = shell and "shell" or ""
    demo_cmd = not demo and "--without-demo all" or ""
    command = (
        Path("/odoo_env")
        / Path(get_odoo_folder(migration_step, execution_context))
        / Path(get_odoo_run_command(migration_step))
    )
    result = (
        f" {command}"
        f" {shell_cmd}"
        # f" --config /etc/odoo.cfg"
        f" --data-dir /env/filestore/"
        f" {demo_cmd}"
        f" {database_cmd}"
        f" {update_cmd}"
        f" {init_cmd}"
        f" {stop_after_init_cmd}"
    )
    return result


def run_odoo(
    ctx,
    migration_step: dict,
    detached_container: bool = False,
    database: str = False,
    update: str = False,
    init: str = False,
    stop_after_init: bool = False,
    shell: bool = False,
    demo: bool = False,
    execution_context: str = False,
    alternative_xml_rpc_port: int = False,
    links: dict = {},
):
    # Ensure that Postgres container exist
    get_postgres_container(ctx)
    logger.info(
        "Launching Odoo Container (Version {version}) for {db_text}"
        " in {execution_context} mode. Demo Data is {demo_text}"
        " {stop_text} {init_text} {update_text}".format(
            version=migration_step["version"],
            db_text=database and "database '%s'" % database or "any databases",
            execution_context=execution_context
            or migration_step["execution_context"],
            demo_text=demo and "enabled" or "disabled",
            stop_text=stop_after_init and " (stop-after-init)" or "",
            init_text=init and " (Init : %s)" % init or "",
            update_text=update and " (Update : %s)" % update or "",
        )
    )

    command = generate_odoo_command(
        ctx,
        migration_step,
        execution_context,
        database,
        demo=demo,
        update=update,
        init=init,
        stop_after_init=stop_after_init,
        shell=shell,
    )

    return run_container_odoo(
        ctx,
        migration_step,
        command,
        detached_container=detached_container,
        database=database,
        execution_context=execution_context,
        alternative_xml_rpc_port=alternative_xml_rpc_port,
    )


def run_container_odoo(
    ctx,
    migration_step: dict,
    command: str,
    detached_container: bool = False,
    database: str = False,
    alternative_xml_rpc_port: int = False,
    execution_context: str = False,
    log_file_suffix: str = "",
    links: dict = {},
):
    env_path = ctx.obj["env_folder_path"]
    odoo_env_path = get_odoo_env_path(ctx, migration_step["version"])

    # Compute 'server_wide_modules'
    # For that purpose, read the custom odoo.cfg file
    # to know if server_wide_modules is defined
    custom_odoo_config_file = odoo_env_path / "odoo.cfg"
    parser = configparser.RawConfigParser()
    parser.read(custom_odoo_config_file)
    server_wide_modules = parser.get(
        "options", "server_wide_modules", fallback=[]
    )
    server_wide_modules += get_server_wide_modules_upgrade(
        migration_step, execution_context
    )

    # compute 'addons_path'
    addons_path = ",".join(
        [
            str(x)
            for x in get_odoo_addons_path(
                ctx, Path("/odoo_env"), migration_step, execution_context
            )
        ]
    )

    # compute 'log_file'
    log_file = "/env/log/{}____{}{}.log".format(
        ctx.obj["log_prefix"], migration_step["complete_name"], log_file_suffix
    )
    host_xmlrpc_port = (
        alternative_xml_rpc_port
        and alternative_xml_rpc_port
        or ctx.obj["config"]["odoo_host_xmlrpc_port"]
    )

    links.update({ctx.obj["config"]["postgres_container_name"]: "db"})

    environments = {
        "DB_HOST": "db",
        "DB_PORT": 5432,
        "DB_USER": "odoo",
        "DB_PASSWORD": "odoo",
        "DB_NAME": database,
        "LOGFILE": log_file,
        "ADDONS_PATH": addons_path,
        "WORKERS": 0,
        "LOCAL_USER_ID": get_local_user_id(),
    }
    # TODO, handle custom config.cfg file
    if server_wide_modules:
        environments["SERVER_WIDE_MODULES"] = ",".join(server_wide_modules)

    return run_container(
        get_docker_image_tag(ctx, migration_step["version"]),
        get_docker_container_name(ctx, migration_step),
        command=command,
        ports={
            host_xmlrpc_port: 8069,
        },
        volumes={
            env_path: "/env/",
            odoo_env_path: "/odoo_env/",
        },
        environments=environments,
        links=links,
        detach=detached_container,
        auto_remove=True,
    )


def kill_odoo(ctx, migration_step: dict):
    kill_container(get_docker_container_name(ctx, migration_step))


def execute_click_odoo_python_files(
    ctx,
    database: str,
    migration_step: dict,
    python_files: list = [],
    execution_context: str = False,
):

    if not python_files:
        # Get post-migration python scripts to execute
        script_folder = get_script_folder(ctx, migration_step)
        python_files = [
            Path("scripts") / Path(migration_step["complete_name"]) / Path(f)
            for f in os.listdir(script_folder)
            if os.path.isfile(os.path.join(script_folder, f))
            and f[-3:] == ".py"
        ]
        python_files = sorted(python_files)

    command = generate_odoo_command(
        ctx,
        migration_step,
        execution_context,
        database,
        shell=True,
    )

    for python_file in python_files:
        command = ("/bin/bash -c 'cat /env/{python_file} | {command}'").format(
            command=command,
            python_file=str(python_file),
        )
        try:
            logger.info(
                "Executing script %s / %s"
                % (migration_step["complete_name"], python_file)
            )
            return run_container_odoo(
                ctx,
                migration_step,
                command,
                detached_container=False,
                database=database,
            )

        except Exception as e:
            traceback.print_exc()
            logger.error(
                "An error occured. Exiting. %s\n%s"
                % (e, traceback.print_exception(*sys.exc_info()))
            )
            raise e
        finally:
            kill_odoo(ctx, migration_step)


def get_odoo_modules_from_csv(module_file_path: Path) -> list:
    logger.debug("Reading '%s' file ..." % module_file_path)
    module_names = []
    csvfile = open(module_file_path, "r")
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
    return module_names
