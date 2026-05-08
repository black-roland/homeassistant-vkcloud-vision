# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant import data_entry_flow
from homeassistant.components.file_upload import process_uploaded_file
from homeassistant.config_entries import (ConfigEntry, ConfigFlow,
                                          ConfigFlowResult, OptionsFlow)
from homeassistant.helpers.selector import (FileSelector, FileSelectorConfig,
                                            NumberSelector,
                                            NumberSelectorConfig,
                                            NumberSelectorMode, ObjectSelector,
                                            ObjectSelectorConfig, TextSelector)

from .api.vkcloud.auth import VKCloudAuth
from .api.vkcloud.vision import VKCloudVision
from .const import (CONF_ALIAS, CONF_CLIENT_ID, CONF_CLIENT_SECRET,
                    CONF_CONFIRM_DELETE, CONF_CONFIRM_TRUNCATE,
                    CONF_CREATE_NEW, CONF_DELETE_PERSON_SPACE,
                    CONF_PERSON_ALIASES, CONF_PERSON_IDS, CONF_PHOTO,
                    CONF_REFRESH_TOKEN, CONF_SPACE, CONF_TRUNCATE_SPACE,
                    CONF_UPDATE_EMBEDDING, DEFAULT_CREATE_NEW, DEFAULT_SPACE,
                    DEFAULT_UPDATE_EMBEDDING, DOMAIN, LOGGER,
                    SECTION_PERSON_ALIASES, SECTION_TRAINING_MODE)


class VKCloudVisionConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for VK Cloud Vision."""

    VERSION = 4

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
            menu_options=["face_recognition", "manual_training", "truncate_space", "delete_persons"],
        )

    async def async_step_face_recognition(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Manage face recognition options (training mode and aliases)."""
        if user_input is not None:
            new_opts = dict(self.config_entry.options)
            new_opts.update(user_input.get(SECTION_TRAINING_MODE, {}))
            new_opts.update(user_input.get(SECTION_PERSON_ALIASES, {}))
            return self.async_create_entry(data=new_opts)

        create_new_default = self.config_entry.options.get(CONF_CREATE_NEW, DEFAULT_CREATE_NEW)
        update_embedding_default = self.config_entry.options.get(CONF_UPDATE_EMBEDDING, DEFAULT_UPDATE_EMBEDDING)
        existing_aliases = self.config_entry.options.get(CONF_PERSON_ALIASES, [])

        training_schema = vol.Schema({
            vol.Required(CONF_CREATE_NEW, default=create_new_default): bool,
            vol.Required(CONF_UPDATE_EMBEDDING, default=update_embedding_default): bool,
        })

        alias_schema = vol.Schema({
            vol.Optional(CONF_PERSON_ALIASES, default=existing_aliases): ObjectSelector(
                ObjectSelectorConfig(
                    fields={
                        "alias": {
                            "required": True,
                            "selector": {"text": None},
                        },
                        "person_id": {
                            "required": True,
                            "selector": {"number": {"min": 1, "mode": "box"}},
                        },
                        "space": {
                            "required": True,
                            "selector": {"number": {"min": 0, "max": 9, "mode": "box"}},
                        },
                    },
                    multiple=True,
                    translation_key="person_aliases",
                )
            )
        })

        schema = self.add_suggested_values_to_schema(
            vol.Schema({
                vol.Required(SECTION_TRAINING_MODE): data_entry_flow.section(
                    training_schema,
                    {"collapsed": False},
                ),
                vol.Required(SECTION_PERSON_ALIASES): data_entry_flow.section(
                    alias_schema,
                    {"collapsed": False},
                ),
            }),
            self.config_entry.options,
        )

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

        space_default = user_input.get(CONF_TRUNCATE_SPACE, DEFAULT_SPACE) if user_input else DEFAULT_SPACE

        data_schema = vol.Schema({
            vol.Required(CONF_TRUNCATE_SPACE, default=space_default): vol.All(
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

    async def async_step_delete_persons(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Delete specific persons from a space."""
        errors: dict[str, str] = {}

        if user_input is not None:
            space = user_input.get(CONF_DELETE_PERSON_SPACE, DEFAULT_SPACE)
            person_ids_str = user_input.get(CONF_PERSON_IDS, "")
            confirm = user_input.get(CONF_CONFIRM_DELETE, False)

            if not confirm:
                errors["base"] = "confirm_delete"
            else:
                person_ids = []
                if person_ids_str:
                    try:
                        person_ids = [int(id.strip()) for id in person_ids_str.split(",") if id.strip()]
                    except ValueError:
                        errors["base"] = "invalid_person_ids"
                if not errors:
                    client: VKCloudVision = self.config_entry.runtime_data
                    try:
                        await client.persons.delete(space, person_ids)
                    except Exception as err:
                        errors["base"] = "delete_failed"
                        LOGGER.error("Delete persons from space %s failed: %s", space, err)
                    else:
                        return self.async_abort(reason="delete_success")

        space_default = user_input.get(CONF_DELETE_PERSON_SPACE, DEFAULT_SPACE) if user_input else DEFAULT_SPACE
        person_ids_default = user_input.get(CONF_PERSON_IDS, "") if user_input else ""

        data_schema = vol.Schema({
            vol.Required(CONF_DELETE_PERSON_SPACE, default=space_default): vol.All(
                NumberSelector(
                    NumberSelectorConfig(min=0, max=9, mode=NumberSelectorMode.BOX),
                ),
                vol.Coerce(int),
            ),
            vol.Required(CONF_PERSON_IDS, default=person_ids_default): TextSelector(),
            vol.Required(CONF_CONFIRM_DELETE, default=False): bool,
        })

        return self.async_show_form(
            step_id="delete_persons",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_manual_training(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle manual training with photo upload."""
        errors: dict[str, str] = {}
        if user_input is not None:
            return await self._process_manual_training(user_input, errors)

        return self.async_show_form(
            step_id="manual_training",
            data_schema=self._build_manual_training_schema(),
            errors=errors,
        )

    def _build_manual_training_schema(self) -> vol.Schema:
        """Build the manual training form schema."""
        return vol.Schema({
            vol.Required(CONF_SPACE, default=DEFAULT_SPACE): vol.All(
                NumberSelector(NumberSelectorConfig(min=0, max=9, mode=NumberSelectorMode.BOX)),
                vol.Coerce(int),
            ),
            vol.Required(CONF_PHOTO): FileSelector(FileSelectorConfig(accept=".jpg,.jpeg,.png,.tiff")),
            vol.Optional(CONF_ALIAS): TextSelector(),
        })

    def _read_uploaded_photo(self, file_id: str) -> bytes:
        """Read uploaded photo bytes from file ID."""
        with process_uploaded_file(self.hass, file_id) as path:
            return path.read_bytes()

    async def _process_manual_training(self, user_input: dict[str, Any], errors: dict[str, str]) -> ConfigFlowResult:
        """Process manual training form submission."""

        try:
            file_id = user_input[CONF_PHOTO]
            space = user_input[CONF_SPACE]
            alias = user_input.get(CONF_ALIAS, "").strip()
            photo_bytes = await self.hass.async_add_executor_job(self._read_uploaded_photo, file_id)

            client: VKCloudVision = self.config_entry.runtime_data
            response = await client.persons.recognize(
                files=[photo_bytes],
                space=space,
                images=[{"name": "training_photo"}],
                create_new=True,
                update_embedding=True,
                max_retries=1,
            )

            if response.has_errors:
                raise Exception(response.error_message)

            person_tags = [p["tag"] for p in response.persons if p.get("tag", "undefined") != "undefined"]
            if not person_tags:
                errors["base"] = "no_faces"
                return self.async_show_form(
                    step_id="manual_training",
                    data_schema=self._build_manual_training_schema(),
                    errors=errors,
                )

            person_ids = [int(t.replace("person", "")) for t in person_tags]
            aliases = self._update_aliases(person_ids, space, alias)

            new_opts = dict(self.config_entry.options)
            new_opts[CONF_PERSON_ALIASES] = aliases
            self.hass.config_entries.async_update_entry(self.config_entry, options=new_opts)

            tags_str = ", ".join(person_tags)
            return self.async_abort(
                reason="manual_training_success",
                description_placeholders={"tags": tags_str},
            )

        except Exception as err:
            LOGGER.exception("Manual training failed", exc_info=err)
            errors["base"] = "training_failed"
            return self.async_show_form(
                step_id="manual_training",
                data_schema=self._build_manual_training_schema(),
                errors=errors,
            )

    def _update_aliases(self, person_ids: list[int], space: int, alias: str) -> list[dict[str, Any]]:
        aliases: list[dict[str, Any]] = list(self.config_entry.options.get(CONF_PERSON_ALIASES, []))
        first_pid = person_ids[0]

        if alias:
            found = False
            for entry in aliases:
                if entry.get("person_id") == first_pid and entry.get("space") == space:
                    entry["alias"] = alias
                    found = True
                    break

            if not found:
                aliases.append({"person_id": first_pid, "space": space, "alias": alias})

        for pid in person_ids:
            if not any(a["person_id"] == pid and a["space"] == space for a in aliases):
                aliases.append({"person_id": pid, "space": space, "alias": f"person{pid}"})

        return aliases
