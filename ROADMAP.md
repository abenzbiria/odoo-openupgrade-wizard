# TODO

* with coop it easy :
- short_help of group decorator ? seems useless...

* add constrains on ``--step`` option.


* revert : set 777 to log and filestore to be able to write on this folder
  inside the containers. TODO, ask to coop it easy or commown for better alternative.

* allow to call odoo-bin shell, via : https://github.com/d11wtq/dockerpty
  (see https://github.com/docker/docker-py/issues/247)


* ``openupgradelib`` requires a new feature psycopg2.sql since
  (21 Aug 2019)
  https://github.com/OCA/openupgradelib/commit/7408580e4469ba4b0cabb923da7facd71567a2fb
  so we pin openupgradelib==2.0.0 (21 Jul 2018)


V12 : Python 3.5.3 (default, Apr  5 2021, 09:00:41)

```
# See : https://github.com/OCA/openupgradelib/issues/248
# https://github.com/OCA/openupgradelib/issues/288
_LEGACY_OPENUPGRADELIB = (
    "git+https://github.com/OCA/openupgradelib.git"
    "@ed01555b8ae20f66b3af178c8ecaf6edd110ce75#egg=openupgradelib"
)

# List of the series of odoo
# python version is defined, based on the OCA CI.
# https://github.com/OCA/oca-addons-repo-template/blob/master/src/.github/workflows/%7B%25%20if%20ci%20%3D%3D%20'GitHub'%20%25%7Dtest.yml%7B%25%20endif%20%25%7D.jinja

```

py310 is not available, due to dependencies to ``odoorpc``
that raise an error :
``ERROR tests/cli_A_init_test.py - AttributeError: module 'collections' has no attribute 'MutableMapping'``
