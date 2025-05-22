# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .api.vkcloud.auth import VKCloudAuth
from .const import (CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_REFRESH_TOKEN,
                    DOMAIN, LOGGER)


class VKCloudVisionConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for VK Cloud Vision."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                auth = VKCloudAuth(
                    self.hass,
                    client_id=user_input[CONF_CLIENT_ID],
                    client_secret=user_input[CONF_CLIENT_SECRET],
                )

                # Validate credentials by attempting to fetch a token
                await auth.get_access_token()
                refresh_token = auth.get_refresh_token()
                if not refresh_token:
                    raise Exception("No refresh token")

                return self.async_create_entry(
                    title="VK Cloud Vision",
                    data={
                        CONF_CLIENT_ID: user_input[CONF_CLIENT_ID],
                        CONF_REFRESH_TOKEN: refresh_token,
                    },
                )

            except Exception as e:
                errors["base"] = "invalid_auth"
                LOGGER.exception("Authentication error", exc_info=e)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CLIENT_ID): str,
                    vol.Required(CONF_CLIENT_SECRET): str,
                }
            ),
            errors=errors,
        )
