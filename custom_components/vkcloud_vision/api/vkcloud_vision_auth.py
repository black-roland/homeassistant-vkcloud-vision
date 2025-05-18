"""VK Cloud Vision OAuth authorization helper."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from datetime import datetime, timedelta
from typing import Optional

from aiohttp import ClientSession
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession


class VKCloudVisionAuth:
    def __init__(
        self,
        hass: HomeAssistant,
        client_id: str,
        client_secret: str,
        refresh_token: Optional[str] = None,
    ) -> None:
        """Initialize VK Cloud Vision authorization helper."""
        self._hass: HomeAssistant = hass
        self._client_id: str = client_id
        self._client_secret: str = client_secret
        self._refresh_token: Optional[str] = refresh_token

        self._session: ClientSession = async_get_clientsession(hass)
        self._token_url: str = "https://mcs.mail.ru/auth/oauth/v1/token"

        self._access_token: Optional[str] = None
        self._expires_at: Optional[datetime] = None

    async def get_access_token(self) -> Optional[str]:
        """Return the access token. If it exists and valid, return it. Otherwise, fetch or refresh one."""
        if self._access_token and self._expires_at and datetime.now() < self._expires_at:
            return self._access_token

        # Try to refresh the token if a refresh_token is available
        if self._refresh_token:
            return await self._refresh_access_token()

        # Otherwise, fetch a new token using client credentials
        return await self._fetch_new_token()

    async def _fetch_new_token(self) -> Optional[str]:
        """Fetch a new access token using client credentials."""
        headers = {
            "Content-Type": "application/json",
        }

        payload = {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "grant_type": "client_credentials",
        }

        try:
            async with self._session.post(
                self._token_url,
                headers=headers,
                json=payload,
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(
                        f"Failed to fetch access token: {response.status} {error_text}"
                    )

                data = await response.json()
                self._access_token = data.get("access_token")
                self._refresh_token = data.get("refresh_token")  # Store refresh token
                expires_in = 3600  # 1 hour as per VK Cloud Vision docs
                self._expires_at = datetime.now() + timedelta(seconds=expires_in - 60)  # Buffer
                return self._access_token

        except Exception as e:
            raise Exception(f"Error during token fetch: {e}")

    async def _refresh_access_token(self) -> Optional[str]:
        """Refresh the access token using the refresh token."""
        headers = {
            "Content-Type": "application/json",
        }

        payload = {
            "client_id": self._client_id,
            "refresh_token": self._refresh_token,
            "grant_type": "refresh_token",
        }

        try:
            async with self._session.post(
                self._token_url,
                headers=headers,
                json=payload,
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(
                        f"Failed to refresh access token: {response.status} {error_text}"
                    )

                data = await response.json()
                self._access_token = data.get("access_token")
                expires_in = 3600  # 1 hour as per VK Cloud Vision docs
                self._expires_at = datetime.now() + timedelta(seconds=expires_in - 60)  # Buffer
                return self._access_token

        except Exception:
            # If refresh fails, try fetching a new token
            return await self._fetch_new_token()

    def get_refresh_token(self) -> Optional[str]:
        """Return the current refresh token."""
        return self._refresh_token
