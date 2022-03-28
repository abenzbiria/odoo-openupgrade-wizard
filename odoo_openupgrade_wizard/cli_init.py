from pathlib import Path

import click

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
from odoo_openupgrade_wizard.tools_system import (
    ensure_file_exists_from_template,
    ensure_folder_exists,
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

    if extra_repository_list:
        extra_repositories = extra_repository_list.split(",")
    else:
        extra_repositories = []

    # 1. create steps from series given as argument
    series = _get_odoo_versions(float(initial_version), float(final_version))
    distinct_versions = list(set(x["version"] for x in series))

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

    # 2. ensure src folder exists
    ensure_folder_exists(ctx.obj["src_folder_path"], mode="777")

    # 3. ensure filestore folder exists
    ensure_folder_exists(ctx.obj["filestore_folder_path"], mode="777")

    # 4. ensure main configuration file exists
    ensure_file_exists_from_template(
        ctx.obj["config_file_path"], _CONFIG_YML_TEMPLATE, steps=steps
    )

    # 4. Create Repo folder and files
    ensure_folder_exists(ctx.obj["repo_folder_path"])

    orgs = {x: [] for x in set([x.split("/")[0] for x in extra_repositories])}
    for extra_repository in extra_repositories:
        org, repo = extra_repository.split("/")
        orgs[org].append(repo)

    for version in distinct_versions:
        ensure_file_exists_from_template(
            ctx.obj["repo_folder_path"] / Path("%s.yml" % (version)),
            _REPO_YML_TEMPLATE,
            version=version,
            orgs=orgs,
        )

    # 5. Create Requirements folder and files
    ensure_folder_exists(ctx.obj["requirement_folder_path"])

    for serie in series:
        ensure_file_exists_from_template(
            ctx.obj["requirement_folder_path"]
            / Path("%s_requirements.txt" % (serie["version"])),
            _REQUIREMENTS_TXT_TEMPLATE,
            python_libraries=serie["python_libraries"],
        )

    # 6. Create Scripts folder and files
    ensure_folder_exists(ctx.obj["script_folder_path"])

    for step in steps:
        step_path = ctx.obj["script_folder_path"] / step["complete_name"]
        ensure_folder_exists(step_path)

        ensure_file_exists_from_template(
            step_path / Path("pre-migration.sql"),
            _PRE_MIGRATION_SQL_TEMPLATE,
        )

        ensure_file_exists_from_template(
            step_path / Path("post-migration.py"),
            _POST_MIGRATION_PY_TEMPLATE,
        )
