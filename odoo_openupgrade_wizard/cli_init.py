from pathlib import Path

import click

from odoo_openupgrade_wizard import templates
from odoo_openupgrade_wizard.configuration_version_dependant import (
    get_odoo_versions,
    get_release_options,
)
from odoo_openupgrade_wizard.tools_odoo import get_odoo_env_path
from odoo_openupgrade_wizard.tools_system import (
    ensure_file_exists_from_template,
    ensure_folder_exists,
)


@click.command()
@click.option(
    "--project-name",
    required=True,
    prompt=True,
    type=str,
    help="Name of your project without spaces neither special"
    " chars or uppercases.  exemple 'my-customer-9-12'."
    " This will be used to tag with a friendly"
    " name the odoo docker images.",
)
@click.option(
    "--initial-release",
    required=True,
    prompt=True,
    type=click.Choice(get_release_options("initial")),
)
@click.option(
    "--final-release",
    required=True,
    prompt=True,
    type=click.Choice(get_release_options("final")),
)
@click.option(
    "--extra-repository",
    "extra_repository_list",
    # TODO, add a callback to check the quality of the argument
    help="Coma separated extra repositories to use in the odoo environment."
    "Ex: 'OCA/web,OCA/server-tools,GRAP/grap-odoo-incubator'",
)
@click.pass_context
def init(
    ctx, project_name, initial_release, final_release, extra_repository_list
):
    """Initialize OpenUpgrade Wizard Environment based on the initial and
    the final release of Odoo you want to migrate.
    """

    # Handle arguments
    if extra_repository_list:
        extra_repositories = extra_repository_list.split(",")
    else:
        extra_repositories = []

    orgs = {x: [] for x in set([x.split("/")[0] for x in extra_repositories])}
    for extra_repository in extra_repositories:
        org, repo = extra_repository.split("/")
        orgs[org].append(repo)

    # 1. Compute Odoo versions
    odoo_versions = get_odoo_versions(
        float(initial_release), float(final_release)
    )

    # 2. Compute Migration Steps

    # Create initial first step
    steps = [
        {
            "name": 1,
            "action": "update",
            "release": odoo_versions[0]["release"],
            "complete_name": "step_01__update__%s"
            % (odoo_versions[0]["release"]),
        }
    ]

    # Add all upgrade steps
    count = 2
    for odoo_version in odoo_versions[1:]:
        steps.append(
            {
                "name": count,
                "action": "upgrade",
                "release": odoo_version["release"],
                "complete_name": "step_%s__upgrade__%s"
                % (str(count).rjust(2, "0"), odoo_version["release"]),
            }
        )
        count += 1

    # add final update step
    if len(odoo_versions) > 1:
        steps.append(
            {
                "name": count,
                "action": "update",
                "release": odoo_versions[-1]["release"],
                "complete_name": "step_%s__update__%s"
                % (str(count).rjust(2, "0"), odoo_versions[-1]["release"]),
            }
        )

    # 3. ensure src folder exists
    ensure_folder_exists(ctx.obj["src_folder_path"])

    # 4. ensure filestore folder exists
    ensure_folder_exists(
        ctx.obj["filestore_folder_path"], mode="777", git_ignore_content=True
    )

    # 5. ensure postgres data folder exists
    ensure_folder_exists(
        ctx.obj["postgres_folder_path"].parent,
        mode="777",
        git_ignore_content=True,
    )
    ensure_folder_exists(
        ctx.obj["postgres_folder_path"],
        mode="777",
    )

    # 6. ensure main configuration file exists
    ensure_file_exists_from_template(
        ctx.obj["config_file_path"],
        templates.CONFIG_YML_TEMPLATE,
        project_name=project_name,
        steps=steps,
        odoo_versions=odoo_versions,
    )

    # 7. Ensure module list file exists
    ensure_file_exists_from_template(
        ctx.obj["module_file_path"],
        templates.MODULES_CSV_TEMPLATE,
        project_name=project_name,
        steps=steps,
        odoo_versions=odoo_versions,
    )

    # 8. Create one folder per version and add files
    for odoo_version in odoo_versions:
        # Create main path for each version
        path_version = get_odoo_env_path(ctx, odoo_version)
        ensure_folder_exists(path_version)

        # Create python requirements file
        ensure_file_exists_from_template(
            path_version / Path("python_requirements.txt"),
            templates.PYTHON_REQUIREMENTS_TXT_TEMPLATE,
            python_libraries=odoo_version["python_libraries"],
        )

        # Create debian requirements file
        ensure_file_exists_from_template(
            path_version / Path("debian_requirements.txt"),
            templates.DEBIAN_REQUIREMENTS_TXT_TEMPLATE,
        )

        # Create odoo config file
        ensure_file_exists_from_template(
            path_version / Path("odoo.cfg"),
            templates.ODOO_CONFIG_TEMPLATE,
        )

        # Create repos.yml file for gitaggregate tools
        ensure_file_exists_from_template(
            path_version / Path("repos.yml"),
            templates.REPO_YML_TEMPLATE,
            odoo_version=odoo_version,
            orgs=orgs,
        )

        # Create Dockerfile file
        ensure_file_exists_from_template(
            path_version / Path("Dockerfile"),
            templates.DOCKERFILE_TEMPLATE,
            odoo_version=odoo_version,
        )

        # Create 'src' folder that will contain all the odoo code
        ensure_folder_exists(
            path_version / Path("src"), git_ignore_content=True
        )

    # 9. Create one folder per step and add files
    ensure_folder_exists(ctx.obj["script_folder_path"])

    for step in steps:
        step_path = ctx.obj["script_folder_path"] / step["complete_name"]
        ensure_folder_exists(step_path)

        ensure_file_exists_from_template(
            step_path / Path("pre-migration.sql"),
            templates.PRE_MIGRATION_SQL_TEMPLATE,
        )

        ensure_file_exists_from_template(
            step_path / Path("post-migration.py"),
            templates.POST_MIGRATION_PY_TEMPLATE,
        )
