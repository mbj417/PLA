# Copyright 2019 Arctoslabs Scandinava AB
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
# contact: unknown@arctoslabs.com
##

all: clean package

clean:
	rm -rf dist deb_dist osm_pla-*.tar.gz osm_pla.egg-info .eggs

package:
	python3 setup.py --command-packages=stdeb.command sdist_dsc
	cp debian/python3-osm-pla.postinst deb_dist/osm-pla*/debian
	cd deb_dist/osm-pla*/  && dpkg-buildpackage -rfakeroot -uc -us
