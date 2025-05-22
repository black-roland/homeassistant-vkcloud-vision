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
from ..exceptions import VKCloudVisionAPIError, VKCloudVisionAuthError

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
            raise VKCloudVisionAuthError("Failed to obtain access token")

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

            # Check API status
            api_status = result.get("status")
            if api_status != 200:
                error_details = result.get("body", "No error details provided")
                raise VKCloudVisionAPIError(
                    message="API returned non-200 status",
                    http_status=response.status,
                    api_status=api_status,
                    error_details=error_details,
                )

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

            # Exponential backoff
            await asyncio.sleep(RETRY_DELAY * (2 ** attempt))

        raise VKCloudVisionAPIError(
            message=f"Failed after {MAX_RETRIES} attempts",
            error_details="Unknown error"
        )
