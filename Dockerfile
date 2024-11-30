FROM python:3.8.1-slim-buster

ENV GOSU_VERSION 1.16

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ARG HOST_USER_ID
ARG HOST_GROUP_ID
ARG DOCKER_GROUP_ID
ARG CELERY_USER_ID


RUN groupadd -g $HOST_GROUP_ID tentron \
    && useradd -r -s /bin/bash -g tentron -u $HOST_USER_ID tentron
RUN groupadd -r -g $DOCKER_GROUP_ID docker \
    && useradd -r -g docker -u $CELERY_USER_ID celery \
    && usermod -aG docker celery
RUN apt-get update --yes --quiet \
    && apt-get install --yes --quiet --no-install-recommends \
    build-essential \
    python3-dev \
    postgresql-client-11 \
    netcat \
    cron

RUN set -eux; \
# save list of currently installed packages for later so we can clean up
	savedAptMark="$(apt-mark showmanual)"; \
	apt-get update; \
	apt-get install -y --no-install-recommends ca-certificates gnupg wget; \
	rm -rf /var/lib/apt/lists/*; \
	\
	dpkgArch="$(dpkg --print-architecture | awk -F- '{ print $NF }')"; \
	wget -O /usr/local/bin/gosu "https://github.com/tianon/gosu/releases/download/$GOSU_VERSION/gosu-$dpkgArch"; \
	wget -O /usr/local/bin/gosu.asc "https://github.com/tianon/gosu/releases/download/$GOSU_VERSION/gosu-$dpkgArch.asc"; \
	\
# verify the signature
	export GNUPGHOME="$(mktemp -d)"; \
	gpg --batch --keyserver hkps://keys.openpgp.org --recv-keys B42F6819007F00F88E364FD4036A9C25BF357DD4; \
	gpg --batch --verify /usr/local/bin/gosu.asc /usr/local/bin/gosu; \
	gpgconf --kill all; \
	rm -rf "$GNUPGHOME" /usr/local/bin/gosu.asc; \
	\
# clean up fetch dependencies
	apt-mark auto '.*' > /dev/null; \
	[ -z "$savedAptMark" ] || apt-mark manual $savedAptMark; \
	apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false; \
	\
	chmod +x /usr/local/bin/gosu; \
# verify that the binary works
	gosu --version; \
	gosu nobody true

# 添加新用户，并设置 gosu 作为 entrypoint
RUN pip install --upgrade pip "gunicorn==20.0.4"


# 创建目录并设置工作目录
RUN mkdir -p /home/app && chown tentron:tentron /home/app
WORKDIR /home/app

#Install project requirements.
COPY --chown=tentron:tentron requirements.txt .
RUN pip install -r requirements.txt

# Copy the current directory contents into the container at /app
COPY --chown=tentron:tentron . .
# Copy the entrypoint shell script and give permissions to execute
COPY entrypoint.prod.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.prod.sh
ENTRYPOINT ["entrypoint.prod.sh" ]

CMD ["gunicorn", "tentron.wsgi:application", "--bind", "0.0.0.0:9000", "--workers", "3", "--timeout", "120", "--access-logfile", "/var/log/gunicorn/access.log", "--error-logfile", "/var/log/gunicorn/error.log", "--log-level", "debug"]
