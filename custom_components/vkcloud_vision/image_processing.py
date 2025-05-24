# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""VK Cloud Vision image processing platform."""

from __future__ import annotations

import io
import os
from typing import Any, Optional, cast

from homeassistant.components.camera import async_get_image
from homeassistant.components.image_processing import \
    DOMAIN as IMAGE_PROCESSING_DOMAIN
from homeassistant.components.image_processing import ImageProcessingEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, split_entity_id
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.template import Template
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import dt as dt_util
from homeassistant.util.json import JsonArrayType, JsonObjectType
from homeassistant.util.pil import draw_box
from PIL import Image, ImageDraw

from .api.vkcloud.vision import VKCloudVision
from .const import DOMAIN, LOGGER


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

    entity_id = f"{IMAGE_PROCESSING_DOMAIN}.vkcloud_vision"
    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self) -> None:
        """Initialize the entity."""
        self._attr_name = "VK Cloud Vision"
        self._attr_unique_id = "vkcloud_vision"
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, self._attr_unique_id)},
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

    async def async_detect_objects(
        self,
        camera_id: str,
        modes: list[str],
        file_out: Optional[Template] = None
    ) -> JsonObjectType:
        """Detect objects with optional bounding box drawing."""
        entry: ConfigEntry[VKCloudVision] = self.hass.config_entries.async_loaded_entries(DOMAIN)[0]
        client: VKCloudVision = entry.runtime_data

        camera_image = await async_get_image(self.hass, camera_id)
        image_data = camera_image.content
        image_name = split_entity_id(camera_id)[1]

        try:
            response = await client.objects.detect(
                files=[image_data],
                modes=modes,
                images=[{"name": image_name}]
            )
        except Exception as err:
            raise HomeAssistantError(f"Detection error: {err}") from err

        output_path = None
        if file_out:
            try:
                output_path = file_out.async_render(variables={"camera_entity": camera_id})
                labels = self._extract_labels(response, image_name)
                await self._save_image(image_data, labels, output_path)
            except Exception as err:
                LOGGER.error("Image processing failed: %s", err)

        self._last_detection = dt_util.utcnow().isoformat()
        self.async_write_ha_state()

        return {
            "response": response,
            "file_out": output_path,
        }

    def _extract_labels(self, response: JsonObjectType, image_name: str) -> list[JsonObjectType]:
        """Extract labels from API response for specific image."""
        labels = []
        for label_type in ["multiobject_labels", "object_labels"]:
            for img_result in cast(list[JsonObjectType], response.get(label_type, [])):
                if img_result.get("name") == image_name and "labels" in img_result:
                    labels.extend(cast(JsonArrayType, img_result["labels"]))
        return labels

    async def _save_image(
        self,
        image_data: bytes,
        labels: list[dict[str, Any]],
        output_path: str
    ) -> None:
        """Draw bounding boxes and save image."""
        image = Image.open(io.BytesIO(image_data)).convert("RGB")
        draw = ImageDraw.Draw(image)
        img_width, img_height = image.size

        for label in labels:
            coord = label.get("coord")
            if coord and len(coord) == 4:
                x1, y1, x2, y2 = coord
                box = (
                    y1 / img_height,  # y_min
                    x1 / img_width,   # x_min
                    y2 / img_height,  # y_max
                    x2 / img_width    # x_max
                )
                draw_box(draw, box, img_width, img_height, label.get("eng", ""))

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        image.save(output_path)
        LOGGER.debug("Image saved: %s", output_path)
