from pathlib import Path

from loguru import logger

_ODOO_VERSION_TEMPLATES = [
    {
        "release": 8.0,
        "python_major_version": "python2",
        "python_libraries": [],
    },
    {
        "release": 9.0,
        "python_major_version": "python2",
        "python_libraries": ["openupgradelib==2.0.0"],
    },
    {
        "release": 10.0,
        "python_major_version": "python2",
        "python_libraries": ["openupgradelib==2.0.0"],
    },
    {
        "release": 11.0,
        "python_major_version": "python3",
        "python_libraries": ["openupgradelib==2.0.0"],
    },
    {
        "release": 12.0,
        "python_major_version": "python3",
        "python_libraries": [
            "git+https://github.com/grap/openupgradelib.git"
            "@2.0.1#egg=openupgradelib"
        ],
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
    if migration_step["release"] >= 10.0:
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


def get_server_wide_modules_upgrade(migration_step: dict) -> str:
    """return a list of modules to load, depending on the migration step."""
    if (
        migration_step["release"] >= 14.0
        and migration_step["action"] == "upgrade"
    ):
        return ["openupgrade_framework"]
    return []


def get_upgrade_analysis_module(migration_step: dict) -> str:
    """ return the upgrade_analysis module name"""

    if migration_step["release"] >= 14.0:
        # (Module in OCA/server-tools)
        return "upgrade_analysis"

    # (module in OCA/OpenUpgrade/odoo/addons/)
    return "openupgrade_records"


def generate_records(odoo_instance, migration_step: dict):
    logger.info(
        "Generate Records in release %s ..."
        " (It can take a while)" % (migration_step["release"])
    )
    if migration_step["release"] < 14.0:
        wizard = odoo_instance.browse_by_create(
            "openupgrade.generate.records.wizard", {}
        )
    else:
        wizard = odoo_instance.browse_by_create(
            "upgrade.generate.record.wizard", {}
        )
    wizard.generate()
