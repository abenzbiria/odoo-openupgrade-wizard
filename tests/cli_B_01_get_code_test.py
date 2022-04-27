from pathlib import Path

from plumbum.cmd import mkdir

from . import cli_runner_invoke


def test_cli_get_code():
    output_folder_path = Path("./tests/output_B")
    mkdir([output_folder_path, "--parents"])

    # We initialize an env with only one version to avoid to git clone
    # large data
    cli_runner_invoke(
        [
            "--env-folder=%s" % output_folder_path,
            "init",
            "--project-name=test-cli",
            "--initial-release=14.0",
            "--final-release=14.0",
            "--extra-repository=OCA/web",
        ]
    )

    cli_runner_invoke(
        [
            "--env-folder=%s" % output_folder_path,
            "get-code",
        ]
    )

    openupgrade_path = output_folder_path / Path(
        "./src/env_14.0/src/openupgrade"
    )

    assert openupgrade_path.exists()

    assert (openupgrade_path / Path("openupgrade_framework")).exists()
