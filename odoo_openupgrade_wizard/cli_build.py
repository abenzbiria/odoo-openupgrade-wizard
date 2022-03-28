import click

from odoo_openupgrade_wizard.configuration_version_dependant import (
    _get_repo_file,
)
from odoo_openupgrade_wizard.tools_system import (
    create_virtualenv,
    ensure_folder_exists,
    git_aggregate,
)


@click.command()
@click.pass_context
def build(ctx):
    """
    Build OpenUpgrade Wizard Environment:
    - gitaggregate all the repositories
    - build virtualenv (TODO)
    """

    # distinct_versions = list(set(x["version"] for x in series))

    for step in ctx.obj["config"]["migration_steps"]:
        # 1. Create main folder for the odoo version
        ensure_folder_exists(step["local_path"], mode="777")

        # 2. Create virtual environment
        create_virtualenv(step["local_path"], step["python"])

        # 3. gitaggregate source code
        git_aggregate(step["local_path"], _get_repo_file(ctx, step))
