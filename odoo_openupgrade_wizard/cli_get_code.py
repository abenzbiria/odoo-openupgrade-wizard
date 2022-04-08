import click

from odoo_openupgrade_wizard.configuration_version_dependant import (
    get_odoo_env_path,
)
from odoo_openupgrade_wizard.tools_system import git_aggregate


@click.command()
@click.pass_context
def get_code(ctx):
    """Get code by running gitaggregate command for each release"""

    # TODO, make it modular.
    # For exemple, possibility to aggregate only 9.0 and 11.0 release
    for odoo_version in ctx.obj["config"]["odoo_versions"]:
        folder_path = get_odoo_env_path(ctx, odoo_version)
        repo_file_path = folder_path / "repos.yml"
        git_aggregate(folder_path, repo_file_path)
