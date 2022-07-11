# <OOW> : Copy of https://github.com/odoo/odoo/blob/12.0/setup/package.dfdebian

FROM debian:stretch

# 1. <OOW> Official Odoo Dockerfile.
# Removing: postgresql, locales, rsync

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update -qq &&  \
    apt-get upgrade -qq -y && \
    apt-get install -yq \
        adduser \
        dh-python \
        packaging-dev \
        postgresql-client \
        python3 \
        python3-babel \
        python3-dateutil \
        python3-decorator \
        python3-docutils \
        python3-gevent \
        python3-html2text \
        python3-pil \
        python3-jinja2 \
        python3-libsass \
        python3-lxml \
        python3-mako \
        python3-mock \
        python3-ofxparse \
        python3-passlib \
        python3-psutil \
        python3-psycopg2 \
        python3-pydot \
        python3-pyparsing \
        python3-pypdf2 \
        python3-reportlab \
        python3-requests \
        python3-serial \
        python3-suds \
        python3-tz \
        python3-usb \
        python3-vatnumber \
        python3-vobject \
        python3-werkzeug \
        python3-xlsxwriter \
    && rm -rf /var/lib/apt/lists/*

# 2. <OOW> Add 2 python dependency files and 1 debian dependency file

COPY ./src/odoo/requirements.txt /odoo_python_requirements.txt
COPY extra_python_requirements.txt /extra_python_requirements.txt
COPY extra_debian_requirements.txt /extra_debian_requirements.txt

# 3. <OOW> Install Debian packages
RUN apt-get update || true \
    && apt-get install -y\
    # <OOW> To allow to run pip install
    python3-pip\
    # <OOW> For python-ldap
    libldap2-dev ldap-utils libsasl2-dev\
    && xargs apt-get install -y --no-install-recommends <extra_debian_requirements.txt \
    && rm -rf /var/lib/apt/lists/*

# 4. <OOW> Install Python librairies
RUN python3 -m pip install --no-cache-dir -r /odoo_python_requirements.txt
RUN python3 -m pip install --no-cache-dir -r /extra_python_requirements.txt

RUN useradd --uid 1000 odoo
