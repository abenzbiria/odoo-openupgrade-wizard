# Python Version

* py310 is not available, due to dependencies to ``odoorpc`` that raise an error :
  ``ERROR tests/cli_A_init_test.py - AttributeError: module 'collections' has no attribute 'MutableMapping'``
  Follow bug : https://stackoverflow.com/questions/69512672/getting-attributeerror-module-collections-has-no-attribute-mutablemapping-w

# openUpgradelib Versions

* ``openupgradelib`` requires a new feature psycopg2.sql since
  (21 Aug 2019)
  https://github.com/OCA/openupgradelib/commit/7408580e4469ba4b0cabb923da7facd71567a2fb
  so we pin openupgradelib==2.0.0 (21 Jul 2018)

The python version in the Odoo:12 docker image is : ``Python 3.5.3 (default, Apr  5 2021, 09:00:41)`` that is very old.


- https://github.com/OCA/openupgradelib/issues/248
- https://github.com/OCA/openupgradelib/issues/288
- https://github.com/OCA/openupgradelib.git@ed01555b8ae20f66b3af178c8ecaf6edd110ce75#egg=openupgradelib

TODO : Fix via another way (other way than pining ``openuppgradelib`` version) the problem of old odoo versions. (it makes the upgrade failing for old revision (V8, etc...))

# Gitlab-CI

* for the time being, Features requiring ``odoorpc`` are failing in gitlab-CI.
  Tests are working locally but there is a network problem. For that reason, tests witch names
  begins by ``cli_2`` like (``cli_20_install_from_csv_test.py``) are disabled in ``.gitlab-ci.yml``.

TODO : work with Pierrick Brun, to run gitlab-runner on Akretion CI (without docker), to see if it is
fixing the problem.

# Features Work In Progress

* Add a tools to analyze workload.

# Possible Improvments

* select ``without-demo all`` depending on if the database
  is created or not (and if current database contains demo data, checking if base.user_demo exists ?)

# Other points not in the scope of GRAP work

* Allow to use custom docker images.

* Check if there are default values for containers, limiting ressources.
