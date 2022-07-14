import socket
import time

import odoorpc
from loguru import logger

# Wait for the launch of odoo instance 60 seconds
_ODOO_RPC_MAX_TRY = 60


class OdooInstance:

    env = False
    version = False

    def __init__(self, ctx, database, alternative_xml_rpc_port=False):
        port = (
            alternative_xml_rpc_port
            and alternative_xml_rpc_port
            or ctx.obj["config"]["odoo_host_xmlrpc_port"]
        )
        logger.info(
            "Connect to Odoo database %s via odoorpc (Port %s)... "
            % (database, port)
        )

        for x in range(1, _ODOO_RPC_MAX_TRY + 1):
            # Connection
            try:
                rpc_connexion = odoorpc.ODOO(
                    "0.0.0.0",
                    "jsonrpc",
                    port=port,
                    timeout=ctx.obj["config"]["odoo_rpc_timeout"],
                )
                # connexion is OK
                break
            except (socket.gaierror, socket.error) as e:
                if x < _ODOO_RPC_MAX_TRY:
                    logger.debug(
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
                "Unable to connect to http://localhost:%s"
                " with login %s and password %s"
                % (
                    port,
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
