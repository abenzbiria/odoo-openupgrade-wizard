from datetime import datetime
from pathlib import Path

import click

from odoo_openupgrade_wizard import templates
from odoo_openupgrade_wizard.tools_odoo_module import Analysis
from odoo_openupgrade_wizard.tools_system import (
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
@click.pass_context
def estimate_workload(ctx, analysis_file_path):
    # Analyse
    analysis = Analysis(ctx)

    # Make some clean to display properly
    analysis.modules = sorted(analysis.modules)

    # Render html file
    # TODO, make
    ensure_file_exists_from_template(
        Path(analysis_file_path),
        templates.ANALYSIS_TEMPLATE,
        ctx=ctx,
        analysis=analysis,
        current_date=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    )
