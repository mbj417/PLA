..
 Copyright 2018 Whitestack, LLC
 *************************************************************

 This file is part of OSM Placement module
 All Rights Reserved to Arctoslabs

 Licensed under the Apache License, Version 2.0 (the "License"); you may
 not use this file except in compliance with the License. You may obtain
 a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 License for the specific language governing permissions and limitations
 under the License.
 For those usages not covered by the Apache License, Version 2.0 please
 contact: unknown@arctoslabs.com

OSM PLA Module
****************

PLA is a placement module for OSM.
It selects VIMs and links for placement of network services.

Components
**********

PLA module has the following components:

* PLA Server: Handles placement.

Configuration
*************

Configuration is handled by the file [pla.yaml] (osm_pla/core/pla.yaml). You can pass a personalized configuration file
through the `--config-file` flag.

Example:

    osm-pla-server --config-file your-config.yaml

Configuration variables can also be overridden through environment variables by following the convention:
OSMPLA_<SECTION>_<VARIABLE>=<VALUE>

Example:

    OSMPLA_GLOBAL_LOGLEVEL=DEBUG

Development
***********

The following is a reference for making changes to the code and testing them in a running OSM deployment.

::

    git clone https://osm.etsi.org/gerrit/osm/PLA.git
    cd PLA
    # Make your changes here
    # Build the image
    docker build -t opensourcemano/pla:develop -f docker/Dockerfile .
    # Start as service in already deployed OSM stack
    docker service create --name osm_pla --network netosm opensourcemano/pla:develop
    # Update image in a running OSM deployment
    docker service update --force --image opensourcemano/pla:develop osm_pla
    # Change a specific env variable
    docker service update --force --env-add VARIABLE_NAME=new_value osm_pla
    # View logs
    docker logs $(docker ps -qf name=osm_pla.1)


Developers
**********

* TBD, Arctos Labs

Maintainers
***********

* TBD, Arctos Labs

Contributions
*************

For information on how to contribute to OSM Placement module, please get in touch with
the developer or the maintainer.

Any new code must follow the development guidelines detailed in the Dev Guidelines
in the OSM Wiki and pass all tests.

Dev Guidelines can be found at:

    [https://osm.etsi.org/wikipub/index.php/Workflow_with_OSM_tools]
