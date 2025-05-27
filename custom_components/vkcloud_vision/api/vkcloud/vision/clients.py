# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from typing import Any, Dict, List, Optional

from .base_client import VKCloudVisionBaseClient
from .response import VKCloudVisionResponse


class VKCloudVisionObjectsClient(VKCloudVisionBaseClient):
    """Client for objects-related VK Cloud Vision API endpoints."""

    async def detect(
        self,
        files: List[bytes],
        modes: List[str],
        images: List[Dict[str, str]],
    ) -> VKCloudVisionResponse:
        """Detect objects in a photo."""
        meta = {
            "mode": modes,  # e.g., ["object", "object2", "scene"]
            "images": images,  # Expected format: [{"name": str}]
        }
        return VKCloudVisionResponse(await self._make_request("/v1/objects/detect", files, meta))


class VKCloudVisionTextClient(VKCloudVisionBaseClient):
    """Client for text-related VK Cloud Vision API endpoints."""

    async def recognize(
        self,
        files: List[bytes],
        images: List[Dict[str, str]],
        mode: Optional[str] = None,
    ) -> VKCloudVisionResponse:
        """Recognize text in a document."""
        meta: Dict[str, Any] = {"images": images}  # Expected format: [{"name": str}]
        if mode:
            meta["mode"] = mode  # e.g., "detailed"
        return VKCloudVisionResponse(await self._make_request("/v1/text/recognize", files, meta))

    async def scene_text_recognize(
        self,
        files: List[bytes],
        images: List[Dict[str, str]],
        lang: Optional[str] = None,
    ) -> VKCloudVisionResponse:
        """Recognize text in scene photos."""
        meta: Dict[str, Any] = {"images": images}  # Expected format: [{"name": str}]
        if lang:
            meta["lang"] = lang  # e.g., "rus", "eng"
        return VKCloudVisionResponse(await self._make_request("/v1/scene_text/recognize", files, meta))
