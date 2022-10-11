import click
from loguru import logger

from odoo_openupgrade_wizard.cli.cli_options import (
    get_odoo_versions_from_options,
    versions_options,
)
from odoo_openupgrade_wizard.tools.tools_odoo import get_odoo_env_path
from odoo_openupgrade_wizard.tools.tools_system import execute_check_output


@click.command()
@versions_options
@click.pass_context
def pull_submodule(ctx, versions):
    """Pull submodule that contains repos.yml file, if define in config.yml"""

    for odoo_version in get_odoo_versions_from_options(ctx, versions):
        version_cfg = (
            ctx.obj["config"]["odoo_version_settings"][odoo_version] or {}
        )
        if version_cfg.get("repo_url"):
            logger.info(
                f"Pull repos.yml from git repository"
                f" for version {odoo_version} ..."
            )
            submodule_path = (
                get_odoo_env_path(ctx, odoo_version) / "repo_submodule"
            )
            if not submodule_path.exists():
                execute_check_output(
                    [
                        "git",
                        "submodule",
                        "add",
                        "-b",
                        str(version_cfg["repo_branch"]),
                        version_cfg["repo_url"],
                        str(submodule_path),
                    ]
                )
            else:
                execute_check_output(
                    [
                        "git",
                        "pull",
                        "origin",
                        str(version_cfg["repo_branch"]),
                        "--rebase",
                    ],
                    working_directory=submodule_path,
                )
        else:
            logger.warning(
                f"No submodule configuration found"
                f" for version {odoo_version} ..."
            )
