import unittest
from pathlib import Path

from . import cli_runner_invoke, move_to_test_folder


class TestCliEstimateWorkload(unittest.TestCase):
    def test_cli_estimate_workload(self):
        move_to_test_folder()

        cli_runner_invoke(
            [
                "--log-level=DEBUG",
                "estimate-workload",
                "--extra-modules="
                # Done Module
                "account"
                # Deleted module (because merged)
                ",account_analytic_default"
                # Deleted module (because renamed)
                ",account_facturx"
                # Deleted module (because lost merge)
                ",base_gengo"
                # Some modules that are not ported (for the time being)
                ",l10n_be_invoice_bba,l10n_ch_qriban,l10n_latam_base"
                # OCA Portted Modules
                ",web_responsive"
                # OCA Unported modules
                ",web_boolean_button"
                ",web_editor_background_color"
                ",web_pivot_computed_measure"
                ",web_view_calendar_list"
                ",web_widget_child_selector"
                ",web_widget_one2many_tree_line_duplicate"
                ",web_widget_dropdown_dynamic_example"
                ",my_module_that_doesnt_exist",
            ]
        )

        # We check file has been created
        # parsing this file is a mess, so we don't do it ;-)
        assert Path("./analysis.html").exists()
