from pathlib import Path

from . import cli_runner_invoke, move_to_test_folder


def test_cli_get_code():
    move_to_test_folder()
    cli_runner_invoke(
        [
            "--log-level=DEBUG",
            "get-code",
        ]
    )

    # Check V14
    web_path = Path("./src/env_14.0/src/OCA/web")
    assert web_path.exists()

    # check V15
    openupgrade_path = Path("./src/env_15.0/src/openupgrade")

    assert openupgrade_path.exists()

    assert (openupgrade_path / Path("openupgrade_framework")).exists()
