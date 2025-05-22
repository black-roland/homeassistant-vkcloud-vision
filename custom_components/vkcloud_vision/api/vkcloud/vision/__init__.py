# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from homeassistant.core import HomeAssistant

from .clients import VKCloudVisionObjectsClient
from ..auth import VKCloudAuth


class VKCloudVision:
    """SDK for VK Cloud Vision API."""

    def __init__(
        self,
        hass: HomeAssistant,
        auth: VKCloudAuth,
    ) -> None:
        """Initialize the VK Cloud Vision SDK."""
        self._hass = hass
        self._auth = auth

        # Initialize feature-specific clients
        # self.persons = PersonsClient(self._hass, self._auth, self._oauth_provider)
        self.objects = VKCloudVisionObjectsClient(self._hass, self._auth)
        # self.docs = DocsClient(self._hass, self._auth, self._oauth_provider)
        # self.text = TextClient(self._hass, self._auth, self._oauth_provider)
        # self.photo = PhotoClient(self._hass, self._auth, self._oauth_provider)
        # self.adult = AdultClient(self._hass, self._auth, self._oauth_provider)
