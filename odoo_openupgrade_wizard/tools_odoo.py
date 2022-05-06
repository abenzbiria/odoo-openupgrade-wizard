import importlib.util
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
from odoo_openupgrade_wizard.tools_docker import kill_container, run_container
from odoo_openupgrade_wizard.tools_odoo_instance import OdooInstance
from odoo_openupgrade_wizard.tools_system import get_script_folder


def get_odoo_addons_path(ctx, root_path: Path, migration_step: dict) -> str:
    odoo_version = get_odoo_version_from_migration_step(ctx, migration_step)
    repo_file = get_odoo_env_path(ctx, odoo_version) / Path("repos.yml")
    base_module_folder = get_base_module_folder(migration_step)
    stream = open(repo_file, "r")
    data = yaml.safe_load(stream)
    data = data

    addons_path = []
    for key in data.keys():
        path = root_path / Path(key)
        if str(path).endswith(get_odoo_folder(migration_step)):
            # Add two folder for odoo folder
            addons_path.append(path / Path("addons"))
            addons_path.append(
                path / Path(base_module_folder) / Path("addons")
            )
        elif skip_addon_path(migration_step, path):
            pass
        else:
            addons_path.append(path)

    return ",".join([str(x) for x in addons_path])


def get_odoo_env_path(ctx, odoo_version: dict) -> Path:
    folder_name = "env_%s" % str(odoo_version["release"]).rjust(4, "0")
    return ctx.obj["src_folder_path"] / folder_name


def get_docker_image_tag(ctx, odoo_version: dict) -> str:
    """Return a docker image tag, based on project name and odoo release"""
    return "odoo-openupgrade-wizard-image__%s__%s" % (
        ctx.obj["config"]["project_name"],
        str(odoo_version["release"]).rjust(4, "0"),
    )


def get_docker_container_name(ctx, migration_step: dict) -> str:
    """Return a docker container name, based on project name,
    odoo release and migration step"""
    return "odoo-openupgrade-wizard-container__%s__%s__step-%s" % (
        ctx.obj["config"]["project_name"],
        str(migration_step["release"]).rjust(4, "0"),
        str(migration_step["name"]).rjust(2, "0"),
    )


def get_odoo_version_from_migration_step(ctx, migration_step: dict) -> dict:
    for odoo_version in ctx.obj["config"]["odoo_versions"]:
        if odoo_version["release"] == migration_step["release"]:
            return odoo_version
    # TODO, improve exception
    raise Exception


def get_server_wide_modules(ctx, migration_step: dict) -> str:
    # TODO, read from odoo.cfg file, the key server_wide_modules
    modules = []
    modules += get_server_wide_modules_upgrade(migration_step)
    return modules


def generate_odoo_command(
    ctx,
    migration_step: dict,
    database: str,
    update: str,
    init: str,
    stop_after_init: bool,
    shell: bool,
    demo: bool,
) -> str:
    addons_path = get_odoo_addons_path(ctx, Path("/odoo_env"), migration_step)
    server_wide_modules = get_server_wide_modules(ctx, migration_step)
    server_wide_modules_cmd = (
        server_wide_modules
        and "--load %s" % ",".join(server_wide_modules)
        or ""
    )
    database_cmd = database and "--database %s" % database or ""
    update_cmd = update and "--update %s" % update or ""
    init_cmd = init and "--init %s" % init or ""
    stop_after_init_cmd = stop_after_init and "--stop-after-init" or ""
    shell_cmd = shell and "shell" or ""
    demo_cmd = not demo and "--without-demo all" or ""
    log_file = "/env/log/{}____{}.log".format(
        ctx.obj["log_prefix"], migration_step["complete_name"]
    )
    command = (
        Path("/odoo_env")
        / Path(get_odoo_folder(migration_step))
        / Path(get_odoo_run_command(migration_step))
    )
    result = (
        f" {command}"
        f" {shell_cmd}"
        f" --db_host db"
        f" --db_port 5432"
        f" --db_user odoo"
        f" --db_password odoo"
        f" --workers 0"
        f" --config /odoo_env/odoo.cfg"
        f" --data-dir /env/filestore/"
        f" --logfile {log_file}"
        f" --addons-path {addons_path}"
        f" {server_wide_modules_cmd}"
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
    alternative_xml_rpc_port: int = False,
):
    logger.info(
        "Launching Odoo Container (Release {release}) for {db_text}"
        " in {action} mode. Demo Data is {demo_text}"
        " {stop_text} {init_text} {update_text}".format(
            release=migration_step["release"],
            db_text=database and "database '%s'" % database or "any databases",
            action=migration_step["action"] == "update"
            and "regular"
            or "OpenUpgrade",
            demo_text=demo and "enabled" or "disabled",
            stop_text=stop_after_init and " (stop-after-init)" or "",
            init_text=init and " (Init : %s)" % init or "",
            update_text=update and " (Update : %s)" % update or "",
        )
    )
    odoo_version = get_odoo_version_from_migration_step(ctx, migration_step)
    env_path = ctx.obj["env_folder_path"]
    odoo_env_path = get_odoo_env_path(ctx, odoo_version)

    command = generate_odoo_command(
        ctx,
        migration_step,
        database=database,
        update=update,
        init=init,
        stop_after_init=stop_after_init,
        shell=shell,
        demo=demo,
    )

    return run_container(
        get_docker_image_tag(ctx, odoo_version),
        get_docker_container_name(ctx, migration_step),
        command=command,
        ports={
            "8069": alternative_xml_rpc_port
            and alternative_xml_rpc_port
            or ctx.obj["config"]["odoo_host_xmlrpc_port"],
        },
        volumes={
            env_path: "/env/",
            odoo_env_path: "/odoo_env/",
        },
        links={ctx.obj["config"]["postgres_container_name"]: "db"},
        detach=detached_container,
        auto_remove=True,
    )


def kill_odoo(ctx, migration_step: dict):
    kill_container(get_docker_container_name(ctx, migration_step))


def execute_python_files_post_migration(
    ctx, database: str, migration_step: dict, python_files: list = []
):
    if not python_files:
        script_folder = get_script_folder(ctx, migration_step)

        python_files = [
            script_folder / Path(f)
            for f in os.listdir(script_folder)
            if os.path.isfile(os.path.join(script_folder, f))
            and f[-3:] == ".py"
        ]
        python_files = sorted(python_files)

    try:
        # Launch Odoo
        run_odoo(
            ctx,
            migration_step,
            detached_container=True,
            database=database,
        )

        # Create Odoo instance via Odoo RPC
        odoo_instance = OdooInstance(ctx, database)

        for python_file in python_files:
            # Generate Python Script

            logger.info("Running Script Post (Python) %s" % python_file)
            package_name = "script.%s.%s" % (
                migration_step["complete_name"],
                python_file.name[:-3],
            )
            module_spec = importlib.util.spec_from_file_location(
                package_name, python_file
            )
            module = importlib.util.module_from_spec(module_spec)
            module_spec.loader.exec_module(module)

            module.main(odoo_instance)
    except Exception as e:
        logger.error(
            "An error occured. Exiting. %s\n%s"
            % (e, traceback.print_exception(*sys.exc_info()))
        )
        raise e
    finally:
        kill_odoo(ctx, migration_step)
