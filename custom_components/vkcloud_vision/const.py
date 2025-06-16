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
ATTR_DETAILED = "detailed"
ATTR_FILE_OUT = "file_out"
ATTR_BOUNDING_BOXES = "bounding_boxes"
ATTR_NUM_SNAPSHOTS = "num_snapshots"
ATTR_SNAPSHOT_INTERVAL_SEC = "snapshot_interval_sec"
ATTR_MAX_RETRIES = "max_retries"

VALID_MODES = [
    "object",
    "object2",
    "scene",
    "car_number",
    "multiobject",
    "pedestrian",
    "selfie",
]


DEFAULT_MODES = ["multiobject"]
DEFAULT_BOUNDING_BOXES = "rus"
DEFAULT_NUM_SNAPSHOTS = 1
DEFAULT_SNAPSHOT_INTERVAL_SEC = .5
DEFAULT_MAX_RETRIES = 5


class BoundingBoxesType(StrEnum):
    """Bounding boxes display options."""
    NONE = "none"
    NO_LABELS = "no_labels"
    RUS = "rus"
    ENG = "eng"


class ResponseType(StrEnum):
    """Response types for VK Cloud Vision services."""
    ACTION_DONE = "action_done"
    ERROR = "error"
    PARTIAL_ACTION_DONE = "partial_action_done"
