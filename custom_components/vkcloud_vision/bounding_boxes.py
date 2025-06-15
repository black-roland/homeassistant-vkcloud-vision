"""Utility functions for image processing in VK Cloud Vision integration."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.


import io
import os
from typing import Any

from homeassistant.exceptions import HomeAssistantError
from PIL import Image, ImageFont, UnidentifiedImageError
from PIL.ImageDraw import Draw, ImageDraw

from .const import LOGGER


class BoundingBoxes:
    """Helper class for image processing tasks."""

    def __init__(self, image_data: bytes, labels: list[dict[str, Any]]) -> None:
        """Initialize the BoundingBoxes class with image data and labels."""
        self.image_data = image_data
        self.labels = labels

    def save_image(self, output_path: str) -> str:
        """Draw bounding boxes with labels and save image."""
        try:
            image = Image.open(io.BytesIO(self.image_data)).convert("RGB")
        except UnidentifiedImageError as err:
            raise HomeAssistantError("Unable to process image: bad data") from err

        draw = Draw(image)

        for label in self.labels:
            coord = label.get("coord")
            if coord and len(coord) == 4:
                self._draw_box(draw, tuple(coord), label.get("rus", ""))

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        image.save(output_path)
        LOGGER.debug("Image saved: %s", output_path)

        return output_path

    def _draw_box(
        self,
        draw: ImageDraw,
        coord: tuple[int, int, int, int],
        text: str = "",
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
        draw.rectangle(
            [x1, y1, x2, y2],
            outline=color,
            width=line_width
        )

        # Draw the label if text is provided
        if text:
            try:
                font_path = os.path.join(os.path.dirname(__file__), "fonts", "Tuffy_Bold.ttf")
                font = ImageFont.truetype(font_path, 20)
            except Exception as err:
                LOGGER.warning("Failed to load custom font: %s. Using default font.", err)
                font = ImageFont.load_default()

            draw.text(
                (x1 + line_width, y1 - line_width - font_height),
                text,
                fill=color,
                font=font,
                font_size=font_height,
            )
