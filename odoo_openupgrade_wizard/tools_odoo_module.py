from functools import total_ordering

from git import Repo
from loguru import logger

from odoo_openupgrade_wizard.tools_odoo import (
    get_odoo_addons_path,
    get_odoo_env_path,
    get_odoo_modules_from_csv,
)


class Analysis(object):

    modules = []

    def __init__(self, ctx):
        module_names = get_odoo_modules_from_csv(ctx.obj["module_file_path"])

        initial_release = ctx.obj["config"]["odoo_versions"][0]["release"]

        # Instanciate a new odoo_module
        for module_name in module_names:
            repository_name = OdooModule.find_repository(
                ctx, module_name, initial_release
            )
            if (
                repository_name
                and "%s.%s" % (repository_name, module_name)
                not in self.modules
            ):
                logger.debug(
                    "Discovering module '%s' in %s for release %s"
                    % (module_name, repository_name, initial_release)
                )
                self.modules.append(
                    OdooModule(ctx, module_name, repository_name)
                )


@total_ordering
class OdooModule(object):

    active = True
    name = False
    repository = False
    module_type = False
    unique_name = False

    @classmethod
    def find_repository(cls, ctx, module_name, current_release):

        # Try to find the repository that contains the module
        main_path = get_odoo_env_path(ctx, {"release": current_release})
        addons_path = get_odoo_addons_path(
            ctx, main_path, {"release": current_release, "action": "update"}
        )
        for addon_path in addons_path:
            if (addon_path / module_name).exists():

                if str(addon_path).endswith("odoo/odoo/addons"):
                    path = addon_path.parent.parent
                elif str(addon_path).endswith("odoo/addons"):
                    path = addon_path.parent
                else:
                    path = addon_path
                repo = Repo(str(path))
                repository_name = repo.remotes[0].url.replace(
                    "https://github.com/", ""
                )

                return repository_name

        return False

    def __init__(self, ctx, module_name, repository_name):
        self.name = module_name
        self.repository = repository_name
        if repository_name == "odoo/odoo":
            self.module_type = "odoo"
        elif repository_name.startswith("OCA"):
            self.module_type = "OCA"
        else:
            self.module_type = "custom"
        self.unique_name = "%s.%s" % (repository_name, module_name)

    def __eq__(self, other):
        if isinstance(other, str):
            return self.unique_name == other
        elif isinstance(other, OdooModule):
            return self.unique_name == other.unique_name

    def __lt__(self, other):
        if self.module_type != other.module_type:
            if self.module_type == "odoo":
                return True
            elif self.module_type == "OCA" and self.module_type == "custom":
                return True
            else:
                return False
        else:
            return self.name < other.name
