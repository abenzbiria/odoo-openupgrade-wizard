import importlib
from functools import total_ordering
from pathlib import Path

from git import Repo
from loguru import logger

from odoo_openupgrade_wizard.configuration_version_dependant import (
    get_apriori_file_relative_path,
    get_coverage_relative_path,
)
from odoo_openupgrade_wizard.tools_odoo import (
    get_odoo_addons_path,
    get_odoo_env_path,
    get_odoo_modules_from_csv,
)


class Analysis(object):
    def __init__(self, ctx):
        module_names = get_odoo_modules_from_csv(ctx.obj["module_file_path"])

        self.modules = []
        self.initial_release = ctx.obj["config"]["odoo_versions"][0]["release"]
        self.final_release = ctx.obj["config"]["odoo_versions"][-1]["release"]
        self.all_releases = [
            x["release"] for x in ctx.obj["config"]["odoo_versions"]
        ]

        # Instanciate a new odoo_module
        for module_name in module_names:

            addon_path = OdooModule.get_addon_path(
                ctx, module_name, self.initial_release
            )
            if addon_path:
                repository_name = OdooModule.get_repository_name(addon_path)
                if (
                    "%s.%s" % (repository_name, module_name)
                    not in self.modules
                ):
                    logger.debug(
                        "Discovering module '%s' in %s for release %s"
                        % (module_name, repository_name, self.initial_release)
                    )
                    self.modules.append(
                        OdooModule(ctx, self, module_name, repository_name)
                    )
            else:
                raise ValueError(
                    "The module %s has not been found in the release %s."
                    "Analyse can not be done."
                    % (module_name, self.initial_release)
                )

    def analyse_module_version(self, ctx):
        self._generate_module_version_first_release(ctx)

        for count in range(len(self.all_releases) - 1):
            previous_release = self.all_releases[count]
            current_release = self.all_releases[count + 1]
            self._generate_module_version_next_release(
                ctx, previous_release, current_release
            )

    def analyse_openupgrade_state(self, ctx):
        logger.info("Parsing openupgrade module coverage for each migration.")
        coverage_analysis = {}
        for release in self.all_releases[1:]:
            coverage_analysis[release] = {}
            relative_path = get_coverage_relative_path({"release": release})
            env_folder_path = get_odoo_env_path(ctx, {"release": release})
            coverage_path = env_folder_path / relative_path
            with open(coverage_path) as f:
                lines = f.readlines()
            for line in [x for x in lines if "|" in x]:
                clean_line = (
                    line.replace("\n", "")
                    .replace("|del|", "")
                    .replace("|new|", "")
                )
                splited_line = [x.strip() for x in clean_line.split("|") if x]
                if len(splited_line) == 2:
                    coverage_analysis[release][splited_line[0]] = splited_line[
                        1
                    ]
                if len(splited_line) == 3:
                    coverage_analysis[release][splited_line[0]] = (
                        splited_line[1] + " " + splited_line[2]
                    ).strip()
                elif len(splited_line) > 3:
                    raise ValueError(
                        "Incorrect value in openupgrade analysis file %s"
                        " for line %s" % (coverage_path, line)
                    )

        for odoo_module in filter(
            lambda x: x.module_type == "odoo", self.modules
        ):
            odoo_module.analyse_openupgrade_state(coverage_analysis)

    def _generate_module_version_first_release(self, ctx):
        logger.info(
            "Analyse version %s. (First Release)" % self.initial_release
        )
        for odoo_module in self.modules:
            # Get new name of the module
            new_name = odoo_module.name

            addon_path = OdooModule.get_addon_path(
                ctx, new_name, self.initial_release
            )

            new_module_version = OdooModuleVersion(
                self.initial_release, odoo_module, addon_path
            )
            odoo_module.module_versions.update(
                {self.initial_release: new_module_version}
            )

    def _generate_module_version_next_release(
        self, ctx, previous_release, current_release
    ):
        logger.info(
            "Analyse change between %s and %s"
            % (previous_release, current_release)
        )
        # Get changes between the two releases
        (
            apriori_module_name,
            apriori_relative_path,
        ) = get_apriori_file_relative_path({"release": current_release})
        apriori_module_path = OdooModule.get_addon_path(
            ctx, apriori_module_name, current_release
        )
        apriori_absolute_path = (
            apriori_module_path
            / Path(apriori_module_name)
            / apriori_relative_path
        )

        module_spec = importlib.util.spec_from_file_location(
            "package", str(apriori_absolute_path)
        )
        module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module)

        renamed_modules = module.renamed_modules
        merged_modules = module.merged_modules

        for odoo_module in self.modules:
            state = False
            new_module_name = False
            if odoo_module.name in renamed_modules:
                state = "renamed"
                new_module_name = renamed_modules[odoo_module.name]
                logger.debug(
                    "%s -> %s : %s renamed into %s"
                    % (
                        previous_release,
                        current_release,
                        odoo_module.name,
                        new_module_name,
                    )
                )
            elif odoo_module.name in merged_modules:
                state = "merged"
                new_module_name = merged_modules[odoo_module.name]
                logger.debug(
                    "%s -> %s : %s merged into %s"
                    % (
                        previous_release,
                        current_release,
                        odoo_module.name,
                        new_module_name,
                    )
                )

            # Handle new module
            if state and new_module_name != odoo_module.name:
                # Ensure that the module exists in self.modules
                new_addon_path = OdooModule.get_addon_path(
                    ctx, new_module_name, current_release
                )
                if not new_addon_path:
                    raise ValueError(
                        "The module %s has not been found in the release %s."
                        " Analyse can not be done."
                        % (new_module_name, current_release)
                    )
                else:
                    new_repository_name = OdooModule.get_repository_name(
                        new_addon_path
                    )
                    if (
                        "%s.%s" % (new_repository_name, new_module_name)
                        not in self.modules
                    ):
                        logger.debug(
                            "Discovering module '%s' in %s for release %s"
                            % (
                                new_module_name,
                                new_repository_name,
                                current_release,
                            )
                        )
                        new_odoo_module = OdooModule(
                            ctx, self, new_module_name, new_repository_name
                        )
                        self.modules.append(new_odoo_module)
                        new_odoo_module.module_versions.update(
                            {
                                current_release: OdooModuleVersion(
                                    current_release,
                                    new_odoo_module,
                                    new_addon_path,
                                )
                            }
                        )

            # Get the previous release of the module
            previous_module_version = odoo_module.get_module_version(
                previous_release
            )
            # if the previous release has been renamed or merged
            # the loss is normal
            if previous_module_version and previous_module_version.state in [
                "merged",
                "renamed",
                "normal_loss",
            ]:
                state = "normal_loss"

            new_addon_path = OdooModule.get_addon_path(
                ctx, odoo_module.name, current_release
            )
            odoo_module.module_versions.update(
                {
                    current_release: OdooModuleVersion(
                        current_release,
                        odoo_module,
                        new_addon_path,
                        state=state,
                        target_module=new_module_name,
                    )
                }
            )


@total_ordering
class OdooModule(object):
    def __init__(self, ctx, analyse, module_name, repository_name):
        self.analyse = analyse
        self.name = module_name
        self.repository = repository_name
        self.unique_name = "%s.%s" % (repository_name, module_name)
        self.module_versions = {}
        if repository_name == "odoo/odoo":
            self.module_type = "odoo"
        elif repository_name.startswith("OCA"):
            self.module_type = "OCA"
        else:
            self.module_type = "custom"

    def get_module_version(self, current_release):
        res = self.module_versions.get(current_release, False)
        return res

    def analyse_openupgrade_state(self, coverage_analysis):
        for module_version in list(self.module_versions.values()):
            module_version.analyse_openupgrade_state(coverage_analysis)

    @classmethod
    def get_addon_path(cls, ctx, module_name, current_release):
        """Search the module in all the addons path of the current release
        and return the addon path of the module, or False if not found.
        For exemple find_repository(ctx, 'web_responsive', 12.0)
        '/PATH_TO_LOCAL_ENV/src/OCA/web'
        """
        # Try to find the repository that contains the module
        main_path = get_odoo_env_path(ctx, {"release": current_release})
        addons_path = get_odoo_addons_path(
            ctx, main_path, {"release": current_release, "action": "upgrade"}
        )
        for addon_path in addons_path:
            if (addon_path / module_name).exists():
                return addon_path
        return False

    @classmethod
    def get_repository_name(cls, addon_path):
        """Given an addons path that contains odoo modules in a folder
        that has been checkouted via git, return a repository name with the
        following format org_name/repo_name.
        For exemple 'OCA/web' or 'odoo/odoo'
        """
        # TODO, make the code cleaner and more resiliant
        # for the time being, the code will fail for
        # - github url set with git+http...
        # - gitlab url
        # - if odoo code is not in a odoo folder in the repos.yml file...
        if str(addon_path).endswith("odoo/odoo/addons") or str(
            addon_path
        ).endswith("openupgrade/odoo/addons"):
            path = addon_path.parent.parent
        elif str(addon_path).endswith("odoo/addons") or str(
            addon_path
        ).endswith("openupgrade/addons"):
            path = addon_path.parent
        else:
            path = addon_path
        repo = Repo(str(path))
        repository_name = repo.remotes[0].url.replace(
            "https://github.com/", ""
        )
        if repository_name.lower() == "oca/openupgrade":
            return "odoo/odoo"
        else:
            return repository_name

    def __eq__(self, other):
        if isinstance(other, str):
            return self.unique_name == other
        elif isinstance(other, OdooModule):
            return self.unique_name == other.unique_name

    def __lt__(self, other):
        if self.module_type != other.module_type:
            if self.module_type == "odoo":
                return True
            elif self.module_type == "OCA" and other.module_type == "custom":
                return True
            else:
                return False
        elif self.repository != other.repository:
            return self.repository < other.repository
        else:
            return self.name < other.name

    def __str__(self):
        return "%s - %s" % (self.unique_name, self.module_type)


class OdooModuleVersion(object):
    def __init__(
        self,
        release,
        odoo_module,
        addon_path,
        state=False,
        target_module=False,
    ):
        self.release = release
        self.odoo_module = odoo_module
        self.addon_path = addon_path
        self.state = state
        self.target_module = target_module
        self.openupgrade_state = ""

    def analyse_openupgrade_state(self, coverage_analysis):
        if self.release == self.odoo_module.analyse.initial_release:
            return
        self.openupgrade_state = coverage_analysis[self.release].get(
            self.odoo_module.name, False
        )

    def get_bg_color(self):
        if self.addon_path:
            if (
                self.odoo_module.module_type == "odoo"
                and self.release != self.odoo_module.analyse.initial_release
            ):
                if self.openupgrade_state and (
                    self.openupgrade_state.lower().startswith("done")
                    or self.openupgrade_state.lower().startswith(
                        "nothing to do"
                    )
                ):
                    return "lightgreen"
                else:
                    return "orange"
            return "lightgreen"
        else:
            # The module doesn't exist in the current release
            if self.state in ["merged", "renamed", "normal_loss"]:
                # Normal case, the previous version has been renamed
                # or merged
                return "lightgray"

            if self.odoo_module.module_type == "odoo":
                # A core module disappeared and has not been merged
                # or renamed
                return "red"
            elif self.release != self.odoo_module.analyse.final_release:
                return "lightgray"
            else:
                return "orange"

    def get_text(self):
        if self.addon_path:
            if (
                self.odoo_module.module_type == "odoo"
                and self.release != self.odoo_module.analyse.initial_release
            ):
                if self.openupgrade_state.lower().startswith(
                    "done"
                ) or self.openupgrade_state.lower().startswith(
                    "nothing to do"
                ):
                    return self.openupgrade_state
                else:
                    return "To analyse"
            return ""
        else:
            if self.state == "merged":
                return "Merged into %s" % self.target_module
            elif self.state == "renamed":
                return "Renamed into %s" % self.target_module
            elif self.state == "normal_loss":
                return ""

            if self.odoo_module.module_type == "odoo":
                # A core module disappeared and has not been merged
                # or renamed
                return "Module lost"
            elif self.release != self.odoo_module.analyse.final_release:
                return "Unported"
            else:
                return "To port"

    def __str__(self):
        return "%s - %s - %s" % (
            self.odoo_module.name,
            self.release,
            self.addon_path,
        )
