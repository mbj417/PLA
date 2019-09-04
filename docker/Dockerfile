# Copyright 2019 ArctosLabs
# *************************************************************

# This file is part of OSM Placement module
# All Rights Reserved to ArctosLabs Scandinavia AB

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at

#         http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# For those usages not covered by the Apache License, Version 2.0 please
# contact: xxx@arctoslabs.com
##

# Setup Alpine Linux as build image
FROM alpine:latest AS builder

ADD https://github.com/MiniZinc/MiniZincIDE/releases/download/2.3.1/MiniZincIDE-2.3.1-bundle-linux-x86_64.tgz /minizinc.tgz
#COPY MiniZincIDE-2.3.1-bundle-linux-x86_64.tgz /minizinc.tgz

RUN tar -zxf /minizinc.tgz && \
    mv /MiniZincIDE-2.3.1-bundle-linux /minizinc

FROM ubuntu:16.04

LABEL authors="Martin Björklund"

RUN apt-get --yes update \
 && apt-get --yes install git python3 python3-pip libmysqlclient-dev libssl-dev libffi-dev mysql-client vim libmpfr4 libglib2.0-0 libx11-6 libpng12-0 libharfbuzz0b libgl1-mesa-glx libpcre16-3 \
 && pip3 install pip==9.0.3

COPY requirements.txt /pla/requirements.txt

RUN pip3 install -r /pla/requirements.txt

COPY --from=builder /minizinc /minizinc

RUN mkdir /entry_data \
    && mkdir /entry_data/mzn-lib \
    && ln -s /entry_data/mzn-lib /minizinc/share/minizinc/exec

COPY . /pla

RUN pip3 install /pla

ENV OSMPLA_MESSAGE_DRIVER kafka
ENV OSMPLA_MESSAGE_HOST kafka
ENV OSMPLA_MESSAGE_PORT 9092

ENV OSMPLA_DATABASE_DRIVER mongo
ENV OSMPLA_DATABASE_URI mongodb://mongo:27017

ENV OSMPLA_SQL_DATABASE_URI sqlite:///pla_sqlite.db
ENV OSMPLA_GLOBAL_REQUEST_TIMEOUT 10
ENV OSMPLA_GLOBAL_LOGLEVEL INFO
ENV OSMPLA_VCA_HOST localhost
ENV OSMPLA_VCA_SECRET secret
ENV OSMPLA_VCA_USER admin
ENV OSMPLA_DATABASE_COMMONKEY changeme

ENV FZNEXEC "/entry_data/fzn-exec"
ENV PATH "/minizinc/bin:${PATH}"
ENV LD_LIBRARY_PATH "/minizinc/lib:${LD_LIBRARY_PATH}"

EXPOSE 1234

#HEALTHCHECK --interval=5s --timeout=2s --retries=12 \
#  CMD osm-pla-healthcheck || exit 1

CMD /bin/bash pla/docker/scripts/start.sh

#WORKDIR /minizinc
