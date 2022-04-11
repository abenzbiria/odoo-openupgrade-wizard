from pathlib import Path

import docker
from loguru import logger


def get_odoo_env_path(ctx, odoo_version: dict) -> Path:
    folder_name = "env_%s" % str(odoo_version["release"]).rjust(4, "0")
    return ctx.obj["src_folder_path"] / folder_name


def get_docker_image_tag(ctx, odoo_version: dict) -> str:
    """Return a docker image tag, based on project name and odoo release"""
    return "odoo-openupgrade-wizard-image-%s-%s" % (
        ctx.obj["config"]["project_name"],
        str(odoo_version["release"]).rjust(4, "0"),
    )


def get_docker_container_name(ctx, migration_step: dict) -> str:
    """Return a docker container name, based on project name,
    odoo release and migration step"""
    return "odoo-openupgrade-wizard-container-%s-%s-step-%s" % (
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
    ctx, migration_step: dict, update_all: bool = False
) -> str:
    # TODO, make it dynamic
    addons_path = (
        "/container_env/src/odoo/addons," "/container_env/src/odoo/odoo/addons"
    )
    update_all_cmd = update_all and "--update_all" or ""
    return (
        f"/container_env/src/odoo/odoo-bin"
        f" --db_host db"
        f" --db_port 5432"
        f" --db_user odoo"
        f" --db_password odoo"
        f" --addons-path {addons_path}"
        f" {update_all_cmd}"
    )


def run_odoo(ctx, migration_step: dict):
    client = docker.from_env()
    odoo_version = get_odoo_version_from_migration_step(ctx, migration_step)
    folder_path = get_odoo_env_path(ctx, odoo_version)

    command = generate_odoo_command(ctx, migration_step)

    image_name = get_docker_image_tag(ctx, odoo_version)
    container_name = get_docker_container_name(ctx, migration_step)
    logger.info(
        "Launching Odoo Docker container named %s based on image '%s'."
        % (container_name, image_name)
    )
    container = client.containers.run(
        image_name,
        name=container_name,
        command=command,
        ports={"8069": 8069, "5432": 5432},
        volumes=["%s:/container_env/" % (folder_path)],
        links={"db": "db"},
        detach=True,
        auto_remove=True,
    )
    logger.info("Container Launched. Command executed : %s" % command)
    return container


def kill_odoo(ctx, migration_step: dict):
    client = docker.from_env()
    containers = client.containers.list(
        all=True,
        filters={"name": get_docker_container_name(ctx, migration_step)},
    )
    for container in containers:
        logger.info(
            "Stop container %s, based on image '%s'."
            % (container.name, ",".join(container.image.tags))
        )
        container.stop()
