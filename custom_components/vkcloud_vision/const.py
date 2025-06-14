"""Constants for the VK Cloud Vision integration."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging
from enum import StrEnum

DOMAIN = "vkcloud_vision"
LOGGER = logging.getLogger(__package__)

CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"
CONF_REFRESH_TOKEN = "refresh_token"

ATTR_MODES = "modes"
ATTR_FILE_OUT = "file_out"
ATTR_DETAILED = "detailed"
ATTR_NUM_SNAPSHOTS = "num_snapshots"

DEFAULT_MODES = ["multiobject"]
VALID_MODES = [
    "object",
    "object2",
    "scene",
    "car_number",
    "multiobject",
    "pedestrian",
    "selfie",
]

DEFAULT_NUM_SNAPSHOTS = 1
# TODO: Make SNAPSHOT_INTERVAL_SEC configurable
SNAPSHOT_INTERVAL_SEC = 1  # seconds between snapshots


class ResponseType(StrEnum):
    """Response types for VK Cloud Vision services."""
    ACTION_DONE = "action_done"
    ERROR = "error"
    PARTIAL_ACTION_DONE = "partial_action_done"
