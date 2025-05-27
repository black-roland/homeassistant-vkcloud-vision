"""Vision response class for VK Cloud Vision API."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.


from typing import List, cast

from homeassistant.util.json import JsonObjectType, JsonValueType


class VKCloudVisionResponse:
    """Class to handle and parse VK Cloud Vision API responses."""

    def __init__(self, response: JsonObjectType):
        """Initialize with API response and image name."""
        self._raw_response = response
        self._errors: List[str] = []
        self._labels: list[JsonObjectType] = []
        self._process_response()

    @property
    def raw_response(self) -> JsonObjectType:
        """Return the raw API response."""
        return self._raw_response

    @property
    def has_errors(self) -> bool:
        """Return True if any errors were found in the response."""
        return bool(self._errors)

    @property
    def error_message(self) -> str | None:
        """Return concatenated error message or None if no errors."""
        return "; ".join(self._errors) if self._errors else None

    @property
    def labels(self) -> list[JsonObjectType]:
        """Return extracted labels for the image."""
        return self._labels

    def _process_response(self) -> None:
        """Process API response to extract labels and errors."""
        for mode, result in self._raw_response.items():
            for image in cast(List[dict[str, JsonValueType]], result):
                status = image.get("status", 1)
                if status != 0:
                    error = image.get("error", "unknown error")
                    self._errors.append(f"{mode}: {error}")

                # Extract labels from object detection results
                if "labels" in image:
                    self._labels.extend(cast(list[JsonObjectType], image["labels"]))
