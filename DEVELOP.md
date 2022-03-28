# Requirements

TODO (poetry, etc...)

# Installation

```
git clone https://gitlab.com/odoo-openupgrade-wizard/odoo-openupgrade-wizard/
cd odoo-openupgrade-wizard
virtualenv env --python=python3.X
. ./env/bin/activate
poetry install
```
Note : ``python3.X`` should be >= to ``python3.6``


``odoo-openupgrade-wizard`` commands are now available in your virutalenv.

# Run tests

## Via pytest

This will run tests only for the current ``python3.X`` version.

(in your virtualenv)
```
poetry run pytest --cov odoo_openupgrade_wizard -v
```
## Via Tox

This will run tests for all the python versions put in the ``tox.ini`` folder.

(in your virtualenv)
```
tox
```

Note : you should have all the python versions available in your local system.

# Structure of the project
