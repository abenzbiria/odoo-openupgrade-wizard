from datetime import datetime
from pathlib import Path

import click

from odoo_openupgrade_wizard.tools.tools_odoo import get_odoo_modules_from_csv
from odoo_openupgrade_wizard.tools.tools_odoo_module import Analysis
from odoo_openupgrade_wizard.tools.tools_system import (
    ensure_file_exists_from_template,
)


@click.command()
@click.option(
    "--analysis-file-path",
    type=click.Path(
        dir_okay=False,
    ),
    default="./analysis.html",
)
@click.option(
    "--extra-modules",
    "extra_modules_list",
    # TODO, add a callback to check the quality of the argument
    help="Coma separated modules to analyse. If not set, the modules.csv"
    " file will be used to define the list of module to analyse."
    "Ex: 'account,product,base'",
)
@click.pass_context
def estimate_workload(ctx, analysis_file_path, extra_modules_list):
    # Analyse
    analysis = Analysis(ctx)

    if extra_modules_list:
        module_list = extra_modules_list.split(",")
    else:
        module_list = get_odoo_modules_from_csv(ctx.obj["module_file_path"])

    analysis.analyse_module_version(ctx, module_list)
    analysis.analyse_missing_module()
    analysis.analyse_openupgrade_state(ctx)
    analysis.estimate_workload(ctx)

    # Make some clean to display properly
    analysis.modules = sorted(analysis.modules)

    # Render html file
    ensure_file_exists_from_template(
        Path(analysis_file_path),
        "analysis.html.j2",
        ctx=ctx,
        analysis=analysis,
        current_date=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    )
