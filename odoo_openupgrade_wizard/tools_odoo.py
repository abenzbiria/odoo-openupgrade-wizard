from pathlib import Path

from odoo_openupgrade_wizard.tools_docker import kill_container, run_container


# WIP
def get_odoo_addons_path(ctx, odoo_version: dict, migration_step: dict) -> str:
    pass
    # repo_file = Path(
    #     self._current_directory,
    #     CUSTOMER_CONFIG_FOLDER,
    #     "repo_files",
    #     "%s.yml" % step["version"],
    # )
    # folder = Path(self._current_directory, step["local_path"])
    # base_module_folder = get_base_module_folder(step)
    # stream = open(repo_file, "r")
    # data = yaml.safe_load(stream)

    # addons_path = []
    # for key in data.keys():
    #     path = os.path.join(folder, key)
    #     if path.endswith(get_odoo_folder(step)):
    #         # Add two folder for odoo folder
    #         addons_path.append(os.path.join(path, "addons"))
    #         addons_path.append(
    #             os.path.join(path, base_module_folder, "addons")
    #         )
    #     elif skip_path(step, path):
    #         pass
    #     else:
    #         addons_path.append(path)

    # return ",".join(addons_path)


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
    return "odoo-openupgrade-wizard-container---%s---%s---step---%s" % (
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
    # TODO, make it dynamic
    addons_path = "/odoo_env/src/odoo/addons," "/odoo_env/src/odoo/odoo/addons"
    database_cmd = database and "--database %s" % database or ""
    update_cmd = update and "--update_%s" % update or ""
    init_cmd = init and "--init %s" % init or ""
    stop_after_init_cmd = stop_after_init and "--stop-after-init" or ""
    shell_cmd = shell and "shell" or ""
    demo_cmd = not demo and "--without-demo all" or ""
    log_file = "/env/log/{}____{}.log".format(
        ctx.obj["log_prefix"], migration_step["complete_name"]
    )
    result = (
        f"/odoo_env/src/odoo/odoo-bin"
        f" --db_host db"
        f" --db_port 5432"
        f" --db_user odoo"
        f" --db_password odoo"
        f" --workers 0"
        f" --config /odoo_env/odoo.cfg"
        # f" --data-dir /env/filestore/"
        f" --logfile {log_file}"
        f" --addons-path {addons_path}"
        f" {database_cmd}"
        f" {update_cmd}"
        f" {init_cmd}"
        f" {stop_after_init_cmd}"
        f" {shell_cmd}"
        f" {demo_cmd}"
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
):
    # TODO, check if stop_after_init and detached_container are redondant.
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
        ports={"8069": 8069, "5432": 5432},
        volumes=[
            "%s:/env/" % (env_path),
            "%s:/odoo_env/" % (odoo_env_path),
        ],
        links={"db": "db"},
        detach=detached_container,
        auto_remove=True,
    )


def kill_odoo(ctx, migration_step: dict):
    kill_container(get_docker_container_name(ctx, migration_step))
