import click
import docker
import dockerpty


@click.command()
@click.pass_context
def test(ctx):
    client = docker.Client()
    container = client.create_container(
        image="busybox:latest",
        stdin_open=True,
        tty=True,
        command="/bin/sh",
    )

    dockerpty.start(client, container)
