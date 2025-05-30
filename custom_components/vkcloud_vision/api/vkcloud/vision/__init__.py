# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from homeassistant.core import HomeAssistant

from ..auth import VKCloudAuth
from .clients import VKCloudVisionObjectsClient, VKCloudVisionTextClient


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

        self.objects = VKCloudVisionObjectsClient(self._hass, self._auth)
        self.text = VKCloudVisionTextClient(self._hass, self._auth)
        # TODO: Face recognition
        # self.persons = PersonsClient(self._hass, self._auth, self._oauth_provider)

        # These APIs aren't really useful in the context of home automation, are they?
        # self.docs = DocsClient(self._hass, self._auth, self._oauth_provider)
        # self.photo = PhotoClient(self._hass, self._auth, self._oauth_provider)
        # self.adult = AdultClient(self._hass, self._auth, self._oauth_provider)
