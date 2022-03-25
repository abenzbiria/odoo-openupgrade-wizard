# List of the series of odoo
# python version is defined, based on the OCA CI.
# https://github.com/OCA/oca-addons-repo-template/blob/master/src/.github/workflows/%7B%25%20if%20ci%20%3D%3D%20'GitHub'%20%25%7Dtest.yml%7B%25%20endif%20%25%7D.jinja
_ODOO_SERIES = [
    {
        "version": 6.0,
        "python": "python2.7",
        "python_libraries": ["openupgradelib"],
    },
    {
        "version": 6.1,
        "python": "python2.7",
        "python_libraries": ["openupgradelib"],
    },
    {
        "version": 7.0,
        "python": "python2.7",
        "python_libraries": ["openupgradelib"],
    },
    {
        "version": 8.0,
        "python": "python2.7",
        "python_libraries": ["openupgradelib"],
    },
    {
        "version": 9.0,
        "python": "python2.7",
        "python_libraries": ["openupgradelib"],
    },
    {
        "version": 10.0,
        "python": "python2.7",
        "python_libraries": ["openupgradelib"],
    },
    {
        "version": 11.0,
        "python": "python3.5",
        "python_libraries": ["openupgradelib"],
    },
    {
        "version": 12.0,
        "python": "python3.6",
        "python_libraries": ["openupgradelib"],
    },
    {
        "version": 13.0,
        "python": "python3.6",
        "python_libraries": ["openupgradelib"],
    },
    {
        "version": 14.0,
        "python": "python3.6",
        "python_libraries": ["openupgradelib"],
    },
    {
        "version": 15.0,
        "python": "python3.8",
        "python_libraries": ["openupgradelib"],
    },
]


def _get_odoo_version_str_list(mode):
    serie_list = [x["version"] for x in _ODOO_SERIES]
    if mode == "initial":
        serie_list = serie_list[:-1]
    if mode == "final":
        serie_list = serie_list[1:]
    return [str(x) for x in serie_list]


def _get_odoo_versions(initial, final):
    result = []
    for serie in _ODOO_SERIES:
        if serie["version"] >= initial and serie["version"] <= final:
            result.append(serie)
    return result
