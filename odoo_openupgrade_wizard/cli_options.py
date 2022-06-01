import click


def releases_options(function):
    function = click.option(
        "-r",
        "--releases",
        type=str,
        help="Coma-separated values of odoo releases for which"
        " you want to perform the operation.",
    )(function)
    return function


def step_option(function):
    function = click.option(
        "-s",
        "--step",
        required=True,
        prompt=True,
        type=int,
        help="Migration step for which you want to perform the operation.",
    )(function)
    return function


def first_step_option(function):
    function = click.option(
        "--first-step",
        type=int,
        help="First step for which to perform the operation",
    )(function)
    return function


def last_step_option(function):
    function = click.option(
        "--last-step",
        type=int,
        help="Last step for which to perform the operation",
    )(function)
    return function


def database_option(function):
    function = click.option(
        "-d",
        "--database",
        type=str,
        help="Odoo Database for which you want to perform the operation.",
    )(function)
    return function


def database_option_required(function):
    function = click.option(
        "-d",
        "--database",
        required=True,
        prompt=True,
        type=str,
        help="Odoo Database for which you want to perform the operation.",
    )(function)
    return function


def get_odoo_versions_from_options(ctx, releases_arg):

    if not releases_arg:
        return ctx.obj["config"]["odoo_versions"]
    else:
        odoo_versions = []
        releases = [float(x) for x in releases_arg.split(",")]
        for odoo_version in ctx.obj["config"]["odoo_versions"]:
            if odoo_version["release"] in releases:
                odoo_versions.append(odoo_version)
        return odoo_versions


def get_migration_step_from_options(ctx, step_arg):
    step = float(step_arg)
    for migration_step in ctx.obj["config"]["migration_steps"]:
        if migration_step["name"] == step:
            return migration_step
    raise ValueError(
        "No migration step found in configuration for step %s" % step_arg
    )


def get_migration_steps_from_options(ctx, first_step_arg, last_step_arg):
    result = []
    if first_step_arg:
        first_step = int(first_step_arg)
    else:
        first_step = ctx.obj["config"]["migration_steps"][0]["name"]
    if last_step_arg:
        last_step = int(last_step_arg)
    else:
        last_step = ctx.obj["config"]["migration_steps"][-1]["name"]
    for migration_step in ctx.obj["config"]["migration_steps"]:
        if migration_step["name"] in list(range(first_step, last_step + 1)):
            result.append(migration_step.copy())
    if result:
        return result

    raise ValueError(
        "Unable to define steps in configuration"
        " from options. (first step %s ; last step %s)"
        % (first_step_arg, last_step_arg)
    )
