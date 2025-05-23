# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""VK Cloud Vision image processing platform."""

from __future__ import annotations

import io
import os
from typing import Any, Optional

from homeassistant.components.camera import async_get_image
from homeassistant.components.image_processing import ImageProcessingEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, split_entity_id
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.template import Template
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import dt as dt_util
from homeassistant.util.json import JsonObjectType
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

    async def async_detect_objects(
        self,
        entry: ConfigEntry,
        camera_ids: list[str],
        modes: list[str],
        file_out: Optional[Template] = None
    ) -> JsonObjectType:
        """Detect objects with optional bounding box drawing."""
        client: VKCloudVision = entry.runtime_data

        files = []
        images = []
        for camera_id in camera_ids:
            camera_image = await async_get_image(self.hass, camera_id, timeout=self.timeout)
            files.append(camera_image.content)
            images.append({"name": split_entity_id(camera_id)[1]})

        try:
            response = await client.objects.detect(files=files, modes=modes, images=images)
        except Exception as err:
            raise HomeAssistantError(f"Error detecting objects: {err}") from err

        # Draw bounding boxes if output path specified
        output_path = None
        if file_out:
            for i, camera_id in enumerate(camera_ids):
                image_name = split_entity_id(camera_id)[1]
                labels = []
                # Collect all labels for this image from all modes
                for label_type in ["object_labels", "multiobject_labels"]:
                    for img_result in response.get(label_type, []):
                        if img_result["name"] == image_name:
                            labels.extend(img_result["labels"])

                if labels:
                    output_path = file_out.async_render(variables={"camera_entity": camera_id})
                    await self._save_image(files[i], labels, output_path)

        self._last_detection = dt_util.utcnow().isoformat()
        self.async_write_ha_state()

        return {
            "response": response,
            "file_out": output_path,
        }

    async def _save_image(
        self,
        image_data: bytes,
        labels: list[dict[str, Any]],
        output_path: str
    ) -> None:
        """Draw bounding boxes on image and save it."""
        try:
            image = Image.open(io.BytesIO(image_data)).convert("RGB")
            img_width, img_height = image.size
            draw = ImageDraw.Draw(image)

            for label in labels:
                coord = label.get("coord")
                if coord and len(coord) == 4:
                    x1, y1, x2, y2 = coord
                    # Convert to normalized coordinates (y_min, x_min, y_max, x_max)
                    box = (
                        y1 / img_height,  # y_min
                        x1 / img_width,   # x_min
                        y2 / img_height,  # y_max
                        x2 / img_width    # x_max
                    )
                    draw_box(draw, box, img_width, img_height, label.get('eng', ''))

            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            image.save(output_path)
            LOGGER.debug("Saved processed image to: %s", output_path)

        except Exception as e:
            LOGGER.error("Error processing image: %s", str(e))
            raise
