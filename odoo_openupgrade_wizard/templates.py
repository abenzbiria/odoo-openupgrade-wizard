_CONFIG_YML_TEMPLATE = """migration_steps:
{% for step in steps %}
  - name: {{ step['name'] }}
    complete_name: {{ step['complete_name'] }}
    version: {{ step['version'] }}
    action: {{ step['action'] }}
    python: {{ step['python'] }}
{% endfor %}
"""

_REPO_YML_TEMPLATE = """
##############################################################################
## Odoo Repository
##############################################################################

./src/odoo:
  remotes:
    odoo: https://github.com/odoo/odoo
  target: odoo {{ version }}-target
  merges:
    - odoo {{ version }}

##############################################################################
## OpenUpgrade Repository
##############################################################################

./src/openupgrade:
  remotes:
    OCA: https://github.com/OCA/OpenUpgrade
  target: OCA {{ version }}-target
  merges:
    - OCA {{ version }}

{% for org_name, repo_list in orgs.items() %}
##############################################################################
## {{ org_name }} Repositories
##############################################################################
{% for repo in repo_list %}
./src/{{ org_name }}/{{ repo }}:
  remotes:
    {{ org_name }}: https://github.com/{{ org_name }}/{{ repo }}
  target: {{ org_name }} {{ version }}-target
  merges:
    - {{ org_name }} {{ version }}
{% endfor %}
{% endfor %}

"""

_REQUIREMENTS_TXT_TEMPLATE = """
{%- for python_librairy in python_libraries -%}
{{ python_librairy }}
{% endfor %}
"""

_PRE_MIGRATION_SQL_TEMPLATE = ""

_POST_MIGRATION_PY_TEMPLATE = """
def main(self, step):
    pass
"""
