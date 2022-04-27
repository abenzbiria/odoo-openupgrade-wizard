# odoo-openupgrade-wizard

Odoo Openupgrade Wizard is a tool that helps developpers to make major
upgrade of Odoo Community Edition. (formely OpenERP).
It works with Openupgrade OCA tools. (https://github.com/oca/openupgrade)

this tool is useful for complex migrations:
- skip several versions
- complex custom code

It will create a migration environment (with all the code available)
and provides helpers to run (and replay) migrations until it works.

# Installation

``pipx install odoo-openupgrade-wizard``.

To develop and contribute to the library, refer to the ``DEVELOP.md`` file.

# Usage

## ``odoo-openupgrade-wizard init``

```
odoo-openupgrade-wizard init\
  --initial-release=10.0\
  --final-release=12.0\
  --project-name=my-customer-10-12\
  --extra-repository=OCA/web,OCA/server-tools
```

Initialize a folder to make a migration from a 10.0 and a 12.0 database.
This will generate the following structure :

```
config.yml
log/
    2022_03_25__23_12_41__init.log
    ...
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
    env_10.0/
        debian_requirements.txt
        Dockerfile
        odoo.cfg
        python_requirements.txt
        repos.yml
        src/
            odoo/
            openupgrade/
    env_11.0/
        ...
    env_12.0/
        ...

```

* ``log`` folder will contains all the log of the ``odoo-openupgrade-wizard``
  and the logs of the odoo instance that will be executed.

* ``scripts`` folder contains a folder per migration step. In each step folder:
  - ``pre-migration.sql`` can contains extra SQL queries you want to execute
    before beginning the step.
  - ``post-migration.py`` can contains extra python command to execute
    after the execution of the step. (the orm will be available)

* ``src`` folder contains a folder per Odoo version. In each environment folder:

    - ``repos.yml`` enumerates the list of the repositories to use to run the odoo instance.
      The syntax should respect the ``gitaggregate`` command.
      (See : https://pypi.org/project/git-aggregator/)
      Repo files are pre-generated. You can update them with your custom settings.
      (custom branches, extra PRs, git shallow options, etc...)

    - ``python_requirements.txt`` enumerates the list of extra python librairies
      required to run the odoo instance.
      The syntax should respect the ``pip install -r`` command.
      (See : https://pip.pypa.io/en/stable/reference/requirements-file-format/)

    - ``debian_requirements.txt`` enumerates the list of extra system librairies
      required to run the odoo instance.

At this step, you should change the autogenerated files.
You can use default files, if you have a very simple odoo instance without custom code,
extra repositories, or dependencies...


## ``odoo-openupgrade-wizard get-code``

```
odoo-openupgrade-wizard get-code
```

This command will simply get all the Odoo code required to run all the steps for your migration.
The code is defined in the ``repos.yml`` of each sub folders.

Note : This step could take a big while !

**Optional arguments**

if you want to update the code of some given releases, you can provide an extra parameter:

```
odoo-openupgrade-wizard get-code --releases 10.0,11.0
```

## ``odoo-openupgrade-wizard docker-build``

This will build local docker images that will be used in the following steps.

This script will pull official odoo docker images, defined in the ``Dockerfile`` of
each folder, and build a custom images on top the official one, installing inside
custom librairies defined in ``debian_requirements.txt``, ``python_requirements.txt``.

At this end of this step executing the following command
``docker images --filter "reference=odoo-openupgrade-wizard-*"`` should show a docker image per version.


```
REPOSITORY                                                 TAG       IMAGE ID       CREATED       SIZE
odoo-openupgrade-wizard-image---my-customer-10-12---12.0   latest    ef664c366208   2 weeks ago   1.39GB
odoo-openupgrade-wizard-image---my-customer-10-12---11.0   latest    24e283fe4ae4   2 weeks ago   1.16GB
odoo-openupgrade-wizard-image---my-customer-10-12---10.0   latest    9d94dce2bd4e   2 weeks ago   924MB
```

**Optional arguments**

if you want to build an image for some given releases, you can provide an extra parameter:

```
odoo-openupgrade-wizard docker-build --releases 10.0,12.0
```
