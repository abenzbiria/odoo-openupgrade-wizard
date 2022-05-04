def main(self):

    # Classic ORM usage Checks
    partners = self.browse_by_search("res.partner")

    self.browse_by_create("res.partner", {"name": "New Partner"})

    new_partners = self.browse_by_search("res.partner")

    if len(partners) + 1 != len(new_partners):
        raise Exception("Creation of partner failed.")

    # Install / uninstall modules checks
    if self.check_modules_installed("sale"):
        self.uninstall_modules("sale")

    self.install_modules("sale")

    if not self.check_modules_installed("sale"):
        raise Exception("'sale' module should be installed")

    self.uninstall_modules(["product"])

    if self.check_modules_installed("sale"):
        raise Exception(
            "'sale' module should not be installed"
            " after uninstallation of product"
        )

    # models checks
    if not self.check_models_present("res.partner"):
        raise Exception("'res.partner' model should be present.")

    if self.check_models_present("res.partner.unexisting.model"):
        raise Exception(
            "'res.partner.unexisting.model' model" " should not be present."
        )

    #
