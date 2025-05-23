# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""VK Cloud Vision image processing platform."""

from __future__ import annotations

from homeassistant.components.camera import async_get_image
from homeassistant.components.image_processing import ImageProcessingEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, split_entity_id
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import dt as dt_util
from homeassistant.util.json import JsonObjectType

from .api.vkcloud.vision import VKCloudVision
from .const import DOMAIN


def setup_platform(
    hass: HomeAssistant,
    _config: ConfigType,
    add_entities: AddEntitiesCallback,
    _discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the VK Cloud Vision image processing platform."""
    add_entities([VKCloudVisionEntity()])


class VKCloudVisionEntity(ImageProcessingEntity):
    """VK Cloud Vision image processing entity."""

    _attr_should_poll = False

    def __init__(self) -> None:
        """Initialize the entity."""
        self._attr_name = "VK Cloud Vision"
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, self._attr_name)},
            name="VK Cloud Vision",
            manufacturer="VK Cloud",
            model="Vision",
            entry_type=dr.DeviceEntryType.SERVICE,
        )
        self._last_detection = None

    @property
    def state(self) -> str | None:
        """Return the state of the entity."""
        return self._last_detection

    def process_image(self, _image: bytes) -> None:
        raise HomeAssistantError("Use `vkcloud_vision.detect_objects` instead")

    async def async_process_image(self, image: bytes) -> None:
        self.process_image(image)

    # TODO: Draw boxes? https://github.com/search?q=repo%3Ahome-assistant%2Fcore%20draw_box&type=code
    async def async_detect_objects(self, entry: ConfigEntry, camera_ids: list[str], modes: list[str]) -> JsonObjectType:
        """Detect objects."""
        client: VKCloudVision = entry.runtime_data

        files = []
        images = []
        for camera_id in camera_ids:
            camera_image = await async_get_image(self.hass, camera_id, timeout=self.timeout)
            files.append(camera_image.content)
            images.append({"name": split_entity_id(camera_id)[1]})

        try:
            result = await client.objects.detect(files=files, modes=modes, images=images)
        except Exception as err:
            raise HomeAssistantError(f"Error detecting objects: {err}") from err

        self._last_detection = dt_util.utcnow().isoformat()
        self.async_write_ha_state()

        return result
