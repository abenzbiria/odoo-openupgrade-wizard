# from pathlib import Path

import click

from odoo_openupgrade_wizard.tools_system import ensure_folder_exists


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

        # # 2. gitaggregate source code
        # repo_file = ctx.obj["repo_folder_path"] / Path(
        #     "%s.yml" % (step["version"])
        # )
