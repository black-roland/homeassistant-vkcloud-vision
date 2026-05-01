"""VK Cloud Vision integration"""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from functools import cache

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import (EntityServiceResponse, HomeAssistant,
                                ServiceCall, SupportsResponse)
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.entity_platform import async_get_platforms
from homeassistant.helpers.typing import ConfigType

from .api.vkcloud.auth import VKCloudAuth
from .api.vkcloud.vision import VKCloudVision
from .const import (ATTR_BOUNDING_BOXES, ATTR_DETAILED, ATTR_FILE_OUT,
                    ATTR_MAX_RETRIES, ATTR_MODES, ATTR_NUM_SNAPSHOTS,
                    ATTR_PROB_THRESHOLD, ATTR_SNAPSHOT_INTERVAL_SEC,
                    CONF_API_KEY, CONF_CLIENT_ID,
                    CONF_FACE_RECOGNITION_SECTION, CONF_REFRESH_TOKEN,
                    CONF_TRAINING_MODE, DEFAULT_BOUNDING_BOXES,
                    DEFAULT_MAX_RETRIES, DEFAULT_MODES, DEFAULT_NUM_SNAPSHOTS,
                    DEFAULT_PROB_THRESHOLD, DEFAULT_SNAPSHOT_INTERVAL_SEC,
                    DEFAULT_TRAINING_MODE, DOMAIN, LOGGER,
                    SERVICE_DETECT_OBJECTS, SERVICE_RECOGNIZE_FACES,
                    SERVICE_RECOGNIZE_TEXT, VALID_MODES, BoundingBoxesType,
                    ResponseType)
from .image_processing import VKCloudVisionEntity

PLATFORMS = (Platform.IMAGE_PROCESSING,)
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


@cache
def get_vision_entity(hass: HomeAssistant) -> VKCloudVisionEntity:
    """Get the VK Cloud Vision entity."""
    for platform in async_get_platforms(hass, DOMAIN):
        for entity in platform.entities.values():
            if isinstance(entity, VKCloudVisionEntity):
                return entity
    raise HomeAssistantError("VK Cloud Vision entity is not setup yet")


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the VK Cloud Vision integration."""
    for platform in PLATFORMS:
        hass.async_create_task(async_load_platform(hass, platform, DOMAIN, {}, config))

    async def detect_objects(call: ServiceCall) -> EntityServiceResponse:
        """Detect objects in images from multiple cameras."""
        vision_entity = get_vision_entity(hass)

        # FIXME: Workaround to process multiple entities in a way `entity_service_call` does
        result = {}
        for camera_id in call.data.get("entity_id", []):
            try:
                result[camera_id] = await vision_entity.async_detect_objects(
                    camera_id,
                    call.data.get(ATTR_MODES, DEFAULT_MODES),
                    call.data.get(ATTR_PROB_THRESHOLD, DEFAULT_PROB_THRESHOLD),
                    call.data.get(ATTR_FILE_OUT),
                    call.data.get(ATTR_BOUNDING_BOXES, ATTR_BOUNDING_BOXES),
                    call.data.get(ATTR_NUM_SNAPSHOTS, DEFAULT_NUM_SNAPSHOTS),
                    call.data.get(ATTR_SNAPSHOT_INTERVAL_SEC, DEFAULT_SNAPSHOT_INTERVAL_SEC),
                    call.data.get(ATTR_MAX_RETRIES, DEFAULT_MAX_RETRIES),
                )
            except HomeAssistantError as err:
                result[camera_id] = {
                    "response": None,
                    "file_out": None,
                    "response_type": ResponseType.ERROR,
                    "error": str(err),
                }

        return result

    async def recognize_text(call: ServiceCall) -> EntityServiceResponse:
        """Recognize text in images from multiple cameras."""
        vision_entity = get_vision_entity(hass)
        mode = "detailed" if call.data.get(ATTR_DETAILED) else None

        # FIXME: Workaround to process multiple entities in a way `entity_service_call` does
        result = {}
        for camera_id in call.data.get("entity_id", []):
            try:
                result[camera_id] = await vision_entity.recognize_text(camera_id, mode)
            except HomeAssistantError as err:
                result[camera_id] = {
                    "response": None,
                    "response_type": ResponseType.ERROR,
                    "error": str(err),
                }

        return result

    async def recognize_faces(call: ServiceCall) -> EntityServiceResponse:
        vision_entity = get_vision_entity(hass)
        vision_entry = hass.config_entries.async_loaded_entries(DOMAIN)[0]

        face_recognition_options = vision_entry.options.get(CONF_FACE_RECOGNITION_SECTION, {})
        training_mode = face_recognition_options.get(CONF_TRAINING_MODE, DEFAULT_TRAINING_MODE)
        LOGGER.debug("Trainig mode: %s, create new: %s, update embedding: %s",
                     training_mode,
                     call.data.get("create_new", training_mode),
                     call.data.get("update_embedding", training_mode))

        result = {}
        for camera_id in call.data.get("entity_id", []):
            try:
                result[camera_id] = await vision_entity.recognize_faces(
                    camera_id,
                    call.data["space"],
                    call.data.get("create_new", training_mode),
                    call.data.get("update_embedding", training_mode),
                )
            except HomeAssistantError as err:
                result[camera_id] = {
                    "response": None,
                    "file_out": None,
                    "response_type": ResponseType.ERROR,
                    "error": str(err),
                }

        return result

    hass.services.async_register(
        DOMAIN,
        SERVICE_DETECT_OBJECTS,
        detect_objects,
        schema=cv.make_entity_service_schema({
            vol.Optional(
                ATTR_MODES, default=["multiobject"]
            ): vol.All(cv.ensure_list, [vol.In(VALID_MODES)]),
            vol.Optional(
                ATTR_PROB_THRESHOLD, default=DEFAULT_PROB_THRESHOLD
            ): vol.All(vol.Coerce(float), vol.Range(min=0.01, max=1.0)),
            vol.Optional(ATTR_FILE_OUT): cv.string,
            vol.Optional(
                ATTR_BOUNDING_BOXES, default=DEFAULT_BOUNDING_BOXES
            ): vol.In([bb.value for bb in BoundingBoxesType]),
            vol.Optional(
                ATTR_NUM_SNAPSHOTS, default=DEFAULT_NUM_SNAPSHOTS
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
            vol.Optional(
                ATTR_SNAPSHOT_INTERVAL_SEC, default=DEFAULT_SNAPSHOT_INTERVAL_SEC
            ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=10)),
            vol.Optional(
                ATTR_MAX_RETRIES, default=DEFAULT_MAX_RETRIES
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=10)),
        }),
        supports_response=SupportsResponse.ONLY,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_RECOGNIZE_TEXT,
        recognize_text,
        schema=cv.make_entity_service_schema({
            vol.Optional(ATTR_DETAILED): bool,
        }),
        supports_response=SupportsResponse.ONLY,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_RECOGNIZE_FACES,
        recognize_faces,
        schema=cv.make_entity_service_schema({
            vol.Required("space"): cv.string,
            vol.Optional("create_new"): cv.boolean,
            vol.Optional("update_embedding"): cv.boolean,
        }),
        supports_response=SupportsResponse.ONLY,
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a config entry."""

    if not entry.data.get(CONF_API_KEY):
        raise ConfigEntryAuthFailed(
            translation_domain=DOMAIN,
            translation_key="reauth_required",
            translation_placeholders={
                "github_issue_url": "https://github.com/black-roland/homeassistant-vkcloud-vision/issues/9"}
        )

    auth_client = VKCloudAuth(
        hass,
        api_key=entry.data.get(CONF_API_KEY),
        client_id=entry.data.get(CONF_CLIENT_ID),
        refresh_token=entry.data.get(CONF_REFRESH_TOKEN),
    )
    client = VKCloudVision(hass, auth_client)
    entry.runtime_data = client
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload config entry."""
    return True


# Migration (keeps old OAuth entries working until user reconfigures)
async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate config entry to version 2 (static key)."""
    if config_entry.version == 1:
        # We cannot auto-convert the key – user must reconfigure.
        # Just bump version; old data is still present so OAuth path works.
        new_data = dict(config_entry.data)
        hass.config_entries.async_update_entry(config_entry, version=2, data=new_data)
        LOGGER.info("Migrated VK Cloud Vision config entry to v2 (OAuth still works until reconfigured)")
        return True

    return False
