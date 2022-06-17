import importlib
import os
from functools import total_ordering
from pathlib import Path

from git import Repo
from loguru import logger
from pygount import SourceAnalysis

from odoo_openupgrade_wizard.configuration_version_dependant import (
    get_apriori_file_relative_path,
    get_coverage_relative_path,
    get_openupgrade_analysis_files,
)
from odoo_openupgrade_wizard.tools_odoo import (
    get_odoo_addons_path,
    get_odoo_env_path,
)


class Analysis(object):
    def __init__(self, ctx):
        self.modules = []
        self.initial_release = ctx.obj["config"]["odoo_versions"][0]["release"]
        self.final_release = ctx.obj["config"]["odoo_versions"][-1]["release"]
        self.all_releases = [
            x["release"] for x in ctx.obj["config"]["odoo_versions"]
        ]

    def analyse_module_version(self, ctx, module_list):
        self._generate_module_version_first_release(ctx, module_list)

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
            for module_version in list(odoo_module.module_versions.values()):
                module_version.analyse_openupgrade_state(coverage_analysis)

        for release in self.all_releases[1:]:
            for odoo_module in filter(
                lambda x: x.module_type == "odoo", self.modules
            ):
                odoo_env_path = get_odoo_env_path(ctx, {"release": release})
                openupgrade_analysis_files = get_openupgrade_analysis_files(
                    odoo_env_path, release
                )
                # TODO, FIX ME
                openupgrade_analysis_files = openupgrade_analysis_files
                # module_version = odoo_module.get_module_version(release)
                # module_version.analyse_openupgrade_work(
                #     openupgrade_analysis_files
                # )

    def analyse_missing_module(self):
        for odoo_module in filter(
            lambda x: x.module_type != "odoo", self.modules
        ):
            last_module_version = odoo_module.module_versions.get(
                self.final_release, False
            )

            if (
                not last_module_version.addon_path
                and last_module_version.state
                not in ["renamed", "merged", "normal_loss"]
            ):
                last_module_version.analyse_missing_module()

    def estimate_workload(self, ctx):
        logger.info("Estimate workload ...")
        for odoo_module in self.modules:
            for module_version in odoo_module.module_versions.values():
                module_version.estimate_workload(ctx)

    def _generate_module_version_first_release(self, ctx, module_list):
        not_found_modules = []
        logger.info(
            "Analyse version %s. (First Release)" % self.initial_release
        )

        # Instanciate a new odoo_module
        for module_name in module_list:

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
                    new_odoo_module = OdooModule(
                        ctx, self, module_name, repository_name
                    )
                    new_module_version = OdooModuleVersion(
                        self.initial_release, new_odoo_module, addon_path
                    )
                    new_odoo_module.module_versions.update(
                        {self.initial_release: new_module_version}
                    )
                    self.modules.append(new_odoo_module)
            else:
                logger.error(
                    "Module %s not found for release %s."
                    % (module_name, self.initial_release)
                )
                not_found_modules.append(module_name)

        if not_found_modules:
            raise ValueError(
                "The modules %s have not been found in the release %s."
                " Analyse can not be done. Please update your repos.yml"
                " of your initial release to add repositories that"
                " include the modules, then run again the command."
                % (",".join(not_found_modules), self.initial_release)
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

    def get_module_qty(self, module_type=False):
        if module_type:
            odoo_modules = [
                x
                for x in filter(
                    lambda x: x.module_type == module_type, self.modules
                )
            ]
        else:
            odoo_modules = self.modules
        return len(odoo_modules)

    def workload_hour_text(self, module_type=False):
        if module_type:
            odoo_modules = [
                x
                for x in filter(
                    lambda x: x.module_type == module_type, self.modules
                )
            ]
        else:
            odoo_modules = self.modules

        total = 0
        for odoo_module in odoo_modules:
            for module_version in list(odoo_module.module_versions.values()):
                total += module_version.workload
        return "%d h" % (int(round(total / 60)))


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


class OdooModuleVersion(object):

    _exclude_directories = [
        "lib",
        "demo",
        "test",
        "tests",
        "doc",
        "description",
    ]
    _exclude_files = ["__openerp__.py", "__manifest__.py"]

    _file_extensions = [".py", ".xml", ".js"]

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
        self.python_code = 0
        self.xml_code = 0
        self.javascript_code = 0
        self.workload = 0
        self.openupgrade_model_lines = 0
        self.openupgrade_field_lines = 0
        self.openupgrade_xml_lines = 0

    def get_last_existing_version(self):
        versions = list(self.odoo_module.module_versions.values())
        return [x for x in filter(lambda x: x.addon_path, versions)][-1]

    def estimate_workload(self, ctx):
        settings = ctx.obj["config"]["workload_settings"]
        port_minimal_time = settings["port_minimal_time"]
        port_per_version = settings["port_per_version"]
        port_per_python_line_time = settings["port_per_python_line_time"]
        port_per_javascript_line_time = settings[
            "port_per_javascript_line_time"
        ]
        port_per_xml_line_time = settings["port_per_xml_line_time"]

        if self.state in ["merged", "renamed", "normal_loss"]:
            # The module has been moved, nothing to do
            return

        if self.odoo_module.module_type == "odoo":
            if self.release == self.odoo_module.analyse.initial_release:
                # No work to do for the initial release
                return
            if self.openupgrade_state and (
                self.openupgrade_state.lower().startswith("done")
                or self.openupgrade_state.lower().startswith("nothing to do")
            ):
                return
            else:
                # TODO
                self.workload = 99

        # OCA / Custom Module
        if self.release != self.odoo_module.analyse.final_release:
            # No need to work for intermediate release (in theory ;-))
            return

        if self.addon_path:
            # The module has been ported, nothing to do
            return

        previous_module_version = self.get_last_existing_version()
        self.workload = (
            # Minimal port time
            port_minimal_time
            # Add time per release
            + (self.release - previous_module_version.release)
            * port_per_version
            # Add python time
            + (port_per_python_line_time * previous_module_version.python_code)
            # Add XML Time
            + (port_per_xml_line_time * previous_module_version.xml_code)
            # Add Javascript Time
            + (
                port_per_javascript_line_time
                * previous_module_version.javascript_code
            )
        )

    def analyse_size(self):
        self.python_code = 0
        self.xml_code = 0
        self.javascript_code = 0
        # compute file list to analyse
        file_list = []
        for root, dirs, files in os.walk(
            self.addon_path / Path(self.odoo_module.name), followlinks=True
        ):
            relative_path = os.path.relpath(Path(root), self.addon_path)
            if set(Path(relative_path).parts) & set(self._exclude_directories):
                continue
            for name in files:
                if name in self._exclude_files:
                    continue
                filename, file_extension = os.path.splitext(name)
                if file_extension in self._file_extensions:
                    file_list.append(
                        (os.path.join(root, name), file_extension)
                    )

        # Analyse files
        for file_path, file_ext in file_list:
            file_res = SourceAnalysis.from_file(
                file_path, "", encoding="utf-8"
            )
            if file_ext == ".py":
                self.python_code += file_res.code
            elif file_ext == ".xml":
                self.xml_code += file_res.code
            elif file_ext == ".js":
                self.javascript_code += file_res.code

    def analyse_openupgrade_state(self, coverage_analysis):
        if self.release == self.odoo_module.analyse.initial_release:
            return
        self.openupgrade_state = coverage_analysis[self.release].get(
            self.odoo_module.name, False
        )

    def analyse_openupgrade_work(self, analysis_files):
        if self.release == self.odoo_module.analyse.initial_release:
            return
        analysis_file = analysis_files.get(self.odoo_module.name, False)
        if analysis_file:
            # TODO
            pass
        else:
            # TODO
            pass

    def workload_hour_text(self):
        if not self.workload:
            return ""
        return "%d h" % (int(round(self.workload / 60)))

    def get_size_text(self):
        data = {
            "Python": self.python_code,
            "XML": self.xml_code,
            "JavaScript": self.javascript_code,
        }
        # Remove empty values
        data = {k: v for k, v in data.items() if v}
        if not data:
            return ""
        else:
            return ", ".join(["%s: %s" % (a, b) for a, b in data.items()])

    def analyse_missing_module(self):
        last_existing_version = self.get_last_existing_version()
        last_existing_version.analyse_size()

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
                return (
                    "To port from %s"
                    % self.get_last_existing_version().release
                )
