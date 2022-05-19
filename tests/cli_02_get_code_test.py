from pathlib import Path

from . import cli_runner_invoke


def test_cli_get_code():
    output_folder_path = Path("./tests/output").absolute()

    cli_runner_invoke(
        [
            "--log-level=DEBUG",
            "--env-folder=%s" % output_folder_path,
            "get-code",
        ]
    )

    # Check V13
    openupgrade_path = output_folder_path / Path(
        "./src/env_13.0/src/openupgrade"
    )
    assert openupgrade_path.exists()

    assert (openupgrade_path / Path("odoo")).exists()

    # check V14
    openupgrade_path = output_folder_path / Path(
        "./src/env_14.0/src/openupgrade"
    )

    assert openupgrade_path.exists()

    assert (openupgrade_path / Path("openupgrade_framework")).exists()
