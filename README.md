# odoo-openupgrade-wizard

Odoo Openupgrade Wizard is a tool that helps developpers to make major
upgrade of Odoo Community Edition. (formely OpenERP).
It works with Openupgrade OCA tools. (https://github.com/oca/openupgrade)

this tool is useful for complex migrations:
- skip several versions
- complex custom code

It will create a migration environment (with all the code available)
and provides helpers to run (and replay) migrations until it works.

## Commands

### ``odoo-openupgrade-wizard init``

```
odoo-openupgrade-wizard init\
  --initial-version=10.0\
  --final-version=12.0\
  --extra-repository=OCA/web,OCA/server-tools
```

Initialize a folder to make a migration from a 10.0 and a 12.0 database.
This will generate the following structure :

```
config.yml
log/
    2022_03_25__23_12_41__init.log
    ...
repos/
    10.0.yml
    11.0.yml
    12.0.yml
requirements/
    10.0_requirements.txt
    11.0_requirements.txt
    12.0_requirements.txt
scripts/
    step_1__update__10.0/
        pre-migration.sql
        post-migration.py
    step_2__upgrade__11.0/
        pre-migration.sql
        post-migration.py
    step_2__upgrade__12.0/
        pre-migration.sql
        post-migration.py
    step_4__update__12.0/
        pre-migration.sql
        post-migration.py
src/
```

* ``log/`` will contains all the log of the ``odoo-openupgrade-wizard``
  and the logs of the odoo instance that will be executed.


* ``repos/`` contains a file per version of odoo, that enumerates the
  list of the repositories to use to run each odoo instance.
  The syntax should respect the ``gitaggregate`` command.
  (See : https://pypi.org/project/git-aggregator/)
  Repo files are pre-generated. You can update them with your custom settings.
  (custom branches, extra PRs, git shallow options, etc...)

* ``requirements/`` contains a file per version of odoo, that enumerates the
  list of extra python librairies required to run each odoo instance.
  The syntax should respect the ``pip install -r`` command.
  (See : https://pip.pypa.io/en/stable/reference/requirements-file-format/)

* ``scripts`` contains a folder per migration step. In each step folder:
  - ``pre-migration.sql`` can contains extra SQL queries you want to execute
    before beginning the step.
  - ``post-migration.py`` can contains extra python command to execute
    after the execution of the step. (the orm will be available)

# TODO

* with coop it easy :
- short_help of group decorator ? seems useless...
