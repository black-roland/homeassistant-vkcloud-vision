"""Base client for VK Cloud Vision API requests."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from typing import Any, Dict, List, Optional
import json

from aiohttp import ClientSession, FormData
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .vkcloud_vision_auth import VKCloudVisionAuth


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
            data.add_field(f"file_{i}", file_data, filename=f"image_{i}.jpg")
        data.add_field("meta", json.dumps(meta))

        url = f"{self._base_url}{endpoint}"

        # TODO: Timeout 10 seconds + retry logic
        try:
            async with self._session.post(
                url,
                params=query_params,
                data=data,
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API request failed: {response.status} {error_text}")
                result = await response.json()
                if result.get("status") in [400, 403, 500]:
                    raise Exception(f"API error: {result.get('body')}")
                return result
        except Exception as e:
            raise Exception(f"Error during API request: {e}")
