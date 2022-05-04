from pathlib import Path

from . import cli_runner_invoke


def test_cli_upgrade():
    return
    output_folder_path = Path("./tests/output_B").absolute()

    db_name = "database_test_cli_upgrade"
    cli_runner_invoke(
        [
            "--log-level=DEBUG",
            "--env-folder=%s" % output_folder_path,
            "run",
            "--step=1",
            "--database=%s" % db_name,
            "--init-modules=base",
            "--stop-after-init",
        ]
    )

    cli_runner_invoke(
        [
            "--log-level=DEBUG",
            "--env-folder=%s" % output_folder_path,
            "upgrade",
            "--database=%s" % db_name,
            "--first-step=1",
            # TODO : set 3 when dropping database will be done
            "--last-step=1",
        ]
    )

    # TODO, write test
