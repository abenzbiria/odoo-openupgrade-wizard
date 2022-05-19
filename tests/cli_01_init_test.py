import filecmp
from pathlib import Path

from plumbum.cmd import mkdir

from . import cli_runner_invoke


def test_cli_init():
    output_folder_path = Path("./tests/output").absolute()
    expected_folder_path = Path("./tests/output_expected").absolute()
    mkdir([output_folder_path, "--parents"])

    cli_runner_invoke(
        [
            "--log-level=DEBUG",
            "--env-folder=%s" % output_folder_path,
            "init",
            "--project-name=test-cli",
            "--initial-release=13.0",
            "--final-release=14.0",
            "--extra-repository=OCA/web",
        ]
    )

    assert filecmp.cmp(
        output_folder_path / Path("config.yml"),
        expected_folder_path / Path("config.yml"),
    )
