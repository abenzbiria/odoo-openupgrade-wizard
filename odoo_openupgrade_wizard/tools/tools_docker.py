import docker
from loguru import logger


def get_docker_client():
    return docker.from_env()


def pull_image(image_name):
    client = get_docker_client()
    client.images.pull(image_name)


def build_image(path, tag, buildargs={}):
    logger.debug(
        "Building image named based on %s/Dockerfile."
        " This can take a big while ..." % (path)
    )
    debug_docker_command = "docker build %s --tag %s" % (path, tag)
    for arg_name, arg_value in buildargs.items():
        debug_docker_command += f"\\\n --build-arg {arg_name}={arg_value}"

    logger.debug("DOCKER COMMAND:\n\n%s\n" % debug_docker_command)
    docker_client = get_docker_client()
    image = docker_client.images.build(
        path=str(path),
        tag=tag,
        buildargs=buildargs,
    )
    logger.debug("Image build.")
    return image


def run_container(
    image_name,
    container_name,
    command=None,
    ports={},
    volumes={},
    environments={},
    links={},
    detach=False,
    auto_remove=False,
):
    client = get_docker_client()
    if not client.images.list(filters={"reference": image_name}):
        raise Exception(
            "The image %s is not available on your system."
            " Did you run 'odoo-openupgrade-wizard docker-build' ?"
            % image_name
        )

    logger.debug("Launching Docker container named %s ..." % (image_name))
    debug_docker_command = "docker run --name %s\\\n" % (container_name)

    for k, v in ports.items():
        debug_docker_command += " --publish {k}:{v}\\\n".format(k=k, v=v)
    for k, v in volumes.items():
        debug_docker_command += " --volume {k}:{v}\\\n".format(
            k=str(k), v=str(v)
        )
    for k, v in environments.items():
        debug_docker_command += " --env {k}={v}\\\n".format(k=k, v=v)
    for k, v in links.items():
        debug_docker_command += " --link {k}:{v}\\\n".format(k=k, v=v)
    if auto_remove:
        debug_docker_command += " --rm"
    if detach:
        debug_docker_command += " --detach"
    debug_docker_command += " %s" % (image_name)
    if command:
        debug_docker_command += " \\\n%s" % (command)
    logger.debug("DOCKER COMMAND:\n%s" % debug_docker_command)

    container = client.containers.run(
        image_name,
        name=container_name,
        command=command,
        ports={x: y for y, x in ports.items()},
        volumes=[str(k) + ":" + str(v) for k, v in volumes.items()],
        environment=environments,
        links=links,
        detach=detach,
        auto_remove=auto_remove,
    )
    if detach:
        logger.debug("Container %s launched." % image_name)
    elif auto_remove:
        logger.debug("Container closed.")

    return container


def exec_container(container, command):
    debug_docker_command = "docker exec %s" % (container.name)
    debug_docker_command += " \\\n%s" % (command)
    logger.debug("DOCKER COMMAND:\n%s" % debug_docker_command)
    docker_result = container.exec_run(command)
    if docker_result.exit_code != 0:
        raise Exception(
            "The command failed in the container %s.\n"
            "- Command : %s\n"
            "- Exit Code : %d\n"
            "- Output: %s"
            % (
                container.name,
                command,
                docker_result.exit_code,
                docker_result.output,
            )
        )
    return docker_result


def kill_container(container_name):
    client = get_docker_client()

    try:
        containers = client.containers.list(
            all=True,
            filters={"name": container_name},
        )
    except docker.errors.NotFound as err:
        logger.debug(f"Cannot kill container {container_name}: " + str(err))
        containers = []

    for container in containers:
        if container.status != "exited":
            logger.debug(
                "Stop container %s, based on image '%s'."
                % (container.name, ",".join(container.image.tags))
            )
            try:
                container.stop()
            except docker.errors.NotFound as err:
                logger.debug(
                    f"Cannot kill container {container.name}: " + str(err)
                )

        # TODO, we should here filter by name
        # but filters={"name": container_name}
        # doesn't work...
        client.containers.prune()
