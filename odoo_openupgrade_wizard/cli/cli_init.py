from pathlib import Path

import click

from odoo_openupgrade_wizard.configuration_version_dependant import (
    get_odoo_versions,
    get_version_options,
)
from odoo_openupgrade_wizard.tools.tools_odoo import get_odoo_env_path
from odoo_openupgrade_wizard.tools.tools_system import (
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
    "--initial-version",
    required=True,
    prompt=True,
    type=click.Choice(get_version_options("initial")),
)
@click.option(
    "--final-version",
    required=True,
    prompt=True,
    type=click.Choice(get_version_options("final")),
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
    ctx, project_name, initial_version, final_version, extra_repository_list
):
    """Initialize OOW Environment based on the initial and
    the final version of Odoo you want to migrate.
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
        float(initial_version), float(final_version)
    )

    # Compute Migration Steps

    # Create initial Regular step
    steps = [
        {
            "name": 1,
            "execution_context": "regular",
            "version": odoo_versions[0],
            "complete_name": "step_01__regular__%s" % (odoo_versions[0]),
        }
    ]
    # Add all Openupgrade steps
    step_nbr = 2
    for odoo_version in odoo_versions[1:]:
        steps.append(
            {
                "name": step_nbr,
                "execution_context": "openupgrade",
                "version": odoo_version,
                "complete_name": "step_%s__openupgrade__%s"
                % (str(step_nbr).rjust(2, "0"), odoo_version),
            }
        )
        step_nbr += 1

    # add final Regular step
    if len(odoo_versions) > 1:
        steps.append(
            {
                "name": step_nbr,
                "execution_context": "regular",
                "version": odoo_versions[-1],
                "complete_name": "step_%s__regular__%s"
                % (str(step_nbr).rjust(2, "0"), odoo_versions[-1]),
            }
        )

    # Ensure src folder exists
    ensure_folder_exists(ctx.obj["src_folder_path"])

    # Ensure main configuration file exists
    ensure_file_exists_from_template(
        ctx.obj["config_file_path"],
        "config.yml.j2",
        project_name=project_name,
        steps=steps,
        odoo_versions=odoo_versions,
    )

    # Ensure module list file exists
    ensure_file_exists_from_template(
        ctx.obj["module_file_path"],
        "modules.csv.j2",
        project_name=project_name,
        steps=steps,
        odoo_versions=odoo_versions,
    )

    # Create one folder per version and add files
    for odoo_version in odoo_versions:
        # Create main path for each version
        path_version = get_odoo_env_path(ctx, odoo_version)
        ensure_folder_exists(path_version)

        # Create python requirements file
        ensure_file_exists_from_template(
            path_version / Path("extra_python_requirements.txt"),
            "odoo/extra_python_requirements.txt.j2",
        )

        # Create debian requirements file
        ensure_file_exists_from_template(
            path_version / Path("extra_debian_requirements.txt"),
            "odoo/extra_debian_requirements.txt.j2",
        )

        # Create odoo config file
        ensure_file_exists_from_template(
            path_version / Path("odoo.conf"),
            "odoo/odoo.conf.j2",
        )

        # Create repos.yml file for gitaggregate tools
        ensure_file_exists_from_template(
            path_version / Path("repos.yml"),
            "odoo/repos.yml.j2",
            odoo_version=odoo_version,
            orgs=orgs,
        )

        # Create Dockerfile file
        ensure_file_exists_from_template(
            path_version / Path("Dockerfile"),
            f"odoo/{odoo_version}/Dockerfile",
        )

        # Create 'src' folder that will contain all the odoo code
        ensure_folder_exists(
            path_version / Path("src"), git_ignore_content=True
        )

    # Create one folder per step and add files
    ensure_folder_exists(ctx.obj["script_folder_path"])

    for step in steps:
        step_path = ctx.obj["script_folder_path"] / step["complete_name"]
        ensure_folder_exists(step_path)

        ensure_file_exists_from_template(
            step_path / Path("pre-migration.sql"),
            "scripts/pre-migration.sql.j2",
        )

        ensure_file_exists_from_template(
            step_path / Path("post-migration.py"),
            "scripts/post-migration.py.j2",
        )
