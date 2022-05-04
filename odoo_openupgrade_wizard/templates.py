CONFIG_YML_TEMPLATE = """project_name: {{ project_name }}

host_odoo_xmlrpc_port: 9069
host_postgres_port: 9432

odoo_versions:
{% for odoo_version in odoo_versions %}
  - release: {{ odoo_version['release'] }}
{% endfor %}

migration_steps:
{% for step in steps %}
  - name: {{ step['name'] }}
    release: {{ step['release'] }}
    action: {{ step['action'] }}
    complete_name: {{ step['complete_name'] }}
{% endfor %}
"""

REPO_YML_TEMPLATE = """
##############################################################################
## Odoo Repository
##############################################################################

./src/odoo:
  defaults:
    depth: 1
  remotes:
    odoo: https://github.com/odoo/odoo
  target: odoo {{ odoo_version['release'] }}-target
  merges:
    - odoo {{ odoo_version['release'] }}

##############################################################################
## OpenUpgrade Repository
##############################################################################

./src/openupgrade:
  defaults:
    depth: 1
  remotes:
    OCA: https://github.com/OCA/OpenUpgrade
  target: OCA {{ odoo_version['release'] }}-target
  merges:
    - OCA {{ odoo_version['release'] }}

{% for org_name, repo_list in orgs.items() %}
##############################################################################
## {{ org_name }} Repositories
##############################################################################
{% for repo in repo_list %}
./src/{{ org_name }}/{{ repo }}:
  defaults:
    depth: 1
  remotes:
    {{ org_name }}: https://github.com/{{ org_name }}/{{ repo }}
  target: {{ org_name }} {{ odoo_version['release'] }}-target
  merges:
    - {{ org_name }} {{ odoo_version['release'] }}
{% endfor %}
{% endfor %}

"""

PYTHON_REQUIREMENTS_TXT_TEMPLATE = """
{%- for python_librairy in python_libraries -%}
{{ python_librairy }}
{% endfor %}
"""

DEBIAN_REQUIREMENTS_TXT_TEMPLATE = """
git
"""

ODOO_CONFIG_TEMPLATE = ""


# Technical Notes:
# - We set apt-get update || true, because for some release (at least odoo:10)
#   the command update fail, because of obsolete postgresql repository.
DOCKERFILE_TEMPLATE = """
FROM odoo:{{ odoo_version['release'] }}
MAINTAINER GRAP, Coop It Easy

# Set User root for installations
USER root

# 1. Make available files in the containers

COPY debian_requirements.txt /debian_requirements.txt

COPY python_requirements.txt /python_requirements.txt

# 2. Install extra debian packages
RUN apt-get update || true &&\
 xargs apt-get install -y --no-install-recommends <debian_requirements.txt

# 3. Install extra Python librairies
RUN {{ odoo_version["python_major_version"] }}\
 -m pip install -r python_requirements.txt

# Reset to odoo user to run the container
USER odoo
"""

PRE_MIGRATION_SQL_TEMPLATE = ""

POST_MIGRATION_PY_TEMPLATE = """
def main(self):
    pass
"""

GIT_IGNORE_CONTENT = """
*
!.gitignore
"""

MODULES_CSV_TEMPLATE = """base,Base
product,Product
web_responsive,Web Responsive Module
"""
