# TODO

* with coop it easy :
- short_help of group decorator ? seems useless...

* add constrains on ``--step`` option.

* revert : set 777 to log and filestore to be able to write on this folder
  inside the containers. TODO, ask to coop it easy or commown for better alternative.

* allow to call odoo-bin shell, via : https://github.com/d11wtq/dockerpty
  (see https://github.com/docker/docker-py/issues/247)


# List of the series of odoo
# python version is defined, based on the OCA CI.
# https://github.com/OCA/oca-addons-repo-template/blob/master/src/.github/workflows/%7B%25%20if%20ci%20%3D%3D%20'GitHub'%20%25%7Dtest.yml%7B%25%20endif%20%25%7D.jinja


# tips
```
# execute sql request in postgres docker
docker exec db psql --username=odoo --dbname=test_v12 -c "update res_partner set ""email"" = 'bib@bqsdfqsdf.txt';"
```

# TODO Nice To have

- Fix gitlabci-local. For the time being, it is not possible to debug
  locally. (there are extra bugs locally that doesn't occures on gitlab,
  in ``cli_B_03_run_test.py``...


- add

# Try gitlab runner

curl -LJO "https://gitlab-runner-downloads.s3.amazonaws.com/latest/deb/gitlab-runner_amd64.deb"

sudo dpkg -i gitlab-runner_amd64.deb

(https://docs.gitlab.com/runner/install/linux-manually.html)


# TODO:
- check dynamic user id with
https://github.com/camptocamp/docker-odoo-project/blob/master/bin/docker-entrypoint.sh


in modules.csv.j2 :
# TODO, this value are usefull for test for analyse between 13 and 14.
# move that values in data/extra_script/modules.csv
# and let this template with only 'base' module.



## Without postgres optimization
2022-07-13 19:42
2022-07-13 21:20

Duration : 1:37 (107)

## With postgres optimization

2022-07-13 21:52
2022-07-14 23:11

duration : 1:19 (79)

16%
