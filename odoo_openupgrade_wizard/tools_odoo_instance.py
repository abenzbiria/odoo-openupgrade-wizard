import socket
import time

import odoorpc
from loguru import logger


def get_odoo_url(ctx) -> str:
    return "http://localhost:%d" % (ctx.obj["config"]["host_odoo_xmlrpc_port"])


_ODOO_RPC_MAX_TRY = 10
_ODOO_RPC_TIMEOUT = 60


class OdooInstance:

    env = False
    version = False

    def __init__(self, ctx, database):
        # # TODO, improve me waith for response on http://localhost:port
        # # with a time out
        # # the docker container take a little time to be up.
        # time.sleep(2)

        for x in range(1, _ODOO_RPC_MAX_TRY + 1):
            # Connection
            try:
                rpc_connexion = odoorpc.ODOO(
                    "localhost",
                    "jsonrpc",
                    port=ctx.obj["config"]["host_odoo_xmlrpc_port"],
                    timeout=_ODOO_RPC_TIMEOUT,
                )
                # connexion is OK
                break
            except (socket.gaierror, socket.error) as e:
                if x < _ODOO_RPC_MAX_TRY:
                    logger.info(
                        "%d/%d Unable to connect to the server."
                        " Retrying in 1 second ..." % (x, _ODOO_RPC_MAX_TRY)
                    )
                    time.sleep(1)
                else:
                    logger.critical(
                        "%d/%d Unable to connect to the server."
                        % (x, _ODOO_RPC_MAX_TRY)
                    )
                    raise e

        # Login
        try:
            rpc_connexion.login(
                database,
                "admin",
                "admin",
            )
        except Exception as e:
            logger.error(
                "Unable to connect to %s with login %s and password %s"
                % (
                    get_odoo_url(ctx),
                    "admin",
                    "admin",
                )
            )
            raise e

        self.env = rpc_connexion.env
        self.version = rpc_connexion.version

    def browse_by_search(
        self, model_name, domain=False, order=False, limit=False
    ):
        domain = domain or []
        model = self.env[model_name]
        return model.browse(model.search(domain, order=order, limit=limit))

    def browse_by_create(self, model_name, vals):
        model = self.env[model_name]
        return model.browse(model.create(vals))

    def check_modules_installed(self, module_names) -> bool:
        if type(module_names) == str:
            module_names = [module_names]
        installed_module_ids = self.env["ir.module.module"].search(
            [
                ("name", "in", module_names),
                ("state", "=", "installed"),
            ]
        )
        return len(module_names) == len(installed_module_ids)

    def check_models_present(
        self, model_name, warning_if_not_found=True
    ) -> bool:
        if self.env["ir.model"].search([("model", "=", model_name)]):
            return True
        else:
            if warning_if_not_found:
                logger.warning(
                    "Model '%s' not found."
                    " Part of the script will be skipped." % (model_name)
                )
            return False

    def install_modules(self, module_names):
        if type(module_names) == str:
            module_names = [module_names]
        installed_modules = []
        i = 0
        for module_name in module_names:
            i += 1
            prefix = str(i) + "/" + str(len(module_names))
            modules = self.browse_by_search(
                "ir.module.module", [("name", "=", module_name)]
            )
            if not len(modules):
                logger.error(
                    "%s - Module '%s': Not found." % (prefix, module_name)
                )
                continue

            module = modules[0]
            if module.state == "installed":
                logger.info(
                    "%s - Module %s still installed."
                    " skipped." % (prefix, module_name)
                )
            elif module.state == "uninstalled":
                try_qty = 0
                installed = False
                while installed is False:
                    try_qty += 1
                    logger.info(
                        "%s - Module '%s': Installing ... %s"
                        % (
                            prefix,
                            module_name,
                            "(try #%d)" % try_qty if try_qty != 1 else "",
                        )
                    )
                    try:
                        module.button_immediate_install()
                        installed = True
                        installed_modules.append(module_name)
                        time.sleep(5)
                    except Exception as e:
                        if try_qty <= 5:
                            sleeping_time = 2 * try_qty * 60
                            logger.warning(
                                "Error. Retrying in %d seconds.\n %s"
                                % (sleeping_time, e)
                            )
                            time.sleep(sleeping_time)
                        else:
                            logger.critical(
                                "Error after %d try. Exiting.\n %s"
                                % (try_qty, e)
                            )
                            raise e
            else:
                logger.error(
                    "%s - Module '%s': In the %s state."
                    " (Unable to install)"
                    % (prefix, module_name, module.state)
                )
        return installed_modules

    def uninstall_modules(self, module_names):
        if type(module_names) == str:
            module_names = [module_names]
        i = 0
        for module_name in module_names:
            i += 1
            prefix = str(i) + "/" + str(len(module_names))
            modules = self.browse_by_search(
                "ir.module.module", [("name", "=", module_name)]
            )
            if not len(modules):
                logger.error(
                    "%s - Module '%s': Not found." % (prefix, module_name)
                )
                continue
            module = modules[0]
            if module.state in (
                "installed",
                "to upgrade",
                "to update",
                "to remove",
            ):
                logger.info(
                    "%s - Module '%s': Uninstalling .." % (prefix, module_name)
                )
                module.button_upgrade_cancel()
                module.button_uninstall()
                wizard = self.browse_by_create("base.module.upgrade", {})
                wizard.upgrade_module()

            else:
                logger.error(
                    "%s - Module '%s': In the %s state."
                    " (Unable to uninstall)"
                    % (prefix, module_name, module.state)
                )
