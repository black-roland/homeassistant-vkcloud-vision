"""VK Cloud Vision integration"""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from functools import cache

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import (HomeAssistant, ServiceCall, ServiceResponse,
                                SupportsResponse)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.entity_platform import async_get_platforms
from homeassistant.helpers.typing import ConfigType

from .api.vkcloud.auth import VKCloudAuth
from .api.vkcloud.vision import VKCloudVision
from .const import (ATTR_FILE_OUT, ATTR_MODES, CONF_CLIENT_ID,
                    CONF_REFRESH_TOKEN, DOMAIN, VALID_MODES)
from .image_processing import VKCloudVisionEntity

PLATFORMS = (Platform.IMAGE_PROCESSING,)
SERVICE_DETECT_OBJECTS = "detect_objects"


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

    async def detect_objects(call: ServiceCall) -> ServiceResponse:
        """Detect objects in an image."""
        config_entry: ConfigEntry[VKCloudVision] = hass.config_entries.async_loaded_entries(DOMAIN)[0]
        vision_entity = get_vision_entity(hass)
        return await vision_entity.async_detect_objects(
            config_entry,
            call.data.get("entity_id", []),
            call.data.get(ATTR_MODES, ["multiobject"]),
            call.data.get(ATTR_FILE_OUT),
        )

    hass.services.async_register(
        DOMAIN,
        SERVICE_DETECT_OBJECTS,
        detect_objects,
        schema=cv.make_entity_service_schema({
            vol.Optional(ATTR_MODES, default=["multiobject"]): vol.All(cv.ensure_list, [vol.In(VALID_MODES)]),
            vol.Optional(ATTR_FILE_OUT): cv.template,
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
