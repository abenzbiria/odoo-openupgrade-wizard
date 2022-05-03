from pathlib import Path

from . import cli_runner_invoke


def test_cli_execute_script():
    output_folder_path = Path("./tests/output_B")

    db_name = "database_test_cli_execute_script"
    cli_runner_invoke(
        [
            "--env-folder=%s" % output_folder_path,
            "run",
            "--step=1",
            "--database=%s" % db_name,
            "--init-modules=base,product",
            "--stop-after-init",
        ]
    )
    # TODO, add manually script
