# <OOW> : Copy of https://github.com/odoo/odoo/blob/16.0/setup/package.dfsrc
FROM debian:buster

RUN apt-get update && \
    apt-get install -y locales && \
    rm -rf /var/lib/apt/lists/*

# Reconfigure locales such that postgresql uses UTF-8 encoding
RUN dpkg-reconfigure locales && \
    locale-gen C.UTF-8 && \
    /usr/sbin/update-locale LANG=C.UTF-8
ENV LC_ALL C.UTF-8

RUN apt-get update -qq &&  \
    apt-get upgrade -qq -y && \
    apt-get install \
        postgresql \
        postgresql-server-dev-all \
        postgresql-client \
        adduser \
        libldap2-dev \
        libsasl2-dev \
        python3-pip \
        python3-wheel \
        build-essential \
        python3 -y && \
    rm -rf /var/lib/apt/lists/*

# 2. <OOW> Add 2 python dependency files and 1 debian dependency file

COPY ./src/odoo/requirements.txt /odoo_python_requirements.txt
COPY extra_python_requirements.txt /extra_python_requirements.txt
COPY extra_debian_requirements.txt /extra_debian_requirements.txt

# 3. <OOW> Install Debian packages
RUN apt-get update -qq \
    && apt-get install -y git \
    && xargs apt-get install -y --no-install-recommends <extra_debian_requirements.txt \
    && rm -rf /var/lib/apt/lists/*

# 4. <OOW> Install Python librairies
RUN pip3 install --upgrade pip \
    && python3 -m pip install --no-cache-dir setuptools-scm \
    && python3 -m pip install --no-cache-dir -r /odoo_python_requirements.txt \
    && python3 -m pip install --no-cache-dir -r /extra_python_requirements.txt

# 5. <OOW> Get local user id and set it to the odoo user
ARG LOCAL_USER_ID

RUN useradd --uid $LOCAL_USER_ID odoo

USER odoo
