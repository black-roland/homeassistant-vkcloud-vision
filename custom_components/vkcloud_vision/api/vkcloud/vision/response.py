"""Vision response class for VK Cloud Vision API."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from typing import List, cast

from homeassistant.util.json import JsonObjectType, JsonValueType


class VKCloudVisionResponse:
    """Class to handle and parse VK Cloud Vision API responses."""

    def __init__(self, raw_response: JsonObjectType, prob_threshold: float = 0.1):
        """Initialize with API response."""
        self._errors: List[str] = []
        self._labels: list[JsonObjectType] = []
        self._prob_threshold = prob_threshold
        self._data = self._process_response(raw_response)

    @property
    def data(self) -> JsonObjectType:
        """Return the processed API response data."""
        return self._data

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
        """Return extracted labels for the first snapshot."""
        return self._labels

    def _process_response(self, response: JsonObjectType) -> JsonObjectType:
        """Process and filter API response."""
        processed = {}
        for mode, result in response.items():
            processed[mode] = []
            first_image = True
            for image in cast(List[dict[str, JsonValueType]], result):
                image_name = image.get("name", "unknown")
                status = image.get("status", 1)

                if status != 0:
                    error = image.get("error", "unknown error")
                    self._errors.append(f"{image_name} ({mode}) {error}")

                processed_image = image.copy()
                if "labels" in image:
                    processed_image["labels"] = [
                        label for label in cast(list[JsonValueType], image["labels"])
                        if cast(dict, label).get("prob", 0) >= self._prob_threshold
                    ]

                    # FIXME: Proper parsing of multiple snapshot labels (good enough for now)
                    if first_image and len(processed_image["labels"]) > 0:
                        self._labels.extend(cast(list[JsonObjectType], processed_image["labels"]))
                        first_image = False

                processed[mode].append(processed_image)

        return processed


class VKCloudVisionFaceRecognitionResponse:
    """Parse response from /v1/persons/recognize."""

    def __init__(self, raw_response: dict):
        self._persons: list[dict] = []
        self._aliases_changed: bool = False
        self._errors: list[str] = []
        self._parse_persons(raw_response)

    @property
    def data(self) -> JsonObjectType:
        """Return the processed API response data."""
        return {
            "persons": cast(JsonValueType, self._persons),
            "aliases_changed": self._aliases_changed,
        }

    @property
    def persons(self) -> list[dict]:
        return self._persons

    @property
    def aliases_changed(self) -> bool:
        return self._aliases_changed

    @property
    def has_errors(self) -> bool:
        return bool(self._errors)

    @property
    def error_message(self) -> str | None:
        return "; ".join(self._errors) if self._errors else None

    def _parse_persons(self, response: JsonObjectType) -> None:
        objects = response.get("objects", [])
        self._aliases_changed = cast(bool, response.get("aliases_changed", False))

        if not objects:
            return

        # We only handle a single image per request
        obj = cast(List[dict], objects)[0]
        status = obj.get("status", 0)
        if status != 0:
            self._errors.append(f"{obj.get('name', 'unknown')}: {obj.get('error', 'unknown')}")

        self._persons = obj.get("persons", [])
