[![Gitlab CI](https://gitlab.com/odoo-openupgrade-wizard/odoo-openupgrade-wizard/badges/main/pipeline.svg)](https://gitlab.com/odoo-openupgrade-wizard/odoo-openupgrade-wizard/-/pipelines)
[![codecov](https://gitlab.com/odoo-openupgrade-wizard/odoo-openupgrade-wizard/badges/main/coverage.svg)](https://gitlab.com/odoo-openupgrade-wizard/odoo-openupgrade-wizard/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)



# odoo-openupgrade-wizard

Odoo Openupgrade Wizard is a tool that helps developpers to make major
upgrade of Odoo Community Edition. (formely OpenERP).
It works with Openupgrade OCA tools. (https://github.com/oca/openupgrade)

this tool is useful for complex migrations:
- migrate several versions
- take advantage of the migration to install / uninstall modules
- execute sql requests or odoo shell scripts between each migration
- analyse workload

It will create a migration environment (with all the code available)
and provides helpers to run (and replay) migrations until it works.

* To develop and contribute to the library, refer to the ``DEVELOP.md`` file.
* Refer to the ``ROADMAP.md`` file to see the current limitation, bugs, and task to do.
* See authors in the ``CONTRIBUTORS.md`` file.

# Installation

**Prerequites:**

* The tools run on debian system
* You should have docker installed on your system
* Some features require extra packages. To have all the features available run:

**Installation:**

The library is available on [PyPI](https://pypi.org/project/odoo-openupgrade-wizard/).

To install it simply run :

``pipx install odoo-openupgrade-wizard``

(See alternative installation in ``DEVELOP.md`` file.)

# Usage

**Note:**

the term ``odoo-openupgrade-wizard`` can be replaced by ``oow``
in all the command lines below.

## Command: ``init``

```
odoo-openupgrade-wizard init\
  --initial-version=10.0\
  --final-version=12.0\
  --project-name=my-customer-10-12\
  --extra-repository=OCA/web,OCA/server-tools
```

Initialize a folder to make a migration from a 10.0 and a 12.0 database.
This will generate the following structure :

```
filestore/
log/
    2022_03_25__23_12_41__init.log
    ...
postgres_data/
scripts/
    step_1__update__10.0/
        pre-migration.sql
        post-migration.py
    step_2__upgrade__11.0/
        ...
    step_3__upgrade__12.0/
        ...
    step_4__update__12.0/
        ...
src/
    env_10.0/
        extra_debian_requirements.txt
        Dockerfile
        odoo.conf
        extra_python_requirements.txt
        repos.yml
        src/
    env_11.0/
        ...
    env_12.0/
        ...
config.yml
modules.csv
```

* ``config.yml`` is the main configuration file of your project.

* ``modules.csv`` file is an optional file. You can fill it with the list
  of your modules installed on your production. The first column of this
  file should contain the technical name of the module.

* ``log`` folder will contains all the log of the ``odoo-openupgrade-wizard``
  and the logs of the odoo instance that will be executed.

* ``filestore`` folder will contains the filestore of the odoo database(s)

* ``postgres_data`` folder will be used by postgres docker image to store
  database.

* ``scripts`` folder contains a folder per migration step. In each step folder:
  - ``pre-migration.sql`` can contains extra SQL queries you want to execute
    before beginning the step.
  - ``post-migration.py`` can contains extra python command to execute
    after the execution of the step.
    Script will be executed with ``odoo shell`` command. All the ORM is available
    via the ``env`` variable.

* ``src`` folder contains a folder per Odoo version. In each environment folder:

    - ``repos.yml`` enumerates the list of the repositories to use to run the odoo instance.
      The syntax should respect the ``gitaggregate`` command.
      (See : https://pypi.org/project/git-aggregator/)
      Repo files are pre-generated. You can update them with your custom settings.
      (custom branches, extra PRs, git shallow options, etc...)

    - ``extra_python_requirements.txt`` enumerates the list of extra python librairies
      required to run the odoo instance.
      The syntax should respect the ``pip install -r`` command.
      (See : https://pip.pypa.io/en/stable/reference/requirements-file-format/)

    - ``extra_debian_requirements.txt`` enumerates the list of extra system librairies
      required to run the odoo instance.

    - ``odoo.conf`` file. Add here extra configuration required for your custom modules.
      the classical keys (``db_host``, ``db_port``, etc...) are automatically
      autogenerated.

At this step, you should change the autogenerated files.
You can use default files, if you have a very simple odoo instance without custom code,
extra repositories, or dependencies...

**Note:**
- In your repos.yml, preserve ``openupgrade`` and ``server-tools`` repositories
  to have all the features of the librairies available.

## Command: ``pull-submodule``

**Prerequites:** init

if you already have a repos.yml file on github / gitlab, it can be convenient to
synchronize the repository, instead of copy past the ``repos.yml`` manually.

In that case, you can add extra values, in the ``config.yml`` file in the section

```
odoo_version_settings:
  12.0:
      repo_url: url_of_the_repo_that_contains_a_repos_yml_file
      repo_branch: 12.0
      repo_file_path: repos.yml
```

then run following command :

```
odoo-openupgrade-wizard pull-submodule
```

## Command: ``get-code``

**Prerequites:** init

```
odoo-openupgrade-wizard get-code
```

This command will simply get all the Odoo code required to run all the steps
for your migration with the ``gitaggregate`` tools.

The code is defined in the ``repos.yml`` of each environment folders. (or in the
directory ``repo_submodule`` if you use ``pull-submodule`` feature.)

**Note**

* This step could take a big while !

**Optional arguments**

if you want to update the code of some given versions, you can provide an extra parameter:

```
odoo-openupgrade-wizard get-code --versions 10.0,11.0
```



## Command: ``docker-build``

**Prerequites:** init + get-code

This will build local docker images that will be used in the following steps.

At this end of this step executing the following command should show a docker image per version.


```
$ docker images --filter "reference=odoo-openupgrade-wizard-*"

REPOSITORY                                                 TAG       IMAGE ID       CREATED       SIZE
odoo-openupgrade-wizard-image---my-customer-10-12---12.0   latest    ef664c366208   2 weeks ago   1.39GB
odoo-openupgrade-wizard-image---my-customer-10-12---11.0   latest    24e283fe4ae4   2 weeks ago   1.16GB
odoo-openupgrade-wizard-image---my-customer-10-12---10.0   latest    9d94dce2bd4e   2 weeks ago   924MB
```

**Optional arguments**

* if you want to (re)build an image for some given versions, you can provide
  an extra parameter: ``--versions 10.0,12.0``

**Note**

* This step could take a big while also !



## Command: ``run`` (BETA)

**Prerequites:** init + get-code + build

```
odoo-openupgrade-wizard run\
    --step 1\
    --database DB_NAME
```

Run an Odoo instance with the environment defined by the step argument.

The database will be created, if it doesn't exists.

if ``stop-after-init`` is disabled, the odoo instance will be available
at your host, at the following url : http://localhost:9069
(Port depends on your ``host_odoo_xmlrpc_port`` setting of your ``config.yml`` file)

**Optional arguments**

* You can add ``--init-modules=purchase,sale`` to install modules.

* You can add ``stop-after-init`` flag to turn off the process at the end
  of the installation.



## Command: ``install-from-csv``

**Prerequites:** init + get-code + build

```
odoo-openupgrade-wizard install-from-csv\
    --database DB_NAME
```

Install the list of the modules defined in your ``modules.csv`` files on the
given database.

The database will be created, if it doesn't exists.

To get a correct ``modules.csv`` file, the following query can be used:
```
psql -c "copy (select name, shortdesc from ir_module_module where state = 'installed' order by 1) to stdout csv" coopiteasy
```



## Command: ``upgrade`` (BETA)

**Prerequites:** init + get-code + build

```
odoo-openupgrade-wizard upgrade\
    --database DB_NAME
```

Realize an upgrade of the database from the initial version to
the final version, following the different steps.

For each step, it will :

1. Execute the ``pre-migration.sql`` of the step.
2. Realize an "update all" (in an upgrade or update context)
3. Execute the scripts via XML-RPC (via ``odoorpc``) defined in
   the ``post-migration.py`` file.

**Optional arguments**

* You can add ``--first-step=2`` to start at the second step.

* You can add ``--last-step=3`` to end at the third step.



## Command: ``generate-module-analysis`` (BETA)

**Prerequites:** init + get-code + build

```
odoo-openupgrade-wizard generate-module-analysis\
    --database DB_NAME
    --step 2
    --modules MODULE_LIST
```

Realize an analyze between the target version (in parameter via the step argument)
and the previous version. It will generate analysis_file.txt files present
in OpenUpgrade project.
You can also use this fonction to analyze differences for custom / OCA modules
between several versions, in case of refactoring.


## Command: ``estimate-workload``

**Prerequites:** init + get-code

```
odoo-openupgrade-wizard estimate-workload
```

Generate an HTML file name ``analysis.html`` with all the information regarding
the work to do for the migration.
- checks that the modules are present in each version. (by managing the
  renaming or merging of modules)
- check that the analysis and migration have been done for the official
  modules present in odoo/odoo
