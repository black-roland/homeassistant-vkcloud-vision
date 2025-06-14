"""Base client for VK Cloud Vision API requests."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, cast

from aiohttp import ClientSession, ClientTimeout, FormData
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util.json import JsonObjectType, JsonValueType

from ..auth import VKCloudAuth
from ..exceptions import (VKCloudVisionAPIError, VKCloudVisionAuthError,
                          VKCloudVisionDetectionError)

_LOGGER = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 10
# TODO: Make MAX_RETRIES configurable
MAX_RETRIES = 3
RETRY_DELAY = 1


class VKCloudVisionBaseClient:
    def __init__(
        self,
        hass: HomeAssistant,
        auth: VKCloudAuth,
        base_url: str = "https://smarty.mail.ru/api",
    ) -> None:
        """Initialize the base client."""
        self._hass = hass
        self._auth = auth
        self._base_url = base_url
        self._session: ClientSession = async_get_clientsession(hass)

    async def _make_request(
        self,
        endpoint: str,
        files: List[bytes],
        meta: Dict[str, Any],
        params: Optional[Dict[str, Any]] = None,
    ) -> JsonObjectType:
        """Make an API request with multipart/form-data."""
        access_token = await self._auth.get_access_token()
        if not access_token:
            raise VKCloudVisionAuthError("Failed to obtain access token")

        url = f"{self._base_url}{endpoint}"

        query_params = {
            "oauth_token": access_token,
            "oauth_provider": "mcs",
        }
        if params:
            query_params.update(params)

        return await self._execute_request_with_retries(url, query_params, files, meta)

    def _prepare_form_data(
        self, files: List[bytes], meta: Dict[str, Any]
    ) -> FormData:
        """Prepare multipart form data for the request using file names from meta."""
        if "images" not in meta or not isinstance(meta["images"], list):
            raise ValueError("meta must contain 'images' key with a list")

        images = meta["images"]
        if len(files) != len(images):
            raise ValueError("Number of files must match number of images in meta")

        names = [img.get("name") for img in images]
        if any(name is None for name in names):
            raise ValueError("All images in meta must have a 'name' key")

        if len(set(names)) != len(names):
            raise ValueError("All image names in meta must be unique")

        data = FormData()
        for file_data, name in zip(files, names):
            data.add_field(name, file_data, filename=name)

        data.add_field("meta", json.dumps(meta))
        return data

    async def _execute_request(
        self, url: str, query_params: Dict[str, Any], data: FormData
    ) -> JsonObjectType:
        """Execute single request attempt."""
        async with self._session.post(
            url, params=query_params, data=data, timeout=ClientTimeout(total=DEFAULT_TIMEOUT)
        ) as response:
            # Handle HTTP status codes
            if response.status >= 502 and response.status <= 504:
                _LOGGER.warning("Received HTTP %d, retrying", response.status)
                raise TimeoutError("Server timeout or gateway error")

            if response.status >= 400:
                error_text = await response.text()
                raise VKCloudVisionAPIError(
                    message=f"API error: HTTP {response.status}",
                    http_status=response.status,
                    error_details=error_text,
                )

            # Parse JSON response
            try:
                result = await response.json()
            except ValueError as err:
                raise VKCloudVisionAPIError(
                    message="Invalid JSON response",
                    http_status=response.status,
                    error_details=str(err),
                )

            # Check if body is present
            try:
                response_body: JsonObjectType = result["body"]
            except KeyError as err:
                raise VKCloudVisionAPIError(
                    message="No response body",
                    http_status=response.status,
                    error_details=str(err),
                )

            # Check API status
            api_status = result.get("status")
            if api_status != 200:
                error_details = str(result("body"))
                raise VKCloudVisionAPIError(
                    message="API returned non-200 status",
                    http_status=response.status,
                    api_status=api_status,
                    error_details=error_details,
                )

            # Check for image errors
            for mode, result in response_body.items():
                for image in cast(List[dict[str, JsonValueType]], result):
                    image_status = cast(int, image.get("status", 0))
                    if image_status == 0:
                        continue

                    image_name = image.get("name", "unknown")
                    raise VKCloudVisionDetectionError(
                        mode=mode,
                        image_name=cast(str, image_name),
                        detection_status=image_status,
                        partial_response=response_body,
                        error_details=image.get("error", "unknown error"),
                    )

            return response_body

    async def _execute_request_with_retries(
        self, url: str, query_params: Dict[str, Any], files: List[bytes], meta: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute request with retry logic."""
        last_error = None

        for attempt in range(MAX_RETRIES):
            data = self._prepare_form_data(files, meta)
            try:
                return await self._execute_request(url, query_params, data)
            except TimeoutError as err:
                last_error = err
                _LOGGER.warning("Timeout occurred on attempt %d/%d", attempt + 1, MAX_RETRIES)
            # VK Cloud support suggested adding retry logic to deal with
            # temporary object detection errors 🤷‍♂️ (ticket #2025060200475)
            except VKCloudVisionDetectionError as err:
                last_error = err
                _LOGGER.info(f"{err.message} occurred on attempt %d/%d", attempt + 1, MAX_RETRIES)

            # Exponential backoff
            await asyncio.sleep(RETRY_DELAY * (2 ** attempt))

        if partial_response := getattr(last_error, 'partial_response', None):
            return partial_response

        raise VKCloudVisionAPIError(
            message=f"Failed after {MAX_RETRIES} attempts",
            error_details="Unknown error",
        )
