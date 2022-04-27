import docker
from loguru import logger


def get_docker_client():
    return docker.from_env()


def run_container(
    image_name,
    container_name,
    command=False,
    ports=False,
    volumes=False,
    links=False,
    detach=False,
    auto_remove=False,
):
    client = get_docker_client()

    logger.info("Launching Docker container named %s ..." % (image_name))
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
    if auto_remove:
        debug_docker_command += " --rm"
    if detach:
        debug_docker_command += " --detach"
    debug_docker_command += " %s\\\n" % (image_name)
    debug_docker_command += " %s" % (command)
    logger.debug(debug_docker_command)

    container = client.containers.run(
        image_name,
        name=container_name,
        command=command,
        ports=ports,
        volumes=volumes,
        links=links,
        detach=detach,
        auto_remove=auto_remove,
    )
    if detach:
        logger.info("Container launched.")
    elif auto_remove:
        logger.info("Container closed.")

    return container


def kill_container(container_name):
    client = get_docker_client()
    containers = client.containers.list(
        all=True,
        filters={"name": container_name},
    )
    for container in containers:
        logger.info(
            "Stop container %s, based on image '%s'."
            % (container.name, ",".join(container.image.tags))
        )
        container.stop()
