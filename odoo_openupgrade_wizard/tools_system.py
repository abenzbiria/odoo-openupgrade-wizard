import argparse
import os
from pathlib import Path

from git_aggregator import main as gitaggregate_cmd
from git_aggregator.utils import working_directory_keeper
from jinja2 import Template
from loguru import logger
from plumbum.cmd import mkdir

from odoo_openupgrade_wizard import templates


def ensure_folder_exists(
    folder_path: Path, mode: str = "755", git_ignore_content: bool = False
):
    """Create a local folder.
    - directory is created if it doesn't exist.
    - mode is applied if defined.
    - a log is done at INFO level.
    """
    if not folder_path.exists():
        cmd = ["--parents", folder_path]
        cmd = ["--mode", mode] + cmd
        logger.info("Creating folder '%s' ..." % (folder_path))
        mkdir(cmd)

    if git_ignore_content:
        ensure_file_exists_from_template(
            folder_path / Path(".gitignore"),
            templates.GIT_IGNORE_CONTENT,
        )


def ensure_file_exists_from_template(
    file_path: Path, template_name: str, **args
):

    template = Template(template_name)
    output = template.render(args)

    if file_path.exists():
        # Check if content is different
        with open(file_path, "r") as file:
            data = file.read()
            file.close()
            if data == output:
                return

        log_text = "Updating file '%s' from template ..." % (file_path)
    else:
        log_text = "Creating file '%s' from template ..." % (file_path)

    with open(file_path, "w") as f:
        logger.info(log_text)
        f.write(output)
        f.close()


def git_aggregate(folder_path: Path, config_path: Path):

    args = argparse.Namespace(
        command="aggregate",
        config=str(config_path),
        jobs=1,
        dirmatch=None,
        do_push=False,
        expand_env=False,
        env_file=None,
        force=False,
    )
    with working_directory_keeper:
        os.chdir(folder_path)
        logger.info(
            "Gitaggregate source code for %s. This can take a while ..."
            % config_path
        )
        gitaggregate_cmd.run(args)
