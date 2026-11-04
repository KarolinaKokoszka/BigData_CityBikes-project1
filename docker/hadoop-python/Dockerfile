ARG BASE_IMAGE
FROM ${BASE_IMAGE}

USER root

RUN echo 'deb http://archive.debian.org/debian stretch main' > /etc/apt/sources.list \
    && apt-get -o Acquire::Check-Valid-Until=false update \
    && apt-get install -y --no-install-recommends python3 \
    && rm -rf /var/lib/apt/lists/*
