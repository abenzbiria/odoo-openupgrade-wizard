# from pathlib import Path

# List of the series of odoo
# python version is defined, based on the OCA CI.
# https://github.com/OCA/oca-addons-repo-template/blob/master/src/.github/workflows/%7B%25%20if%20ci%20%3D%3D%20'GitHub'%20%25%7Dtest.yml%7B%25%20endif%20%25%7D.jinja
_ODOO_VERSION_TEMPLATES = [
    {
        "release": 8.0,
        "python_major_version": "python2",
        "python_libraries": ["openupgradelib"],
    },
    {
        "release": 9.0,
        "python_major_version": "python2",
        "python_libraries": ["openupgradelib"],
    },
    {
        "release": 10.0,
        "python_major_version": "python2",
        "python_libraries": ["openupgradelib"],
    },
    {
        "release": 11.0,
        "python_major_version": "python3",
        "python_libraries": ["openupgradelib"],
    },
    {
        "release": 12.0,
        "python_major_version": "python3",
        "python_libraries": ["openupgradelib"],
    },
    {
        "release": 13.0,
        "python_major_version": "python3",
        "python_libraries": ["openupgradelib"],
    },
    {
        "release": 14.0,
        "python_major_version": "python3",
        "python_libraries": ["openupgradelib"],
    },
    {
        "release": 15.0,
        "python_major_version": "python3",
        "python_libraries": ["openupgradelib"],
    },
]


def get_release_options(mode: str) -> list:
    """Get options available for release click argument.
    Arguments:
        mode: Possible value 'initial', 'final'
    Return:
        list of string.
    Exemple:
        ['9.0', '10.0', '11.0']
    """
    releases_list = [str(x["release"]) for x in _ODOO_VERSION_TEMPLATES]
    if mode == "initial":
        releases_list = releases_list[:-1]
    if mode == "final":
        releases_list = releases_list[1:]
    return releases_list


def get_odoo_versions(initial_release: float, final_release: float) -> list:
    """Return a list of odoo versions from the initial release to the final
    release
    """
    result = []
    for version_template in _ODOO_VERSION_TEMPLATES:
        if (
            version_template["release"] >= initial_release
            and version_template["release"] <= final_release
        ):
            result.append(version_template)
    return result


# def _get_repo_file(ctx, step):
#     return ctx.obj["repo_folder_path"] / Path("%s.yml" % (step["version"]))


def get_odoo_env_path(ctx, odoo_version):
    folder_name = "env_%s" % str(odoo_version["release"]).rjust(4, "0")
    return ctx.obj["src_folder_path"] / folder_name
