import os
from pathlib import Path

from loguru import logger

from odoo_openupgrade_wizard.tools_docker import get_docker_client
from odoo_openupgrade_wizard.tools_system import get_script_folder


def get_postgres_container():
    client = get_docker_client()
    containers = client.containers.list(filters={"name": "db"})
    if not containers:
        raise Exception("Postgresql container not found with name 'db'.")
    return containers[0]


def execute_sql_request(request, database="postgres"):
    container = get_postgres_container()
    docker_command = (
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
    docker_result = container.exec_run(docker_command)
    if docker_result.exit_code != 0:
        raise Exception(
            "Request %s failed on database %s. Exit Code : %d"
            % (request, database, docker_result.exit_code)
        )
    lines = docker_result.output.decode("utf-8").split("\n")
    result = []
    for line in lines:
        if not line:
            continue
        result.append([x.strip() for x in line.split("|")])
    return result


def ensure_database(database: str, state="present"):
    """
    - Connect to postgres container.
    - Check if the database exist.
    - if doesn't exists and state == 'present', create it.
    - if exists and state == 'absent', drop it.
    """
    request = "select datname FROM pg_database WHERE datistemplate = false;"

    result = execute_sql_request(request)

    if state == "present":
        if [database] in result:
            return

        logger.info("Create database '%s' ..." % database)
        request = "CREATE DATABASE {database} owner odoo;".format(
            database=database
        )
        execute_sql_request(request)
    else:
        if [database] not in result:
            return

        logger.info("Drop database '%s' ..." % database)
        request = "DROP DATABASE {database};".format(database=database)
        execute_sql_request(request)


def execute_sql_files_pre_migration(
    ctx, database: str, migration_step: dict, sql_files: list = []
):
    if not sql_files:
        script_folder = get_script_folder(ctx, migration_step)

        sql_files = [
            script_folder / Path(f)
            for f in os.listdir(script_folder)
            if os.path.isfile(os.path.join(script_folder, f))
            and f[-3:] == ".sql"
        ]
        sql_files = sorted(sql_files)
