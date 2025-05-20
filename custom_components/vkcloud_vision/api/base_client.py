"""Base client for VK Cloud Vision API requests."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from aiohttp import ClientError, ClientSession, FormData
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .vkcloud_vision_auth import VKCloudVisionAuth

_LOGGER = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 10
MAX_RETRIES = 3
RETRY_DELAY = 1


class BaseVKCloudVisionClient:
    def __init__(
        self,
        hass: HomeAssistant,
        auth: VKCloudVisionAuth,
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
    ) -> Dict[str, Any]:
        """Make an API request with multipart/form-data."""
        access_token = await self._auth.get_access_token()
        if not access_token:
            raise Exception("Failed to obtain access token")

        # Prepare query parameters
        query_params = {
            "oauth_token": access_token,
            "oauth_provider": "mcs",
        }
        if params:
            query_params.update(params)

        # Prepare multipart form data
        data = FormData()
        for i, file_data in enumerate(files):
            data.add_field(f"image_{i}.jpg", file_data, filename=f"image_{i}.jpg")
        data.add_field("meta", json.dumps(meta))

        url = f"{self._base_url}{endpoint}"
        last_error = None

        for attempt in range(MAX_RETRIES):
            try:
                async with asyncio.timeout(DEFAULT_TIMEOUT):
                    async with self._session.post(
                        url,
                        params=query_params,
                        data=data,
                        raise_for_status=True,
                    ) as response:
                        result = await response.json()
                        if result.get("status") != 200:
                            raise Exception(f"API error: {result.get('body')}")
                        return result

            except asyncio.TimeoutError:
                last_error = f"Request timed out after {DEFAULT_TIMEOUT} seconds"
                _LOGGER.warning(
                    "Timeout occurred on attempt %d/%d", attempt + 1, MAX_RETRIES
                )
            except ClientError as err:
                last_error = f"Client error: {str(err)}"
                _LOGGER.warning(
                    "Client error occurred on attempt %d/%d: %s",
                    attempt + 1,
                    MAX_RETRIES,
                    str(err),
                )
            except Exception as err:
                last_error = f"Unexpected error: {str(err)}"
                _LOGGER.warning(
                    "Error occurred on attempt %d/%d: %s",
                    attempt + 1,
                    MAX_RETRIES,
                    str(err),
                )

            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))

        raise Exception(
            f"Failed after {MAX_RETRIES} attempts. Last error: {last_error}"
        )
