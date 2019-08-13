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
# contact: prithiv.mohan@intel.com or adrian.hoban@intel.com

from setuptools import setup


def parse_requirements(requirements):
    with open(requirements) as f:
        return [l.strip('\n') for l in f if l.strip('\n') and not l.startswith('#') and '://' not in l]


_name = 'osm_pla'
_version_command = ('git describe --match v* --tags --long --dirty', 'pep440-git-full')
_description = 'OSM Placement Module'
_author = "Arctos Labs"
_author_email = 'hidden@arctoslabs.com'
_maintainer = 'Unknown'
_maintainer_email = 'unknown@unknown.com'
_license = 'Apache 2.0'
_url = 'https://github.com/mbj417/PLA.git'

setup(
    name=_name,
    version_command=_version_command,
    description=_description,
    long_description=open('README.rst', encoding='utf-8').read(),
    author=_author,
    author_email=_author_email,
    maintainer=_maintainer,
    maintainer_email=_maintainer_email,
    url=_url,
    license=_license,
    packages=[_name],
    package_dir={_name: _name},
    install_requires=[
        "aiokafka==0.4.*",
        "requests==2.18.*",
        "pyyaml==3.*",
        "pymysql==0.9.*",
        "osm-common",
        "n2vc"
   ],
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "osm-pla-server = osm_pla.cmd.pla_server:main",
        ]
    },
    dependency_links=[
        'git+https://osm.etsi.org/gerrit/osm/common.git#egg=osm-common@v5.0',
        'git+https://osm.etsi.org/gerrit/osm/common.git#egg=n2vc@v5.0'
    ],
    setup_requires=['setuptools-version-command']
)
