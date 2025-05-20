"""VK Cloud Vision integration"""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import (HomeAssistant, ServiceCall, ServiceResponse,
                                SupportsResponse)
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.exceptions import HomeAssistantError

from .api.vkcloud_vision_auth import VKCloudVisionAuth
from .api.vkcloud_vision_sdk import VKCloudVisionSDK
from .const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, ATTR_FILENAMES, DOMAIN

PLATFORMS = ()
SERVICE_DETECT_OBJECTS = "detect_objects"

type VKCloudVisionConfigEntry = ConfigEntry[VKCloudVisionSDK]


async def async_setup(hass: HomeAssistant, entry: ConfigType) -> bool:

    async def detect_objects(call: ServiceCall) -> ServiceResponse:
        """Detect objects in an image."""
        filenames = call.data.get(ATTR_FILENAMES, [])

        if not filenames:
            raise HomeAssistantError("No filenames provided")

        # Validate file paths
        files = []
        for filename in filenames:
            if not hass.config.is_allowed_path(filename):
                raise HomeAssistantError(f"Access to {filename} is not allowed")
            try:
                with open(filename, "rb") as f:
                    files.append(f.read())
            except (FileNotFoundError, PermissionError) as e:
                raise HomeAssistantError(f"Failed to read file {filename}: {str(e)}")

        # Get the first loaded config entry
        config_entry: VKCloudVisionConfigEntry = hass.config_entries.async_loaded_entries(DOMAIN)[0]
        sdk: VKCloudVisionSDK = config_entry.runtime_data

        # Prepare metadata
        images = [{"name": f"image_{i}.jpg"} for i in range(len(filenames))]

        try:
            # Call the SDK to detect objects
            result = await sdk.objects.detect(
                images=files,
                images_meta=images,
                modes=["multiobject"],
            )

            # TODO: Validate result.status

            # Process object_labels, scene_labels, etc.
            return result.get("body", {})

        except Exception as e:
            raise HomeAssistantError(f"Failed to detect objects: {str(e)}")

    hass.services.async_register(
        DOMAIN,
        SERVICE_DETECT_OBJECTS,
        detect_objects,
        schema=vol.Schema(
            {
                vol.Required(ATTR_FILENAMES, default=[]): vol.All(cv.ensure_list, [cv.string]),
            }
        ),
        supports_response=SupportsResponse.ONLY,
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a config entry."""

    auth_client = VKCloudVisionAuth(
        hass, entry.data[CONF_CLIENT_ID], entry.data[CONF_CLIENT_SECRET]
    )
    sdk = VKCloudVisionSDK(hass, auth_client)

    entry.runtime_data = sdk

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
