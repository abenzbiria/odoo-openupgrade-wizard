from odoo_openupgrade_wizard.tools.tools_postgres import (
    ensure_database,
    execute_sql_request,
)


def copydb(ctx, source, dest):
    # drop database if exist
    ensure_database(ctx, dest, state="absent")

    # Copy database
    request = f"CREATE DATABASE {dest} WITH TEMPLATE {source};"
    execute_sql_request(ctx, request)
