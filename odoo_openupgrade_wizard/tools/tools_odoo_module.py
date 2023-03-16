import importlib
import os
from functools import total_ordering
from pathlib import Path

import requests
from git import Repo
from git.exc import InvalidGitRepositoryError
from loguru import logger
from pygount import SourceAnalysis

from odoo_openupgrade_wizard.configuration_version_dependant import (
    get_apriori_file_relative_path,
    get_coverage_relative_path,
    get_openupgrade_analysis_files,
)
from odoo_openupgrade_wizard.tools.tools_odoo import (
    get_odoo_addons_path,
    get_odoo_env_path,
)


class Analysis(object):
    def __init__(self, ctx):
        self.modules = []
        self.initial_version = ctx.obj["config"]["odoo_versions"][0]
        self.final_version = ctx.obj["config"]["odoo_versions"][-1]
        self.all_versions = [x for x in ctx.obj["config"]["odoo_versions"]]

    def analyse_module_version(self, ctx, module_list):
        self._generate_module_version_first_version(ctx, module_list)

        for count in range(len(self.all_versions) - 1):
            previous_version = self.all_versions[count]
            current_version = self.all_versions[count + 1]
            self._generate_module_version_next_version(
                ctx, previous_version, current_version
            )

    def analyse_openupgrade_state(self, ctx):
        logger.info("Parsing openupgrade module coverage for each migration.")
        coverage_analysis = {}
        for version in self.all_versions[1:]:
            coverage_analysis[version] = {}
            relative_path = get_coverage_relative_path(version)
            env_folder_path = get_odoo_env_path(ctx, version)
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
                    coverage_analysis[version][splited_line[0]] = splited_line[
                        1
                    ]
                if len(splited_line) == 3:
                    coverage_analysis[version][splited_line[0]] = (
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

        for version in self.all_versions[1:]:
            odoo_env_path = get_odoo_env_path(ctx, version)
            openupgrade_analysis_files = get_openupgrade_analysis_files(
                odoo_env_path, version
            )
            openupgrade_analysis_files = openupgrade_analysis_files
            for odoo_module in filter(
                lambda x: x.module_type == "odoo", self.modules
            ):
                module_version = odoo_module.get_module_version(version)
                if module_version:
                    module_version.analyse_openupgrade_work(
                        openupgrade_analysis_files
                    )

    def analyse_missing_module(self):
        for odoo_module in filter(
            lambda x: x.module_type != "odoo", self.modules
        ):
            last_module_version = odoo_module.module_versions.get(
                self.final_version, False
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

    def _generate_module_version_first_version(self, ctx, module_list):
        logger.info(
            "Analyse version %s. (First version)" % self.initial_version
        )

        # Instanciate a new odoo_module
        for module_name in module_list:

            addon_path = OdooModule.get_addon_path(
                ctx, module_name, self.initial_version
            )
            if addon_path:
                repository_name = OdooModule.get_repository_name(addon_path)
                if (
                    "%s.%s" % (repository_name, module_name)
                    not in self.modules
                ):
                    logger.debug(
                        "Discovering module '%s' in %s for version %s"
                        % (module_name, repository_name, self.initial_version)
                    )
            else:
                repository_name = False
                logger.error(
                    "Module %s not found for version %s."
                    % (module_name, self.initial_version)
                )
            new_odoo_module = OdooModule(
                ctx, self, module_name, repository_name
            )
            new_module_version = OdooModuleVersion(
                self.initial_version, new_odoo_module, addon_path
            )
            new_odoo_module.module_versions.update(
                {self.initial_version: new_module_version}
            )
            self.modules.append(new_odoo_module)

    def _generate_module_version_next_version(
        self, ctx, previous_version, current_version
    ):
        logger.info(
            "Analyse change between %s and %s"
            % (previous_version, current_version)
        )
        # Get changes between the two versions
        (
            apriori_module_name,
            apriori_relative_path,
        ) = get_apriori_file_relative_path(current_version)
        apriori_module_path = OdooModule.get_addon_path(
            ctx, apriori_module_name, current_version
        )
        if not apriori_module_path:
            raise ValueError(
                "Unable to find the path of the module %s for the version %s"
                % (apriori_module_name, current_version)
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
                        previous_version,
                        current_version,
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
                        previous_version,
                        current_version,
                        odoo_module.name,
                        new_module_name,
                    )
                )

            # Handle new module
            if state and new_module_name != odoo_module.name:
                # Ensure that the module exists in self.modules
                new_addon_path = OdooModule.get_addon_path(
                    ctx, new_module_name, current_version
                )
                if not new_addon_path:
                    raise ValueError(
                        "The module %s has not been found in the version %s."
                        " Analyse can not be done."
                        % (new_module_name, current_version)
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
                            "Discovering module '%s' in %s for version %s"
                            % (
                                new_module_name,
                                new_repository_name,
                                current_version,
                            )
                        )
                        new_odoo_module = OdooModule(
                            ctx, self, new_module_name, new_repository_name
                        )
                        self.modules.append(new_odoo_module)
                        new_odoo_module.module_versions.update(
                            {
                                current_version: OdooModuleVersion(
                                    current_version,
                                    new_odoo_module,
                                    new_addon_path,
                                )
                            }
                        )

            # Get the previous version of the module
            previous_module_version = odoo_module.get_module_version(
                previous_version
            )
            # if the previous version has been renamed or merged
            # the loss is normal
            if previous_module_version and previous_module_version.state in [
                "merged",
                "renamed",
                "normal_loss",
            ]:
                state = "normal_loss"

            new_addon_path = OdooModule.get_addon_path(
                ctx, odoo_module.name, current_version
            )
            odoo_module.module_versions.update(
                {
                    current_version: OdooModuleVersion(
                        current_version,
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
        self.ignored = self.is_ignored(ctx, module_name)
        self.module_versions = {}
        if not repository_name:
            self.module_type = "not_found"
        elif repository_name == "odoo/odoo":
            self.module_type = "odoo"
        elif repository_name.startswith("oca"):
            self.module_type = "oca"
        else:
            self.module_type = "custom"

    @property
    def workload(self):
        return sum(
            round(module_version.workload)
            for _, module_version in self.module_versions.items()
        )

    def is_ignored(self, ctx, module_name):
        """Return true if module should be ignored"""
        settings = ctx.obj["config"]["workload_settings"]
        return module_name in settings["ignored_module_list"]

    def get_module_version(self, current_version):
        res = self.module_versions.get(current_version, False)
        return res

    def get_odoo_apps_url(self):
        logger.info("Searching %s in the Odoo appstore ..." % self.name)
        url = f"https://apps.odoo.com/apps/modules/14.0/{self.name}/"
        if requests.get(url).status_code == 200:
            return url
        return False

    def get_odoo_code_search_url(self):
        logger.info("Searching %s in Odoo-Code-Search ..." % self.name)
        url = (
            f"https://odoo-code-search.com/ocs/search?"
            f"q=name%3A%3D{self.name}+version%3A{self.analyse.initial_version}"
        )
        result = requests.get(url)
        if '<td class="code">404</td>' in result.text:
            return False
        return url

    @classmethod
    def get_addon_path(cls, ctx, module_name, current_version):
        """Search the module in all the addons path of a given version
        and return the addon path of the module, or False if not found.
        For exemple find_repository(ctx, 'web_responsive', 12.0)
        '/PATH_TO_LOCAL_ENV/src/oca/web'
        """
        # Try to find the repository that contains the module
        main_path = get_odoo_env_path(ctx, current_version)
        addons_path = get_odoo_addons_path(
            ctx,
            main_path,
            {"version": current_version, "execution_context": "openupgrade"},
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
        For exemple 'oca/web' or 'odoo/odoo'
        """
        # TODO, make the code cleaner and more resiliant
        # for the time being, the code will fail for
        # - github url set with git+http...
        # - gitlab url
        # - if odoo code is not in a odoo folder in the repos.yml file...
        odoo_odoo_addons = (
            "odoo/odoo/addons",
            "odoo/openerp/addons",
            "openupgrade/odoo/addons",
            "openupgrade/openerp/addons",
        )
        odoo_addons = (
            "odoo/addons",
            "openupgrade/addons",
        )
        if str(addon_path).endswith(odoo_odoo_addons):
            path = addon_path.parent.parent
        elif str(addon_path).endswith(odoo_addons):
            path = addon_path.parent
        else:
            path = addon_path
        try:
            repo = Repo(str(path))
        except InvalidGitRepositoryError as err:
            logger.critical(f"{path} is not a Git Repository.")
            raise err
        github_url_prefixes = (
            "https://github.com/",
            "git@github.com:",
        )
        repository_names = []
        for remote in repo.remotes:
            # Standardize all repository_name to lower case
            repository_name = remote.url.lower()
            for github_url_prefix in github_url_prefixes:
                repository_name = repository_name.replace(
                    github_url_prefix, ""
                )
            if repository_name.endswith(".git"):
                repository_name = repository_name[: -len(".git")]
            repository_names.append(repository_name)
        # find main repository_name
        main_repository_name = next(
            (
                repo_name
                for repo_name in repository_names
                if repo_name.startswith("oca")
            ),
            None,
        )
        if not main_repository_name:
            main_repository_name = repository_names[0]
        if main_repository_name == "oca/openupgrade":
            return "odoo/odoo"
        else:
            return main_repository_name

    def __eq__(self, other):
        if isinstance(other, str):
            return self.unique_name == other
        elif isinstance(other, OdooModule):
            return self.unique_name == other.unique_name

    def __lt__(self, other):
        if self.module_type != other.module_type:
            if self.module_type == "odoo":
                return True
            elif self.module_type == "oca" and other.module_type in [
                "custom",
                "not_found",
            ]:
                return True
            elif (
                self.module_type == "custom"
                and other.module_type == "not_found"
            ):
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
        version,
        odoo_module,
        addon_path,
        state=False,
        target_module=False,
    ):
        self.version = version
        self.odoo_module = odoo_module
        self.addon_path = addon_path
        self.state = "ignored" if odoo_module.ignored else state
        self.target_module = target_module
        self.openupgrade_state = ""
        self.python_code = 0
        self.xml_code = 0
        self.javascript_code = 0
        self._workload = 0
        self.analysis_file = False
        self.openupgrade_model_lines = 0
        self.openupgrade_field_lines = 0
        self.openupgrade_xml_lines = 0

    @property
    def workload(self):
        return int(round(self._workload))

    @workload.setter
    def workload(self, value):
        self._workload = int(round(value))

    def get_last_existing_version(self):
        if self.odoo_module.module_type != "not_found":
            versions = list(self.odoo_module.module_versions.values())
            return [x for x in filter(lambda x: x.addon_path, versions)][-1]
        else:
            return False

    def estimate_workload(self, ctx):
        settings = ctx.obj["config"]["workload_settings"]
        port_minimal_time = settings["port_minimal_time"]
        port_per_version = settings["port_per_version"]
        port_per_python_line_time = settings["port_per_python_line_time"]
        port_per_javascript_line_time = settings[
            "port_per_javascript_line_time"
        ]
        port_per_xml_line_time = settings["port_per_xml_line_time"]
        open_upgrade_minimal_time = settings["open_upgrade_minimal_time"]
        openupgrade_model_line_time = settings["openupgrade_model_line_time"]
        openupgrade_field_line_time = settings["openupgrade_field_line_time"]
        openupgrade_xml_line_time = settings["openupgrade_xml_line_time"]

        if self.state in ["merged", "renamed", "normal_loss", "ignored"]:
            # The module has been moved, nothing to do
            return

        if self.odoo_module.module_type == "odoo":
            if self.version == self.odoo_module.analyse.initial_version:
                # No work to do for the initial version
                return
            if self.openupgrade_state and (
                self.openupgrade_state.lower().startswith("done")
                or self.openupgrade_state.lower().startswith("nothing to do")
                or self.openupgrade_state.lower().startswith(
                    "no db layout changes"
                )
            ):
                return
            else:
                self.workload = (
                    # Minimal openupgrade time
                    open_upgrade_minimal_time
                    # Add model time
                    + (
                        openupgrade_model_line_time
                        * self.openupgrade_model_lines
                    )
                    # Add field Time
                    + (
                        openupgrade_field_line_time
                        * self.openupgrade_field_lines
                    )
                    # Add XML Time
                    + (openupgrade_xml_line_time * self.openupgrade_xml_lines)
                )

        # OCA / Custom Module
        if self.version != self.odoo_module.analyse.final_version:
            # No need to work for intermediate version (in theory ;-))
            return

        if self.addon_path:
            # The module has been ported, nothing to do
            return

        previous_module_version = self.get_last_existing_version()
        if not previous_module_version:
            return
        self.workload = (
            # Minimal port time
            port_minimal_time
            # Add time per version
            + (self.version - previous_module_version.version)
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
        if self.version == self.odoo_module.analyse.initial_version:
            return
        self.openupgrade_state = coverage_analysis[self.version].get(
            self.odoo_module.name, False
        )

    def analyse_openupgrade_work(self, analysis_files):
        if self.version == self.odoo_module.analyse.initial_version:
            return
        analysis_file = analysis_files.get(self.odoo_module.name, False)

        if not analysis_file:
            return

        self.analysis_file = analysis_file
        with open(analysis_file, "r") as input_file:
            line_type = False
            for line in input_file.readlines():
                if line.startswith("---Models in module"):
                    line_type = "model"
                    continue
                elif line.startswith("---Fields in module"):
                    line_type = "field"
                    continue
                elif line.startswith("---XML records in module"):
                    line_type = "xml"
                    continue
                elif line.startswith("---nothing has changed in this module"):
                    continue
                elif line.startswith("---"):
                    raise Exception("comment %s not undestood" % line)

                if line_type == "model":
                    self.openupgrade_model_lines += 1
                elif line_type == "field":
                    self.openupgrade_field_lines += 1
                elif line_type == "xml":
                    self.openupgrade_xml_lines += 1

    def workload_hour_text(self):
        if not self.workload:
            return ""
        hour = int(self.workload // 60)
        minute = round(self.workload % 60)
        return f"{hour}h{minute:02}"

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

    def get_analysis_text(self):
        data = {
            "Model": self.openupgrade_model_lines,
            "Field": self.openupgrade_field_lines,
            "XML": self.openupgrade_xml_lines,
        }
        # Remove empty values
        data = {k: v for k, v in data.items() if v}
        if not data:
            return ""
        else:
            return ", ".join(["%s: %s" % (a, b) for a, b in data.items()])

    def analysis_url(self):
        return os.path.relpath(self.analysis_file, Path(os.getcwd()))

    def analyse_missing_module(self):
        last_existing_version = self.get_last_existing_version()
        if not last_existing_version:
            return
        last_existing_version.analyse_size()

    def get_bg_color(self):
        if self.addon_path:
            if (
                self.odoo_module.module_type == "odoo"
                and self.version != self.odoo_module.analyse.initial_version
            ):
                if self.openupgrade_state and (
                    self.openupgrade_state.lower().startswith("done")
                    or self.openupgrade_state.lower().startswith(
                        "nothing to do"
                    )
                    or self.openupgrade_state.lower().startswith(
                        "no db layout changes"
                    )
                ):
                    return "lightgreen"
                else:
                    return "orange"
            return "lightgreen"
        else:
            # The module doesn't exist in the current version
            if self.state in ["merged", "renamed", "normal_loss", "ignored"]:
                # Normal case, the previous version has been renamed
                # or merged
                return "lightgray"

            if self.odoo_module.module_type == "odoo":
                # A core module disappeared and has not been merged
                # or renamed
                return "red"
            elif self.version != self.odoo_module.analyse.final_version:
                return "lightgray"
            elif self.odoo_module.module_type == "not_found":
                return "lightgray"
            else:
                return "orange"

    def get_text(self):
        if self.addon_path:
            if (
                self.odoo_module.module_type == "odoo"
                and self.version != self.odoo_module.analyse.initial_version
            ):
                if self.openupgrade_state:
                    return self.openupgrade_state
                else:
                    return "To analyse"
        else:
            if self.state == "merged":
                return "Merged into %s" % self.target_module
            elif self.state == "renamed":
                return "Renamed into %s" % self.target_module
            elif self.state == "ignored":
                return "Ignored"
            elif self.state == "normal_loss":
                return ""

            if self.odoo_module.module_type == "odoo":
                # A core module disappeared and has not been merged
                # or renamed
                return "Module lost"
            else:
                last_existing_version = self.get_last_existing_version()
                if not last_existing_version:
                    return "Unknown"
                elif self.version != self.odoo_module.analyse.final_version:
                    return "Unported"
                else:
                    return "To port from %s" % last_existing_version.version
