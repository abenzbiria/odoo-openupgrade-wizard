# Unused for the time being

# def _check_orm_usage(self):
#     # Classic ORM usage Checks
#     partners = self.browse_by_search("res.partner")

#     self.browse_by_create("res.partner", {"name": "New Partner"})

#     new_partners = self.browse_by_search("res.partner")

#     if len(partners) + 1 != len(new_partners):
#         raise Exception("Creation of partner failed.")


# def _check_modules(self):
#     if self.check_modules_installed("sale"):
#         self.uninstall_modules("sale")

#     self.install_modules("sale")

#     if not self.check_modules_installed("sale"):
#         raise Exception("'sale' module should be installed")

#     self.uninstall_modules(["product"])

#     if self.check_modules_installed("sale"):
#         raise Exception(
#             "'sale' module should not be installed"
#             " after uninstallation of product"
#         )


# def _check_models(self):
#     if not self.check_models_present("res.partner"):
#         raise Exception("'res.partner' model should be present.")

#     if self.check_models_present("res.partner.unexisting.model"):
#         raise Exception(
#             "'res.partner.unexisting.model' model" " should not be present."
#         )


# def main(self):
#     _check_orm_usage(self)
#     _check_modules(self)
#     _check_models(self)
