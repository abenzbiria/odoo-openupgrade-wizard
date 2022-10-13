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
from odoo_openupgrade_wizard.tools.tools_system import get_local_user_id


@click.command()
@versions_options
@click.pass_context
def docker_build(ctx, versions):
    """Build Odoo Docker Images and pull Postgres image"""

    # Pull DB image
    logger.info(
        "Pulling the postgresql docker image. This can take a while..."
    )
    pull_image(ctx.obj["config"]["postgres_image_name"])

    # Build images for each odoo version
    for odoo_version in get_odoo_versions_from_options(ctx, versions):

        odoo_requirement_file_path = (
            get_odoo_env_path(ctx, odoo_version) / "src/odoo/requirements.txt"
        )
        if not odoo_requirement_file_path.exists():
            logger.error(
                "Building Odoo docker image for version {odoo_version}, "
                "because file {odoo_requirement_file_path} cannot be found. "
                "Have your run the get-code command ?",
                odoo_version=odoo_version,
                odoo_requirement_file_path=odoo_requirement_file_path,
            )
            continue

        logger.info(
            "Building Odoo docker image for version '%s'. "
            "This can take a while..." % (odoo_version)
        )
        image = build_image(
            get_odoo_env_path(ctx, odoo_version),
            get_docker_image_tag(ctx, odoo_version),
            {"LOCAL_USER_ID": str(get_local_user_id())},
        )
        logger.info("Docker Image build. '%s'" % image[0].tags[0])
