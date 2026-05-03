# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (ConfigEntry, ConfigFlow,
                                          ConfigFlowResult, OptionsFlow)
from homeassistant.helpers.selector import (NumberSelector,
                                            NumberSelectorConfig,
                                            NumberSelectorMode)

from .api.vkcloud.auth import VKCloudAuth
from .api.vkcloud.vision import VKCloudVision
from .const import (CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_CONFIRM_TRUNCATE,
                    CONF_REFRESH_TOKEN, CONF_TRAINING_MODE,
                    CONF_TRUNCATE_SPACE, DEFAULT_SPACE, DEFAULT_TRAINING_MODE,
                    DOMAIN, LOGGER)


class VKCloudVisionConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for VK Cloud Vision."""

    VERSION = 3

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the initial step (OAuth only for new users)."""
        errors: dict[str, str] = {}

        if user_input is not None:
            client_id = user_input[CONF_CLIENT_ID].strip()
            client_secret = user_input[CONF_CLIENT_SECRET].strip()
            try:
                # Validate OAuth credentials
                auth = VKCloudAuth(
                    self.hass,
                    client_id=client_id,
                    client_secret=client_secret,
                )
                await auth.get_access_token()
                refresh_token = auth.get_refresh_token()
                if not refresh_token:
                    raise Exception("No refresh token received from OAuth server")
                return self.async_create_entry(
                    title="VK Cloud Vision",
                    data={
                        CONF_CLIENT_ID: client_id,
                        CONF_REFRESH_TOKEN: refresh_token,
                    },
                )
            except Exception as e:  # noqa: BLE001
                errors["base"] = "invalid_auth"
                LOGGER.exception("Authentication error", exc_info=e)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_CLIENT_ID): str,
                vol.Required(CONF_CLIENT_SECRET): str,
            }),
            errors=errors,
            description_placeholders={
                "obtain_token_url": "https://msk.cloud.vk.com/app/services/machinelearning/vision/access/"
            }
        )

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle reconfiguration (force OAuth credentials)."""
        entry: ConfigEntry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]  # type: ignore[index]
        )

        errors: dict[str, str] = {}
        current_client_id = entry.data.get(CONF_CLIENT_ID, "")

        if user_input is not None:
            client_id = user_input.get(CONF_CLIENT_ID, current_client_id).strip()
            client_secret = user_input[CONF_CLIENT_SECRET].strip()
            try:
                auth = VKCloudAuth(
                    self.hass,
                    client_id=client_id,
                    client_secret=client_secret,
                )
                await auth.get_access_token()
                refresh_token = auth.get_refresh_token()
                if not refresh_token:
                    raise Exception("No refresh token received from OAuth server")
                # Update to OAuth format (removes any existing static token)
                self.hass.config_entries.async_update_entry(
                    entry,
                    data={
                        CONF_CLIENT_ID: client_id,
                        CONF_REFRESH_TOKEN: refresh_token,
                    },
                    version=self.VERSION,
                )
                self.hass.config_entries.async_schedule_reload(entry.entry_id)
                return self.async_abort(reason="reconfigure_successful")
            except Exception as e:  # noqa: BLE001
                errors["base"] = "invalid_auth"
                LOGGER.exception("Reconfiguration error", exc_info=e)

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema({
                vol.Required(CONF_CLIENT_ID, default=current_client_id): str,
                vol.Required(CONF_CLIENT_SECRET): str,
            }),
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

    async def async_step_init(self, _user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Show the main menu."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["face_recognition", "truncate_space"],
        )

    async def async_step_face_recognition(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Manage face recognition options (training mode)."""
        if user_input is not None:
            new_opts = dict(self.config_entry.options)
            new_opts[CONF_TRAINING_MODE] = user_input[CONF_TRAINING_MODE]
            return self.async_create_entry(data=new_opts)

        training_mode = self.config_entry.options.get(CONF_TRAINING_MODE, DEFAULT_TRAINING_MODE)

        schema = vol.Schema({
            vol.Required(CONF_TRAINING_MODE, default=training_mode): bool,
        })

        return self.async_show_form(
            step_id="face_recognition",
            data_schema=schema,
        )

    async def async_step_truncate_space(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Truncate a person space."""
        errors: dict[str, str] = {}

        if user_input is not None:
            space = user_input.get(CONF_TRUNCATE_SPACE, DEFAULT_SPACE)
            confirm = user_input.get(CONF_CONFIRM_TRUNCATE, False)

            if not confirm:
                errors["base"] = "confirm_truncate"
            else:
                client: VKCloudVision = self.config_entry.runtime_data
                try:
                    await client.persons.truncate(space)
                except Exception as err:
                    errors["base"] = "truncate_failed"
                    LOGGER.error("Truncate space %s failed: %s", space, err)
                else:
                    return self.async_abort(reason="truncate_success")

        data_schema = vol.Schema({
            vol.Required(CONF_TRUNCATE_SPACE, default=DEFAULT_SPACE): vol.All(
                NumberSelector(
                    NumberSelectorConfig(min=0, max=9, mode=NumberSelectorMode.BOX),
                ),
                vol.Coerce(int),
            ),
            vol.Required(CONF_CONFIRM_TRUNCATE, default=False): bool,
        })

        return self.async_show_form(
            step_id="truncate_space",
            data_schema=data_schema,
            errors=errors,
        )
