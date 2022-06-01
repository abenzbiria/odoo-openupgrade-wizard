import filecmp
from pathlib import Path

from . import cli_runner_invoke, move_to_test_folder


def test_cli_init():
    move_to_test_folder()
    expected_folder_path = Path("../output_expected").absolute()

    cli_runner_invoke(
        [
            "--log-level=DEBUG",
            "init",
            "--project-name=test-cli",
            "--initial-release=13.0",
            "--final-release=14.0",
            "--extra-repository=OCA/web,OCA/server-tools",
        ]
    )

    assert filecmp.cmp(
        Path("config.yml"),
        expected_folder_path / Path("config.yml"),
    )
