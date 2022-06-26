from pathlib import Path

import click

from odoo_openupgrade_wizard.configuration_version_dependant import (
    get_odoo_versions,
    get_python_libraries,
    get_python_major_version,
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
    """Initialize OpenUpgrade Wizard Environment based on the initial and
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

    # 2. Compute Migration Steps

    # Create initial first step
    steps = [
        {
            "name": 1,
            "execution_context": "regular",
            "version": odoo_versions[0],
            "complete_name": "step_01__update__%s" % (odoo_versions[0]),
        }
    ]

    # Add all upgrade steps
    step_nbr = 2
    for odoo_version in odoo_versions[1:]:
        steps.append(
            {
                "name": step_nbr,
                "execution_context": "openupgrade",
                "version": odoo_version,
                "complete_name": "step_%s__upgrade__%s"
                % (str(step_nbr).rjust(2, "0"), odoo_version),
            }
        )
        step_nbr += 1

    # add final update step
    if len(odoo_versions) > 1:
        steps.append(
            {
                "name": step_nbr,
                "execution_context": "regular",
                "version": odoo_versions[-1],
                "complete_name": "step_%s__update__%s"
                % (str(step_nbr).rjust(2, "0"), odoo_versions[-1]),
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
        "config.yml.j2",
        project_name=project_name,
        steps=steps,
        odoo_versions=odoo_versions,
    )

    # 7. Ensure module list file exists
    ensure_file_exists_from_template(
        ctx.obj["module_file_path"],
        "modules.csv.j2",
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
            "odoo/python_requirements.txt.j2",
            python_libraries=get_python_libraries(odoo_version),
        )

        # Create debian requirements file
        ensure_file_exists_from_template(
            path_version / Path("debian_requirements.txt"),
            "odoo/debian_requirements.txt.j2",
        )

        # Create odoo config file
        ensure_file_exists_from_template(
            path_version / Path("odoo.cfg"),
            "odoo/odoo.cfg.j2",
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
            "odoo/Dockerfile.j2",
            odoo_version=odoo_version,
            python_major_version=get_python_major_version(odoo_version),
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
            "scripts/pre-migration.sql.j2",
        )

        ensure_file_exists_from_template(
            step_path / Path("post-migration.py"),
            "scripts/post-migration.py.j2",
        )
