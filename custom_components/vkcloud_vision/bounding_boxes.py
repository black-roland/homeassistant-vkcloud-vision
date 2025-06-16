"""Utility functions for image processing in VK Cloud Vision integration."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.


import io
import os
from typing import Any, Optional

from homeassistant.exceptions import HomeAssistantError
from PIL import Image, ImageFont, UnidentifiedImageError
from PIL.ImageDraw import Draw, ImageDraw
from propcache.api import cached_property

from .const import LOGGER, BoundingBoxesType


class BoundingBoxes:
    """Helper class for image processing tasks."""

    def __init__(self, image_data: bytes, labels: list[dict[str, Any]], mode: BoundingBoxesType) -> None:
        """Initialize the BoundingBoxes class with image data and labels."""
        self.image_data = image_data
        self.labels = labels
        self.mode = mode

    @cached_property
    def _font(self) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        try:
            font_path = os.path.join(os.path.dirname(__file__), "fonts", "Tuffy_Bold.ttf")
            return ImageFont.truetype(font_path, 20)
        except Exception as err:
            LOGGER.warning("Failed to load custom font: %s. Using default font.", err)
            return ImageFont.load_default()

    def save_image(self, output_path: str) -> str:
        """Draw bounding boxes with labels and save image."""
        try:
            image = Image.open(io.BytesIO(self.image_data)).convert("RGB")
        except UnidentifiedImageError as err:
            raise HomeAssistantError("Unable to process image: bad data") from err

        draw = Draw(image)

        if self.mode != BoundingBoxesType.NONE:
            for label in self.labels:
                coord = label.get("coord")
                if not coord:
                    continue

                text = None
                if self.mode == BoundingBoxesType.RUS:
                    text = label.get("rus")
                elif self.mode == BoundingBoxesType.ENG:
                    text = label.get("eng")

                self._draw_box(draw, tuple(coord), text, label.get("prob", 0))

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        image.save(output_path)
        LOGGER.debug("Image saved: %s", output_path)

        return output_path

    def _draw_box(
        self,
        draw: ImageDraw,
        coord: tuple[int, int, int, int],
        text_label: Optional[str] = None,
        probability: float = 0,
        color: tuple[int, int, int] = (255, 255, 0),
    ) -> None:
        """Draw a bounding box on an image using direct coordinates.

        Args:
            draw: ImageDraw object
            coord: Tuple of (x1, y1, x2, y2) coordinates
            text: Label text to display
            color: RGB color tuple for the box
        """
        line_width = 3
        font_height = 20
        x1, y1, x2, y2 = coord

        # Draw the bounding box
        draw.rectangle([x1, y1, x2, y2], outline=color, width=line_width)

        # Draw the label if text is provided
        if text_label:
            text = f"{text_label} {probability:.0%}" if probability else text_label

            draw.text(
                (x1, y1 - line_width - font_height),
                text,
                fill=color,
                font=self._font,
                font_size=font_height,
            )
