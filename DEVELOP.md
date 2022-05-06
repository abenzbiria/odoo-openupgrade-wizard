# Extra Developper Requirements

If you want to use this library without installing anything in your
system, execute the following steps, otherwise, go to 'Installation' part.

1. Run a docker container:

``docker run -it ubuntu:focal``

2. Execute the following commnands

```

apt-get update
apt-get install git python3 python3-pip python3-venv

python3 -m pip install --user pipx
python3 -m pipx ensurepath

su root

pipx install virtualenv
pipx install poetry
```

# Installation

```
git clone https://gitlab.com/odoo-openupgrade-wizard/odoo-openupgrade-wizard/
cd odoo-openupgrade-wizard
virtualenv env --python=python3
. ./env/bin/activate
poetry install
```

``odoo-openupgrade-wizard`` commands are now available in your virutalenv.

# Add python dependencies

If you add new dependencies, you have to:

- add the reference in the file ``pyproject.toml``

- run the following command in your virtualenv : ``poetry update``

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


```
sudo apt-get install python3.6  python3.6-distutils
sudo apt-get install python3.7  python3.7-distutils
sudo apt-get install python3.8  python3.8-distutils
sudo apt-get install python3.9  python3.9-distutils
```

## Via Gitlab Runner locally


```
# Install tools
pipx install gitlabci-local

# Run new available command
gitlabci-local
```

# Réferences

- how to install gitlab runner locally:

https://docs.gitlab.com/runner/install/linux-manually.html

- Check your CI locally. (French)

https://blog.stephane-robert.info/post/gitlab-valider-ci-yml/

https://blog.callr.tech/building-docker-images-with-gitlab-ci-best-practices/
