# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""VK Cloud Vision image processing platform."""

from __future__ import annotations

import asyncio

from homeassistant.components.camera import async_get_image
from homeassistant.components.image_processing import \
    DOMAIN as IMAGE_PROCESSING_DOMAIN
from homeassistant.components.image_processing import ImageProcessingEntity
from homeassistant.core import HomeAssistant, split_entity_id
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import dt as dt_util
from homeassistant.util.json import JsonObjectType

from .api.vkcloud.vision import VKCloudVision
from .bounding_boxes import BoundingBoxes
from .const import DOMAIN, LOGGER, BoundingBoxesType, ResponseType

DEFAULT_IMAGE_TIMEOUT = 10
MAX_IMAGE_RETRIES = 10
RETRY_IMAGE_DELAY = 1


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
        prob_threshold: float,
        file_out: str | None,
        bounding_boxes: str,
        num_snapshots: int,
        snapshot_interval_sec: float,
        max_retries: int,
    ) -> JsonObjectType:
        """Detect objects with optional bounding box drawing."""
        entry = self.hass.config_entries.async_loaded_entries(DOMAIN)[0]
        client: VKCloudVision = entry.runtime_data

        images_data = await self._async_get_images(camera_id, num_snapshots, snapshot_interval_sec)
        images_meta = [{"name": f"{split_entity_id(camera_id)[1]}_{i + 1}"} for i in range(num_snapshots)]

        try:
            response = await client.objects.detect(
                files=images_data,
                modes=modes,
                images=images_meta,
                prob_threshold=prob_threshold,
                max_retries=max_retries,
            )
        except Exception as err:
            LOGGER.exception("Detection error", exc_info=err)
            raise HomeAssistantError(f"Detection error: {err}") from err

        output_path = None
        if file_out:
            if num_snapshots > 1:
                LOGGER.debug("Multiple snapshots (%d) provided, but only the first one will be saved to %s.",
                             num_snapshots, file_out)
            try:
                boxes = BoundingBoxes(images_data[0], response.labels, BoundingBoxesType(bounding_boxes))
                output_path = await self.hass.async_add_executor_job(boxes.save_image, file_out)
            except Exception as err:
                LOGGER.error("Image processing failed: %s", err)
                raise HomeAssistantError(f"Image processing failed: {err}") from err

        self._last_detection = dt_util.utcnow().isoformat()
        self.async_write_ha_state()

        return {
            "response": response.data,
            "file_out": output_path,
            "response_type": ResponseType.PARTIAL_ACTION_DONE if response.has_errors else ResponseType.ACTION_DONE,
            "error": response.error_message,
        }

    async def recognize_text(self, camera_id: str, mode: str | None) -> JsonObjectType:
        """Recognize text in an image."""
        entry = self.hass.config_entries.async_loaded_entries(DOMAIN)[0]
        client: VKCloudVision = entry.runtime_data

        image_data = await self._async_get_image(camera_id)
        image_meta = {"name": split_entity_id(camera_id)[1]}

        try:
            response = await client.text.recognize(
                files=[image_data],
                images=[image_meta],
                mode=mode,
            )
        except Exception as err:
            raise HomeAssistantError(f"Text recognition error: {err}") from err

        self._last_detection = dt_util.utcnow().isoformat()
        self.async_write_ha_state()

        return {
            "response": response.data,
            "response_type": ResponseType.PARTIAL_ACTION_DONE if response.has_errors else ResponseType.ACTION_DONE,
            "error": response.error_message,
        }

    async def _async_get_image(self, camera_id: str) -> bytes:
        """Get a single image from camera with retry logic."""
        last_error = None

        for attempt in range(MAX_IMAGE_RETRIES):
            try:
                camera_image = await async_get_image(self.hass, camera_id)
                return camera_image.content
            except HomeAssistantError as err:
                last_error = str(err)
                LOGGER.warning("Failed to get image from %s (attempt %d/%d): %s",
                               camera_id, attempt + 1, MAX_IMAGE_RETRIES, last_error)

                if attempt < MAX_IMAGE_RETRIES - 1:
                    await asyncio.sleep(RETRY_IMAGE_DELAY * (2 ** attempt))

        raise HomeAssistantError(
            f"Failed to get image from {camera_id} after {MAX_IMAGE_RETRIES} attempts. Last error: {last_error}")

    async def _async_get_images(self, camera_id: str, num_snapshots: int, snapshot_interval_sec: float) -> list[bytes]:
        """Get multiple snapshots from camera with a small interval."""
        images_data = []

        for i in range(num_snapshots):
            image_data = await self._async_get_image(camera_id)
            images_data.append(image_data)
            if i < num_snapshots - 1:
                await asyncio.sleep(snapshot_interval_sec)

        return images_data
