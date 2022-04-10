# Extra Developper Requirements

If you want to contribute to this library without installing anything in your
system,

1. Run a docker container :

``docker run -it ubuntu:focal``

2. Execute the following commnands

```

apt-get update
apt-get install git python3 python3-pip python3-venv

python3 -m pip install --user pipx
python3 -m pipx ensurepath

# re-login via su root

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

## Via Gitlab Runner locally


```
pipx install gitlabci-local
curl -LJO "https://gitlab-runner-downloads.s3.amazonaws.com/latest/rpm/gitlab-runner_amd64.rpm"
sudo dpkg -i gitlab-runner_amd64.deb

# add gitlab-runner user to docker group
sudo usermod -a -G docker gitlab-runner
```

# Réferences

- how to install gitlab runner locally:

https://docs.gitlab.com/runner/install/linux-manually.html

- Check your CI locally. (French)

https://blog.stephane-robert.info/post/gitlab-valider-ci-yml/
