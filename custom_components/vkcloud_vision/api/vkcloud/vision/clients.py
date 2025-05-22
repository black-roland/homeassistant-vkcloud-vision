# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from typing import Any, Dict, List

from .base_client import VKCloudVisionBaseClient


class VKCloudVisionObjectsClient(VKCloudVisionBaseClient):
    """Client for objects-related VK Cloud Vision API endpoints."""

    async def detect(
        self,
        modes: List[str],
        images_meta: List[Dict[str, str]],
        images: List[bytes],
    ) -> Dict[str, Any]:
        """Detect objects in a photo."""
        meta = {
            "mode": modes,  # e.g., ["object", "object2", "scene"]
            "images": images_meta,  # Expected format: [{"name": str}]
        }
        return await self._make_request("/v1/objects/detect", images, meta)
