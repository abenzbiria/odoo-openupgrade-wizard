import click

from odoo_openupgrade_wizard.cli_options import (
    get_odoo_versions_from_options,
    releases_options,
)
from odoo_openupgrade_wizard.configuration_version_dependant import (
    get_odoo_env_path,
)
from odoo_openupgrade_wizard.tools_system import git_aggregate


@click.command()
@releases_options
@click.pass_context
def get_code(ctx, releases):
    """Get code by running gitaggregate command for each release"""

    for odoo_version in get_odoo_versions_from_options(ctx, releases):
        folder_path = get_odoo_env_path(ctx, odoo_version)
        repo_file_path = folder_path / "repos.yml"
        git_aggregate(folder_path, repo_file_path)
