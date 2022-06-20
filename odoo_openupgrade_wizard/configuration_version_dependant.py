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
    """return a boolean to indicate if the addon_path should be
    remove (during the generation of the addons_path).
    Note : if repo.yml contains both odoo and openupgrade repo
    we skip one of them (before the V14 refactoring)"""
    return (
        str(path).endswith("/src/odoo")
        or str(path).endswith("src/openupgrade")
    ) and migration_step["release"] < 14.0


def get_server_wide_modules_upgrade(migration_step: dict) -> list:
    """return a list of modules to load, depending on the migration step."""
    if (
        migration_step["release"] >= 14.0
        and migration_step["action"] == "upgrade"
    ):
        return ["openupgrade_framework"]
    return []


def get_upgrade_analysis_module(migration_step: dict) -> str:
    """return the upgrade_analysis module name"""

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


def get_installable_odoo_modules(odoo_instance, migraton_step):
    if migraton_step["release"] < 14.0:
        # TODO, improve that algorithm, if possible
        modules = odoo_instance.browse_by_search(
            "ir.module.module",
            [
                ("state", "!=", "uninstallable"),
                ("website", "not ilike", "github/OCA"),
            ],
        )

    else:
        # We use here a new feature implemented in the upgrade_analysis
        # in a wizard to install odoo modules
        wizard = odoo_instance.browse_by_create("upgrade.install.wizard", {})
        wizard.select_odoo_modules()
        modules = wizard.module_ids

    return modules.mapped("name")


def generate_analysis_files(
    final_odoo_instance, final_step, initial_odoo_host, initial_database
):
    logger.info(
        "Generate analysis files for"
        " the modules installed on %s ..." % (initial_database)
    )
    proxy_vals = {
        "name": "Proxy to Previous Release",
        "server": initial_odoo_host,
        "port": "8069",
        "database": initial_database,
        "username": "admin",
        "password": "admin",
    }
    if final_step["release"] < 14.0:
        logger.info("> Create proxy ...")
        proxy = final_odoo_instance.browse_by_create(
            "openupgrade.comparison.config", proxy_vals
        )

        logger.info("> Create wizard ...")
        wizard = final_odoo_instance.browse_by_create(
            "openupgrade.analysis.wizard",
            {
                "server_config": proxy.id,
                "write_files": True,
            },
        )
        logger.info("> Launch analysis. This can take a while ...")
        wizard.get_communication()

    else:
        logger.info("> Create proxy ...")
        proxy = final_odoo_instance.browse_by_create(
            "upgrade.comparison.config", proxy_vals
        )

        logger.info("> Create wizard ...")
        analysis = final_odoo_instance.browse_by_create(
            "upgrade.analysis",
            {
                "config_id": proxy.id,
            },
        )

        logger.info("> Launch analysis. This can take a while ...")
        analysis.analyze()


def get_apriori_file_relative_path(migration_step: dict) -> (str, Path):
    """Return the module name and the relative file path of
    the apriori.py file that contains all the rename and
    the merge information for a given upgrade."""
    if migration_step["release"] < 14.0:
        return ("openupgrade_records", Path("lib/apriori.py"))
    else:
        return ("openupgrade_scripts", Path("apriori.py"))


def get_coverage_relative_path(migration_step: dict) -> (str, Path):
    """Return the path of the coverage file."""
    if migration_step["release"] < 10.0:
        base_path = Path("src/openupgrade/openerp/openupgrade/doc/source")
    elif migration_step["release"] < 14.0:
        base_path = Path("src/openupgrade/odoo/openupgrade/doc/source")
    else:
        base_path = Path("src/openupgrade/docsource")

    previous_release = migration_step["release"] - 1
    return base_path / Path(
        "modules%s-%s.rst"
        % (
            ("%.1f" % previous_release).replace(".", ""),
            ("%.1f" % migration_step["release"]).replace(".", ""),
        )
    )


def get_openupgrade_analysis_files(
    odoo_env_path: Path, release: float
) -> dict:
    """return a dictionnary of module_name : path,
    where module_name is the name of each module of a release
    and and path is the path of the migration_analysis.txt file
    of the module"""
    result = {}
    if release < 14.0:
        base_name = "openupgrade_analysis.txt"
    else:
        base_name = "upgrade_analysis.txt"

    files = [
        x
        for x in sorted(odoo_env_path.rglob("**/*.txt"))
        if x.name == base_name
    ]

    for file in files:
        # this part doesn't depends only of the release
        # 14+ module can have migrations folder.
        if file.parent.parent.name == "migrations":
            module_name = file.parent.parent.parent.name
        else:
            module_name = file.parent.parent.name
        result[module_name] = file
    logger.debug(
        "Release %s : %d analysis files found." % (release, len(result))
    )
    return result
