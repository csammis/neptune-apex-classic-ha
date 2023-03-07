"""Configuration UI definition."""

import logging
from typing import Any

from neptune_apex_classic.connection import ApexConnection
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONFIG_KEY_SERIAL_NUMBER,
    DEFAULT_NAME,
    DEFAULT_PASSWORD,
    DEFAULT_USERNAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class ApexConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Define the config flow for the Apex."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Present the user configuration."""
        errors = {}
        if user_input is not None:
            session = async_get_clientsession(self.hass, False)
            conn = ApexConnection(
                user_input[CONF_HOST],
                session,
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
            )
            serial_number = await conn.get_serial_number()
            if serial_number is None:
                errors["base"] = "status-not-found"
            else:
                _LOGGER.info("Setting up Apex with serial number %s", serial_number)
                await self.async_set_unique_id(serial_number)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data={
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_NAME: user_input[CONF_NAME],
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONFIG_KEY_SERIAL_NUMBER: serial_number,
                    },
                )

        user_input = user_input or {}
        data_schema = {
            vol.Required(CONF_HOST, default=user_input.get(CONF_HOST)): str,
            vol.Required(
                CONF_NAME, default=user_input.get(CONF_NAME, DEFAULT_NAME)
            ): str,
            vol.Optional(
                CONF_USERNAME, default=user_input.get(CONF_USERNAME, DEFAULT_USERNAME)
            ): str,
            vol.Optional(
                CONF_PASSWORD, default=user_input.get(CONF_PASSWORD, DEFAULT_PASSWORD)
            ): str,
        }

        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(data_schema), errors=errors
        )
