"""Constants for the VK Cloud Vision integration."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging

DOMAIN = "vkcloud_vision"
LOGGER = logging.getLogger(__package__)

CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"
CONF_REFRESH_TOKEN = "refresh_token"

ATTR_MODES = "modes"
ATTR_FILE_OUT = "file_out"
ATTR_DETAILED = "detailed"

VALID_MODES = [
    "object",
    "object2",
    "scene",
    "car_number",
    "multiobject",
    "pedestrian",
    "selfie",
]
