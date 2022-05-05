import docker
from loguru import logger


def get_docker_client():
    return docker.from_env()


def build_image(path, tag):
    logger.debug(
        "Building image named based on %s/Dockerfile."
        " This can take a big while ..." % (path)
    )
    debug_docker_command = "docker build %s --tag %s" % (path, tag)
    logger.debug("DOCKER COMMAND:\n %s" % debug_docker_command)
    docker_client = get_docker_client()
    image = docker_client.images.build(
        path=str(path),
        tag=tag,
    )
    logger.debug("Image build.")
    return image


def run_container(
    image_name,
    container_name,
    command=None,
    ports=False,
    volumes=False,
    environments={},
    links={},
    detach=False,
    auto_remove=False,
):
    client = get_docker_client()

    logger.debug("Launching Docker container named %s ..." % (image_name))
    debug_docker_command = "docker run --name %s\\\n" % (container_name)
    if ports:
        for internal_port, host_port in ports.items():
            debug_docker_command += (
                " --publish {host_port}:{internal_port}\\\n".format(
                    internal_port=internal_port, host_port=host_port
                )
            )
    if volumes:
        for volume in volumes:
            external_path, internal_path = volume.split(":")
            debug_docker_command += (
                " --volume {external_path}:{internal_path}\\\n".format(
                    external_path=external_path, internal_path=internal_path
                )
            )
    if links:
        for k, v in links.items():
            debug_docker_command += " --link {k}:{v}\\\n".format(k=k, v=v)
    if environments:
        for k, v in environments.items():
            debug_docker_command += " --env {k}={v}\\\n".format(k=k, v=v)
    if auto_remove:
        debug_docker_command += " --rm"
    if detach:
        debug_docker_command += " --detach"
    debug_docker_command += " %s" % (image_name)
    if command:
        debug_docker_command += " \\\n%s" % (command)
    logger.debug("DOCKER COMMAND:\n %s" % debug_docker_command)

    container = client.containers.run(
        image_name,
        name=container_name,
        command=command,
        ports=ports,
        volumes=volumes,
        environment=environments,
        # environment=[
        #     "POSTGRES_USER=odoo",
        #     "POSTGRES_PASSWORD=odoo",
        #     "POSTGRES_DB=postgres",
        # ],
        links=links,
        detach=detach,
        auto_remove=auto_remove,
    )
    if detach:
        logger.debug("Container %s launched." % image_name)
    elif auto_remove:
        logger.debug("Container closed.")

    return container


def kill_container(container_name):
    client = get_docker_client()
    containers = client.containers.list(
        all=True,
        filters={"name": container_name},
    )
    for container in containers:
        logger.debug(
            "Stop container %s, based on image '%s'."
            % (container.name, ",".join(container.image.tags))
        )
        container.stop()
