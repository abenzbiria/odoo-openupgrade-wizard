import logging

_logger = logging.getLogger(__name__)
_logger.info("click_odoo_test.py : Begin of script ...")

env = env  # noqa: F821

for i in range(0, 10):
    env["res.partner"].create({"name": "Partner #%d" % (i)})

_logger.info("click_odoo_test.py : End of script.")
