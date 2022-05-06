from pathlib import Path

from odoo_openupgrade_wizard.tools_odoo import get_odoo_env_path

from . import build_ctx_from_config_file, cli_runner_invoke


def test_cli_generate_module_analysis():
    output_folder_path = Path("./tests/output_B").absolute()
    db_name = "database_test_cli_cli_generate_module_analysis"

    ctx = build_ctx_from_config_file(output_folder_path)
    # identify main analysis file of openupgrade
    analysis_file_path = get_odoo_env_path(ctx, {"release": 14.0}) / Path(
        "src/openupgrade/openupgrade_scripts/scripts"
        "/base/14.0.1.3/upgrade_general_log.txt"
    )

    # This file should exist
    assert analysis_file_path.exists()

    # We remove this file and run the analysis
    analysis_file_path.unlink()

    analysis_file_path
    cli_runner_invoke(
        [
            "--log-level=DEBUG",
            "--env-folder=%s" % output_folder_path,
            "generate-module-analysis",
            "--step=2",
            "--database=%s" % db_name,
            "--modules=base",
        ]
    )

    # The file should has been recreated by the analysis command
    assert analysis_file_path.exists()
