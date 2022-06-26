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
from odoo_openupgrade_wizard.tools.tools_system import get_script_folder


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
    update: str,
    init: str,
    stop_after_init: bool,
    shell: bool,
    demo: bool,
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
        f" --config /odoo_env/_auto_generated_odoo.cfg"
        f" {demo_cmd}"
        f" {database_cmd}"
        f" {update_cmd}"
        f" {init_cmd}"
        f" {stop_after_init_cmd}"
    )
    return result


def generate_odoo_config_file(
    ctx, migration_step, log_file, execution_context
):
    """Create a config file name _auto_generated_odoo.cfg
    in the according environment (defined by migration_step)
    This configuration file is a merge of the odoo.cfg file that can
    contain custom values, and the values required to run the docker container.
    """
    odoo_env_path = get_odoo_env_path(ctx, migration_step["version"])

    custom_odoo_config_file = odoo_env_path / "odoo.cfg"
    auto_generated_odoo_config_file = (
        odoo_env_path / "_auto_generated_odoo.cfg"
    )

    parser = configparser.RawConfigParser()
    # Read custom file
    parser.read(custom_odoo_config_file)

    # compute addons_path
    addons_path = ",".join(
        [
            str(x)
            for x in get_odoo_addons_path(
                ctx, Path("/odoo_env"), migration_step, execution_context
            )
        ]
    )

    # compute server wides modules
    server_wide_modules = parser.get(
        "options", "server_wide_modules", fallback=[]
    )
    server_wide_modules += get_server_wide_modules_upgrade(migration_step)

    # Add required keys
    if "options" not in parser:
        parser.add_section("options")
    parser.set("options", "db_host", "db")
    parser.set("options", "db_port", 5432)
    parser.set("options", "db_user", "odoo")
    parser.set("options", "db_password", "odoo")
    parser.set("options", "workers", 0)
    parser.set("options", "data_dir", "/env/filestore/")
    parser.set("options", "logfile", log_file)
    parser.set("options", "addons_path", addons_path)
    if server_wide_modules:
        parser.set(
            "options", "server_wide_modules", ",".join(server_wide_modules)
        )

    parser.write(open(auto_generated_odoo_config_file, "w"))


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
    env_path = ctx.obj["env_folder_path"]
    odoo_env_path = get_odoo_env_path(ctx, migration_step["version"])
    log_file = "/env/log/{}____{}.log".format(
        ctx.obj["log_prefix"], migration_step["complete_name"]
    )
    generate_odoo_config_file(ctx, migration_step, log_file, execution_context)

    command = generate_odoo_command(
        ctx,
        migration_step,
        execution_context,
        database=database,
        update=update,
        init=init,
        stop_after_init=stop_after_init,
        shell=shell,
        demo=demo,
    )

    host_xmlrpc_port = (
        alternative_xml_rpc_port
        and alternative_xml_rpc_port
        or ctx.obj["config"]["odoo_host_xmlrpc_port"]
    )
    links.update({ctx.obj["config"]["postgres_container_name"]: "db"})
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

    # Prepare data information for docker
    links = {ctx.obj["config"]["postgres_container_name"]: "db"}
    env_path = ctx.obj["env_folder_path"]
    odoo_env_path = get_odoo_env_path(ctx, migration_step["version"])

    # Generate odoo config file
    log_file = "/env/log/{}____{}__post_migration.log".format(
        ctx.obj["log_prefix"], migration_step["complete_name"]
    )
    generate_odoo_config_file(ctx, migration_step, log_file, execution_context)

    for python_file in python_files:
        # TODO, check if we should set python2 for old version of Odoo
        # or just 'python'
        command = (
            "click-odoo"
            " --database {database}"
            " --config /odoo_env/_auto_generated_odoo.cfg"
            " /env/{python_file}"
        ).format(
            database=database,
            python_file=str(python_file),
        )
        try:
            logger.info(
                "Executing script %s / %s"
                % (migration_step["complete_name"], python_file)
            )
            run_container(
                get_docker_image_tag(ctx, migration_step["version"]),
                get_docker_container_name(ctx, migration_step),
                command=command,
                ports={},
                volumes={
                    env_path: "/env/",
                    odoo_env_path: "/odoo_env/",
                },
                links=links,
                detach=False,
                auto_remove=True,
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
