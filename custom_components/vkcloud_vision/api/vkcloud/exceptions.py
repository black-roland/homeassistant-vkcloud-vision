# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from typing import Any, Optional


class VKCloudVisionAPIError(Exception):
    """Base exception for VK Cloud Vision API errors."""

    def __init__(
        self,
        message: str,
        http_status: Optional[int] = None,
        api_status: Optional[int] = None,
        error_details: Optional[Any] = None,
    ) -> None:
        """Initialize the exception."""
        self.message = message
        self.http_status = http_status
        self.api_status = api_status
        self.error_details = error_details
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return a string representation of the error."""
        parts = [self.message]
        if self.http_status is not None:
            parts.append(f"HTTP Status: {self.http_status}")
        if self.api_status is not None:
            parts.append(f"API Status: {self.api_status}")
        if self.error_details:
            parts.append(f"details: {self.error_details}")
        return ", ".join(parts)


class VKCloudVisionAuthError(VKCloudVisionAPIError):
    """Exception for authentication-related errors."""
    pass


class VKCloudVisionBadRequestError(VKCloudVisionAPIError):
    """Exception for bad request errors (HTTP 400)."""
    pass


class VKCloudVisionForbiddenError(VKCloudVisionAPIError):
    """Exception for forbidden errors (HTTP 403)."""
    pass
