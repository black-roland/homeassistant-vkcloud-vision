"""Base client for VK Cloud Vision API requests."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from aiohttp import ClientSession, ClientTimeout, FormData
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from ..auth import VKCloudAuth

_LOGGER = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 10
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
    ) -> Dict[str, Any]:
        """Make an API request with multipart/form-data."""
        access_token = await self._auth.get_access_token()
        if not access_token:
            raise Exception("Failed to obtain access token")

        url = f"{self._base_url}{endpoint}"

        query_params = {
            "oauth_token": access_token,
            "oauth_provider": "mcs",
        }
        if params:
            query_params.update(params)

        data = self._prepare_form_data(files, meta)

        return await self._execute_request_with_retries(url, query_params, data)

    def _prepare_form_data(
        self,
        files: List[bytes],
        meta: Dict[str, Any]
    ) -> FormData:
        """Prepare multipart form data for the request."""
        data = FormData()
        for i, file_data in enumerate(files):
            data.add_field(f"image_{i}.jpg", file_data, filename=f"image_{i}.jpg")
        data.add_field("meta", json.dumps(meta))
        return data

    async def _execute_request(
        self,
        url: str,
        query_params: Dict[str, Any],
        data: FormData
    ) -> Dict[str, Any]:
        """Execute single request attempt."""
        async with self._session.post(
            url,
            params=query_params,
            data=data,
            timeout=ClientTimeout(total=DEFAULT_TIMEOUT),
        ) as response:
            if response.status >= 502 and response.status <= 504:
                raise TimeoutError()

            if response.status >= 400:
                raise Exception(f"API error: {response.status}")

            result = await response.json()
            if result.get("status") != 200:
                raise Exception(f"API error: {result.get('body')}")

            return result

    async def _execute_request_with_retries(
        self,
        url: str,
        query_params: Dict[str, Any],
        data: FormData
    ) -> Dict[str, Any]:
        """Execute request with retry logic."""
        for attempt in range(MAX_RETRIES):
            try:
                return await self._execute_request(url, query_params, data)
            except TimeoutError:
                _LOGGER.warning("Timeout occurred on attempt %d/%d", attempt + 1, MAX_RETRIES)

            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))

        raise Exception(f"Failed after {MAX_RETRIES} attempts")
