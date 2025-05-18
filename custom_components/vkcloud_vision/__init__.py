"""VK Cloud Vision integration"""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .api.vkcloud_vision_sdk import VKCloudVisionSDK
from .const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
)

from .api.vkcloud_vision_auth import VKCloudVisionAuth


PLATFORMS = (Platform.IMAGE_PROCESSING,)


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
