"""VK Cloud Vision integration"""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import (HomeAssistant, ServiceCall, ServiceResponse,
                                SupportsResponse)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .api.vkcloud.auth import VKCloudAuth
from .api.vkcloud.vision import VKCloudVision
from .const import (ATTR_FILENAMES, CONF_CLIENT_ID, CONF_MODES,
                    CONF_REFRESH_TOKEN, DOMAIN, VALID_MODES)

PLATFORMS = []
SERVICE_DETECT_OBJECTS = "detect_objects"


# TODO: Draw boxes? https://github.com/search?q=repo%3Ahome-assistant%2Fcore%20draw_box&type=code
async def async_setup(hass: HomeAssistant, entry: ConfigType) -> bool:
    """Set up the VK Cloud Vision integration."""

    async def detect_objects(call: ServiceCall) -> ServiceResponse:
        """Detect objects in an image."""
        filenames = call.data.get(ATTR_FILENAMES, [])
        modes = call.data.get(CONF_MODES, ["object2"])  # Default to object2 if not specified

        # Validate modes
        if not modes:
            raise HomeAssistantError("At least one mode must be selected")
        if not all(mode in VALID_MODES for mode in modes):
            raise HomeAssistantError(f"Invalid modes: {modes}. Valid modes are {VALID_MODES}")

        # Validate and read files
        files = []
        if filenames:
            for filename in filenames:
                if not hass.config.is_allowed_path(filename):
                    raise HomeAssistantError(f"Access to {filename} is not allowed")
                try:
                    with open(filename, "rb") as f:
                        files.append(f.read())
                except (FileNotFoundError, PermissionError) as e:
                    raise HomeAssistantError(f"Failed to read file {filename}: {str(e)}")
        else:
            raise HomeAssistantError("No filenames provided")

        # Get the first loaded config entry
        config_entry: ConfigEntry[VKCloudVision] = hass.config_entries.async_loaded_entries(DOMAIN)[0]
        sdk: VKCloudVision = config_entry.runtime_data

        # Prepare metadata
        images_meta = [{"name": f"image_{i}.jpg"} for i in range(len(filenames))]

        try:
            # Call the SDK to detect objects
            result = await sdk.objects.detect(
                images=files,
                images_meta=images_meta,
                modes=modes,
            )

            # Validate result status
            if result.get("status") != 200:
                raise HomeAssistantError(f"API error: {result.get('body', 'Unknown error')}")

            # Format the response

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
                vol.Optional(CONF_MODES, default=["multiobject"]): vol.All(
                    cv.ensure_list, [vol.In(VALID_MODES)]
                ),
            }
        ),
        supports_response=SupportsResponse.ONLY,
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a config entry."""
    auth_client = VKCloudAuth(
        hass, client_id=entry.data[CONF_CLIENT_ID], refresh_token=entry.data[CONF_REFRESH_TOKEN])
    sdk = VKCloudVision(hass, auth_client)
    entry.runtime_data = sdk
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
