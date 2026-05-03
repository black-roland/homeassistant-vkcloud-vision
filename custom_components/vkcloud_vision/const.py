"""Constants for the VK Cloud Vision integration."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging
from enum import StrEnum

DOMAIN = "vkcloud_vision"
LOGGER = logging.getLogger(__package__)

# Static API key
CONF_API_KEY = "api_key"

# Keep the old ones for migration (they will be removed from new entries)
CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"
CONF_REFRESH_TOKEN = "refresh_token"

ATTR_MODES = "modes"
ATTR_PROB_THRESHOLD = "prob_threshold"
ATTR_LANG = "lang"
ATTR_FILE_OUT = "file_out"
ATTR_BOUNDING_BOXES = "bounding_boxes"
ATTR_NUM_SNAPSHOTS = "num_snapshots"
ATTR_SNAPSHOT_INTERVAL_SEC = "snapshot_interval_sec"
ATTR_MAX_RETRIES = "max_retries"
ATTR_SPACE = "space"
ATTR_CREATE_NEW = "create_new"
ATTR_UPDATE_EMBEDDING = "update_embedding"
ATTR_CONFIDENCE_THRESHOLD = "confidence_threshold"

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
DEFAULT_PROB_THRESHOLD = 0.1
DEFAULT_CONFIDENCE_THRESHOLD = 0.1
DEFAULT_BOUNDING_BOXES = "rus"
DEFAULT_NUM_SNAPSHOTS = 1
DEFAULT_SNAPSHOT_INTERVAL_SEC = .5
DEFAULT_MAX_RETRIES = 5
DEFAULT_SPACE = 0
DEFAULT_CREATE_NEW = False
DEFAULT_TRAINING_MODE = False

CONF_TRAINING_MODE = "training_mode"
CONF_TRUNCATE_SPACE = "truncate_space"
CONF_CONFIRM_TRUNCATE = "confirm_truncate"

SERVICE_DETECT_OBJECTS = "detect_objects"
SERVICE_RECOGNIZE_TEXT = "recognize_text"
SERVICE_RECOGNIZE_FACES = "recognize_faces"


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
