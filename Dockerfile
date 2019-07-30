# Copyright 2017 Intel Research and Development Ireland Limited
# *************************************************************

# This file is part of OSM Placement module
# All Rights Reserved to Intel Corporation

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

#__author__ = "Martin Björklund"
#__date__   = "30/Jul/2019"

FROM ubuntu:16.04
RUN  apt-get update && \
  DEBIAN_FRONTEND=noninteractive apt-get --yes install git tox make python-all python3 python3-pip debhelper wget && \
  DEBIAN_FRONTEND=noninteractive apt-get --yes install libmysqlclient-dev libxml2 python3-all libssl-dev && \
  DEBIAN_FRONTEND=noninteractive pip3 install -U setuptools setuptools-version-command stdeb
