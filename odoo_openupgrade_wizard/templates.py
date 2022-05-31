CONFIG_YML_TEMPLATE = """
project_name: {{ project_name }}

postgres_image_name: postgres:13
postgres_container_name: {{project_name}}-db

odoo_host_xmlrpc_port: 9069
odoo_default_country_code: FR

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
odoorpc
click-odoo
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
import logging

_logger = logging.getLogger(__name__)
_logger.info("Executing post-migration.py script ...")

env = env  # noqa: F821

"""

GIT_IGNORE_CONTENT = """
*
!.gitignore
"""

MODULES_CSV_TEMPLATE = """
base,Base
account,Account Module
web_responsive,Web Responsive Module
"""

ANALYSIS_TEMPLATE = """
<html>
  <body>
    <h1>Migration Analysis</h1>
    <table border="1" width="100%">
      <thead>
        <tr>
          <th>Initial Release</th>
          <th>Final Release</th>
          <th>Project Name</th>
          <th>Analysis Date</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>{{ ctx.obj["config"]["odoo_versions"][0]["release"] }}</td>
          <td>{{ ctx.obj["config"]["odoo_versions"][-1]["release"] }}</td>
          <td>{{ ctx.obj["config"]["project_name"] }}</td>
          <td>{{ current_date }}</td>
        </tr>
      </tbody>
    </table>

    <table border="1" width="100%">
      <thead>
        <tr>
          <th> - </th>
        </tr>
      </thead>
      <tbody>
{%- for odoo_module in analysis.modules -%}
        <tr>
          <td>{{odoo_module.name}} ({{odoo_module.module_type}})
          </td>
        </tr>
{% endfor %}

      </tbody>
    </table>
  </body>
</html>
"""
