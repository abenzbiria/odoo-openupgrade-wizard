import click

from odoo_openupgrade_wizard.tools_docker import get_docker_client


@click.command()
@click.pass_context
def test_dev(ctx):
    client = get_docker_client()
    client.containers.list(filters={"name": "db"})[0]
