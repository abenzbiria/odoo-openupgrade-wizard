import click
from loguru import logger

from odoo_openupgrade_wizard.cli.cli_options import (
    get_odoo_versions_from_options,
    versions_options,
)
from odoo_openupgrade_wizard.tools.tools_docker import build_image, pull_image
from odoo_openupgrade_wizard.tools.tools_odoo import (
    get_docker_image_tag,
    get_odoo_env_path,
)


@click.command()
@versions_options
@click.pass_context
def docker_build(ctx, versions):
    """Build Odoo Docker Images. (One image per version)"""

    # Pull DB image
    pull_image(ctx.obj["config"]["postgres_image_name"])

    # Build images for each odoo version
    for odoo_version in get_odoo_versions_from_options(ctx, versions):
        logger.info(
            "Building Odoo docker image for version '%s'. "
            "This can take a while..." % (odoo_version)
        )
        image = build_image(
            get_odoo_env_path(ctx, odoo_version),
            get_docker_image_tag(ctx, odoo_version),
        )
        logger.info("Docker Image build. '%s'" % image[0].tags[0])
