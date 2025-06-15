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
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.entity_platform import async_get_platforms
from homeassistant.helpers.typing import ConfigType

from .api.vkcloud.auth import VKCloudAuth
from .api.vkcloud.vision import VKCloudVision
from .const import (ATTR_DETAILED, ATTR_FILE_OUT, ATTR_MODES,
                    ATTR_NUM_SNAPSHOTS, ATTR_SNAPSHOT_INTERVAL_SEC,
                    CONF_CLIENT_ID, CONF_REFRESH_TOKEN, DEFAULT_MODES,
                    DEFAULT_NUM_SNAPSHOTS, DEFAULT_SNAPSHOT_INTERVAL_SEC,
                    DOMAIN, VALID_MODES, ResponseType)
from .image_processing import VKCloudVisionEntity

PLATFORMS = (Platform.IMAGE_PROCESSING,)
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

SERVICE_DETECT_OBJECTS = "detect_objects"
SERVICE_RECOGNIZE_TEXT = "recognize_text"


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
                    call.data.get(ATTR_FILE_OUT),
                    call.data.get(ATTR_NUM_SNAPSHOTS, DEFAULT_NUM_SNAPSHOTS),
                    call.data.get(ATTR_SNAPSHOT_INTERVAL_SEC, DEFAULT_SNAPSHOT_INTERVAL_SEC),
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

    hass.services.async_register(
        DOMAIN,
        SERVICE_DETECT_OBJECTS,
        detect_objects,
        schema=cv.make_entity_service_schema({
            vol.Optional(
                ATTR_MODES, default=["multiobject"]
            ): vol.All(cv.ensure_list, [vol.In(VALID_MODES)]),
            vol.Optional(ATTR_FILE_OUT): cv.string,
            vol.Optional(
                ATTR_NUM_SNAPSHOTS, default=DEFAULT_NUM_SNAPSHOTS
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
            vol.Optional(
                ATTR_SNAPSHOT_INTERVAL_SEC, default=DEFAULT_SNAPSHOT_INTERVAL_SEC
            ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=10)),
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

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a config entry."""
    auth_client = VKCloudAuth(
        hass, client_id=entry.data[CONF_CLIENT_ID], refresh_token=entry.data[CONF_REFRESH_TOKEN])
    client = VKCloudVision(hass, auth_client)
    entry.runtime_data = client
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload config entry."""
    return True
