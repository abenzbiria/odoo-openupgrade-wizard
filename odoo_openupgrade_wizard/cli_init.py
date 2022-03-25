from pathlib import Path

import click
from jinja2 import Template
from loguru import logger
from plumbum.cmd import mkdir

from odoo_openupgrade_wizard.configuration_version_dependant import (
    _get_odoo_version_str_list,
    _get_odoo_versions,
)
from odoo_openupgrade_wizard.templates import (
    _CONFIG_YML_TEMPLATE,
    _POST_MIGRATION_PY_TEMPLATE,
    _PRE_MIGRATION_SQL_TEMPLATE,
    _REPO_YML_TEMPLATE,
    _REQUIREMENTS_TXT_TEMPLATE,
)


@click.command()
@click.option(
    "-iv",
    "--initial-version",
    required=True,
    prompt=True,
    type=click.Choice(_get_odoo_version_str_list("initial")),
)
@click.option(
    "-fv",
    "--final-version",
    required=True,
    prompt=True,
    type=click.Choice(_get_odoo_version_str_list("final")),
)
@click.option(
    "-er",
    "--extra-repository",
    "extra_repository_list",
    # TODO, add a callback to check the quality of the argument
    help="Coma separated extra repositories to use in the odoo environment."
    "Ex: 'OCA/web,OCA/server-tools,GRAP/grap-odoo-incubator'",
)
@click.pass_context
def init(ctx, initial_version, final_version, extra_repository_list):
    """
    Initialize OpenUpgrade Wizard Environment based on the initial and
    the final version of Odoo you want to migrate.
    """
    # 1. create src directory if not exists
    if not ctx.obj["src_folder_path"].exists():
        logger.info("Creating folder '%s' ..." % (ctx.obj["src_folder_path"]))
        mkdir(["--mode", "777", ctx.obj["src_folder_path"]])

    # 2. create filestore directory if not exists
    if not ctx.obj["filestore_folder_path"].exists():
        logger.info(
            "Creating folder '%s' ..." % (ctx.obj["filestore_folder_path"])
        )
        mkdir(["--mode", "777", ctx.obj["filestore_folder_path"]])

    # 3. Create main config file
    series = _get_odoo_versions(float(initial_version), float(final_version))

    # Create initial first step
    steps = [series[0].copy()]
    steps[0].update(
        {
            "name": "step_1",
            "action": "update",
            "complete_name": "step_1__update__%s" % (steps[0]["version"]),
        }
    )

    # Add all upgrade steps
    count = 1
    for serie in series[1:]:
        steps.append(serie.copy())
        steps[count].update(
            {
                "name": "step_%d" % (count + 1),
                "action": "upgrade",
                "complete_name": "step_%d__upgrade__%s"
                % (count + 1, serie["version"]),
            }
        )
        count += 1

    # add final update step
    steps.append(series[-1].copy())
    steps[-1].update(
        {
            "name": "step_%d" % (count + 1),
            "action": "update",
            "complete_name": "step_%d__update__%s"
            % (count + 1, steps[-1]["version"]),
        }
    )

    template = Template(_CONFIG_YML_TEMPLATE)
    output = template.render(steps=steps)
    with open(ctx.obj["config_file_path"], "w") as f:
        logger.info(
            "Creating configuration file '%s' ..."
            % (ctx.obj["config_file_path"])
        )
        f.write(output)
        f.close()

    distinct_versions = list(set(x["version"] for x in series))

    # 4. Create Repo folder and files
    if not ctx.obj["repo_folder_path"].exists():
        logger.info("Creating folder '%s' ..." % (ctx.obj["repo_folder_path"]))
        mkdir([ctx.obj["repo_folder_path"]])

    extra_repositories = extra_repository_list.split(",")

    orgs = {x: [] for x in set([x.split("/")[0] for x in extra_repositories])}
    for extra_repository in extra_repositories:
        org, repo = extra_repository.split("/")
        orgs[org].append(repo)

    for version in distinct_versions:
        template = Template(_REPO_YML_TEMPLATE)
        output = template.render(version=version, orgs=orgs)
        file_name = ctx.obj["repo_folder_path"] / Path("%s.yml" % (version))
        with open(file_name, "w") as f:
            logger.info("Creating Repo file '%s' ..." % (file_name))
            f.write(output)
            f.close()

    # 5. Create Requirements folder and files
    if not ctx.obj["requirement_folder_path"].exists():
        logger.info(
            "Creating folder '%s' ..." % (ctx.obj["requirement_folder_path"])
        )
        mkdir([ctx.obj["requirement_folder_path"]])

    for serie in series:
        template = Template(_REQUIREMENTS_TXT_TEMPLATE)
        output = template.render(python_libraries=serie["python_libraries"])
        file_name = ctx.obj["requirement_folder_path"] / Path(
            "%s_requirements.txt" % (serie["version"])
        )
        with open(file_name, "w") as f:
            logger.info("Creating Requirements file '%s' ..." % (file_name))
            f.write(output)
            f.close()

    # 6. Create Scripts folder and files
    if not ctx.obj["script_folder_path"].exists():
        logger.info(
            "Creating folder '%s' ..." % (ctx.obj["script_folder_path"])
        )
        mkdir([ctx.obj["script_folder_path"]])

    for step in steps:
        step_path = ctx.obj["script_folder_path"] / step["complete_name"]
        if not step_path.exists():
            logger.info("Creating folder '%s' ..." % (step_path))
            mkdir([step_path])
        template = Template(_PRE_MIGRATION_SQL_TEMPLATE)
        output = template.render()
        file_name = step_path / Path("pre-migration.sql")
        with open(file_name, "w") as f:
            logger.info(
                "Creating pre-migration.sql file '%s' ..." % (file_name)
            )
            f.write(output)
            f.close()
        template = Template(_POST_MIGRATION_PY_TEMPLATE)
        output = template.render()
        file_name = step_path / Path("post-migration.py")
        with open(file_name, "w") as f:
            logger.info(
                "Creating post-migration.py file '%s' ..." % (file_name)
            )
            f.write(output)
            f.close()
