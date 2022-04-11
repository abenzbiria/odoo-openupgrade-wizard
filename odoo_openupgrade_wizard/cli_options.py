import click


def releases_options(function):
    function = click.option(
        "--releases",
        type=str,
        help="Coma-separated values of odoo releases for which"
        " you want to perform the operation.",
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


def step_options(function):
    function = click.option(
        "--step",
        required=True,
        prompt=True,
        type=str,
        help="Migration step for which you want to perform the operation.",
    )(function)
    return function


def get_migration_step_from_options(ctx, step_arg):
    step = float(step_arg)
    for migration_step in ctx.obj["config"]["migration_steps"]:
        if migration_step["name"] == step:
            return migration_step
    # TODO, improve exception
    raise Exception
