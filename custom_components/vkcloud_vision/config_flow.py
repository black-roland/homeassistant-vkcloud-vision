# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant import data_entry_flow
from homeassistant.config_entries import (ConfigEntry, ConfigFlow,
                                          ConfigFlowResult, OptionsFlow)

from .api.vkcloud.auth import VKCloudApiKeyAuth
from .const import (CONF_API_KEY, CONF_FACE_RECOGNITION_SECTION,
                    CONF_TRAINING_MODE, DEFAULT_TRAINING_MODE, DOMAIN, LOGGER)


class VKCloudVisionConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for VK Cloud Vision."""

    VERSION = 2

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle initial setup (static API key only)."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = user_input[CONF_API_KEY].strip()
            try:
                # Minimal validation
                auth = VKCloudApiKeyAuth(self.hass, api_key)
                await auth.get_access_token()  # just ensures it's non-empty
                return self.async_create_entry(
                    title="VK Cloud Vision",
                    data={CONF_API_KEY: api_key},
                )
            except Exception as e:  # noqa: BLE001
                errors["base"] = "invalid_auth"
                LOGGER.exception("Authentication error", exc_info=e)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_API_KEY): str}),
            errors=errors,
            description_placeholders={
                "obtain_token_url": "https://msk.cloud.vk.com/app/services/machinelearning/vision/access/"
            }
        )

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle reconfiguration (change API key)."""
        entry: ConfigEntry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]  # type: ignore[index]
        )

        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = user_input[CONF_API_KEY].strip()
            try:
                auth = VKCloudApiKeyAuth(self.hass, api_key)
                await auth.get_access_token()
                # Update entry to new static-key format (removes old OAuth data)
                self.hass.config_entries.async_update_entry(
                    entry,
                    data={CONF_API_KEY: api_key},
                    version=self.VERSION,
                )
                self.hass.config_entries.async_schedule_reload(entry.entry_id)
                return self.async_abort(reason="reconfigure_successful")
            except Exception as e:  # noqa: BLE001
                errors["base"] = "invalid_auth"
                LOGGER.exception("Reconfiguration error", exc_info=e)

        # Pre-fill with current key if it exists
        current_key = entry.data.get(CONF_API_KEY, "")
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {vol.Required(CONF_API_KEY, default=current_key): str}
            ),
            errors=errors,
            description_placeholders={
                "obtain_token_url": "https://msk.cloud.vk.com/app/services/machinelearning/vision/access/"
            }
        )

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        """Perform reauth upon ConfigEntryAuthFailed."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Dialog that informs the user that re-authentication is required."""
        # After user confirms → show the exact same API key form as reconfigure
        # (context["entry_id"] is already set by HA for reauth flows)
        return await self.async_step_reconfigure()

    @staticmethod
    def async_get_options_flow(_entry: ConfigEntry) -> OptionsFlow:
        """Create the options flow."""
        return VKCloudVisionOptionsFlow()


class VKCloudVisionOptionsFlow(OptionsFlow):
    """VK Cloud Vision options flow."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        schema = self.vkcloud_vision_config_option_schema()
        return self.async_show_form(
            step_id="init",
            data_schema=schema,
        )

    def vkcloud_vision_config_option_schema(self) -> vol.Schema:
        """VK Cloud Vision options schema."""

        face_recognition_schema = vol.Schema(
            {
                vol.Optional(CONF_TRAINING_MODE, default=DEFAULT_TRAINING_MODE): bool,
            }
        )

        return self.add_suggested_values_to_schema(
            vol.Schema(
                {
                    vol.Required(CONF_FACE_RECOGNITION_SECTION): data_entry_flow.section(
                        face_recognition_schema,
                        {"collapsed": False},
                    ),
                }
            ),
            self.config_entry.options,
        )
