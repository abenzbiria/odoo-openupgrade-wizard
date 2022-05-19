from pathlib import Path

from . import cli_runner_invoke


def test_cli_execute_script_python():
    output_folder_path = Path("./tests/output").absolute()

    extra_script_path = Path(
        "./tests/extra_script/post-migration-custom_test.py"
    ).absolute()

    db_name = "database_test_cli_execute_script_python"

    # Install Odoo on V13 with product installed
    cli_runner_invoke(
        [
            "--log-level=DEBUG",
            "--env-folder=%s" % output_folder_path,
            "run",
            "--step=1",
            "--database=%s" % db_name,
            "--init-modules=product",
            "--stop-after-init",
        ]
    )

    cli_runner_invoke(
        [
            "--log-level=DEBUG",
            "--env-folder=%s" % output_folder_path,
            "execute-script-python",
            "--step=1",
            "--database=%s" % db_name,
            "--script-file-path=%s" % extra_script_path,
        ]
    )
    # TODO, add manually script
