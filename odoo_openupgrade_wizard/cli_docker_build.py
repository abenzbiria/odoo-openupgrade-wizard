import click
import docker
from loguru import logger

from odoo_openupgrade_wizard.cli_options import (
    get_odoo_versions_from_options,
    releases_options,
)
from odoo_openupgrade_wizard.configuration_version_dependant import (
    get_docker_image_tag,
    get_odoo_env_path,
)


@click.command()
@releases_options
@click.pass_context
def docker_build(ctx, releases):
    """Build Odoo Docker Images. (One image per release)"""

    docker_client = docker.from_env()

    for odoo_version in get_odoo_versions_from_options(ctx, releases):
        logger.info(
            "Building Odoo docker image for release '%s'. "
            "This can take a while..." % (odoo_version["release"])
        )
        image = docker_client.images.build(
            path=str(get_odoo_env_path(ctx, odoo_version)),
            tag=get_docker_image_tag(ctx, odoo_version),
        )
        logger.info("Docker Image build. '%s'" % image[0].tags[0])
