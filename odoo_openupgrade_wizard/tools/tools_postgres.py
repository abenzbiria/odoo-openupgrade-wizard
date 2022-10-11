import os
import time
from pathlib import Path

import docker
from loguru import logger

from odoo_openupgrade_wizard.tools.tools_docker import (
    exec_container,
    get_docker_client,
    run_container,
)
from odoo_openupgrade_wizard.tools.tools_system import get_script_folder


def get_postgres_container(ctx):
    client = get_docker_client()
    image_name = ctx.obj["config"]["postgres_image_name"]
    container_name = ctx.obj["config"]["postgres_container_name"]
    volume_name = ctx.obj["config"]["postgres_volume_name"]

    # Check if container exists
    containers = client.containers.list(
        all=True, filters={"name": container_name}
    )
    if containers:
        container = containers[0]
        if container.status == "exited":
            logger.warning(
                "Found container %s in a exited status. Removing it..."
                % container_name
            )
            container.remove()
        else:
            return container

    # Check if volume exists
    try:
        client.volumes.get(volume_name)
        logger.debug("Recovering existing postgres volume: %s" % volume_name)
    except docker.errors.NotFound:
        logger.info("Creating Postgres volume: %s" % volume_name)
        client.volumes.create(volume_name)

    command = None
    postgres_extra_settings = ctx.obj["config"].get("postgres_extra_settings")
    if postgres_extra_settings:
        command = "postgres"
        for key, value in postgres_extra_settings.items():
            command += f" -c {key}={value}"

    logger.info("Launching Postgres Container. (Image %s)" % image_name)
    container = run_container(
        image_name,
        container_name,
        command=command,
        environments={
            "POSTGRES_USER": "odoo",
            "POSTGRES_PASSWORD": "odoo",
            "POSTGRES_DB": "postgres",
            "PGDATA": "/var/lib/postgresql/data/pgdata",
        },
        volumes={
            # Data volume
            volume_name: "/var/lib/postgresql/data/pgdata/",
            # main folder path (to pass files)
            ctx.obj["env_folder_path"].absolute(): "/env/",
        },
        detach=True,
    )
    # TODO, improve me.
    # Postgres container doesn't seems available immediately.
    # check in odoo container, i remember that there is
    # some script to do the job
    time.sleep(5)
    return container


def execute_sql_file(ctx, database, sql_file):
    container = get_postgres_container(ctx)

    # Recreate relative path to make posible to
    # call psql in the container
    if str(ctx.obj["env_folder_path"]) not in str(sql_file):
        raise Exception(
            "The SQL file %s is not in the"
            " main folder %s available"
            " in the postgres container."
            % (sql_file, ctx.obj["env_folder_path"])
        )
    relative_path = Path(
        str(sql_file).replace(str(ctx.obj["env_folder_path"]), ".")
    )

    container_path = Path("/env/") / relative_path
    command = (
        "psql --username=odoo --dbname={database} --file {file_path}"
    ).format(database=database, file_path=container_path)
    logger.info(
        "Executing the script '%s' in postgres container"
        " on database %s" % (relative_path, database)
    )
    exec_container(container, command)


def execute_sql_request(ctx, request, database="postgres"):
    container = get_postgres_container(ctx)
    command = (
        "psql"
        " --username=odoo"
        " --dbname={database}"
        " --tuples-only"
        ' --command "{request}"'
    ).format(database=database, request=request)
    logger.debug(
        "Executing the following command in postgres container"
        " on database %s \n %s" % (database, request)
    )
    docker_result = exec_container(container, command)

    lines = docker_result.output.decode("utf-8").split("\n")
    result = []
    for line in lines:
        if not line:
            continue
        result.append([x.strip() for x in line.split("|")])
    return result


def ensure_database(ctx, database: str, state="present"):
    """
    - Connect to postgres container.
    - Check if the database exist.
    - if doesn't exists and state == 'present', create it.
    - if exists and state == 'absent', drop it.
    """
    request = "select datname FROM pg_database WHERE datistemplate = false;"

    result = execute_sql_request(ctx, request)

    if state == "present":
        if [database] in result:
            return

        logger.info("Create database '%s' ..." % database)
        request = "CREATE DATABASE {database} owner odoo;".format(
            database=database
        )
        execute_sql_request(ctx, request)
    else:
        if [database] not in result:
            return

        logger.info("Drop database '%s' ..." % database)
        request = "DROP DATABASE {database};".format(database=database)
        execute_sql_request(ctx, request)


def execute_sql_files_pre_migration(
    ctx, database: str, migration_step: dict, sql_files: list = []
):
    ensure_database(ctx, database, state="present")
    if not sql_files:
        script_folder = get_script_folder(ctx, migration_step)
        sql_files = [
            script_folder / Path(f)
            for f in os.listdir(script_folder)
            if os.path.isfile(os.path.join(script_folder, f))
            and f[-4:] == ".sql"
        ]
        sql_files = sorted(sql_files)

    for sql_file in sql_files:
        execute_sql_file(ctx, database, sql_file)
