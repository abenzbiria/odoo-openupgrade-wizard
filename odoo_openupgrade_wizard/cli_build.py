# from pathlib import Path

import click
from loguru import logger
from plumbum.cmd import mkdir


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
        if not step["local_path"].exists():
            logger.info("Creating folder '%s' ..." % (step["local_path"]))
            mkdir(["--mode", "777", step["local_path"]])

        # # 2. gitaggregate source code
        # repo_file = ctx.obj["repo_folder_path"] / Path(
        #     "%s.yml" % (step["version"])
        # )
