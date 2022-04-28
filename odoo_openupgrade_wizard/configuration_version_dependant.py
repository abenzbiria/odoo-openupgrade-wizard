from pathlib import Path

# See : https://github.com/OCA/openupgradelib/issues/248
# https://github.com/OCA/openupgradelib/issues/288
_LEGACY_OPENUPGRADELIB = (
    "git+https://github.com/OCA/openupgradelib.git"
    "@ed01555b8ae20f66b3af178c8ecaf6edd110ce75#egg=openupgradelib"
)


# List of the series of odoo
# python version is defined, based on the OCA CI.
# https://github.com/OCA/oca-addons-repo-template/blob/master/src/.github/workflows/%7B%25%20if%20ci%20%3D%3D%20'GitHub'%20%25%7Dtest.yml%7B%25%20endif%20%25%7D.jinja
_ODOO_VERSION_TEMPLATES = [
    {
        "release": 8.0,
        "python_major_version": "python2",
        "python_libraries": [_LEGACY_OPENUPGRADELIB],
    },
    {
        "release": 9.0,
        "python_major_version": "python2",
        "python_libraries": [_LEGACY_OPENUPGRADELIB],
    },
    {
        "release": 10.0,
        "python_major_version": "python2",
        "python_libraries": [_LEGACY_OPENUPGRADELIB],
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


def get_odoo_run_command(migration_step: dict) -> str:
    """Return the name of the command to execute, depending on the migration
    step. (odoo-bin, odoo.py, etc...)"""
    if migration_step["release"] >= 9.0:
        return "odoo-bin"

    return "odoo.py"


def get_odoo_folder(migration_step: dict) -> str:
    """return the main odoo folder, depending on the migration step.
    (./src/odoo, ./src/openupgrade, ...)"""

    if migration_step["action"] == "update":
        return "src/odoo"

    if migration_step["release"] >= 14.0:
        return "src/odoo"

    return "src/openupgrade"


def get_base_module_folder(migration_step: dict) -> str:
    """return the name of the folder (odoo, openerp, etc...)
    where the 'base' module is, depending on the migration_step"""
    if migration_step["release"] >= 10.0:
        return "odoo"

    return "openerp"


def skip_addon_path(migration_step: dict, path: Path) -> bool:
    # if repo.yml contains both odoo and openupgrade repo
    # we skip one of them (before the refactoring)
    return (
        str(path).endswith("/src/odoo")
        or str(path).endswith("src/openupgrade")
    ) and migration_step["release"] < 14.0
