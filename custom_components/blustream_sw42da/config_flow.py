"""Config flow for the Blustream SW42DA integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
import homeassistant.helpers.config_validation as cv

from homeassistant.helpers.device_registry import format_mac

from . import Sw42daApi
from .const import DOMAIN, CONF_BAUD_RATE, CONF_INPUT1_NAME, CONF_INPUT2_NAME, CONF_INPUT3_NAME, CONF_INPUT4_NAME


_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default="192.168.67.31"): cv.string,
        vol.Required(CONF_PORT, default=8000): cv.positive_int,
        vol.Required(CONF_BAUD_RATE, default=57600): cv.positive_int,
        vol.Optional(CONF_INPUT1_NAME, default="INPUT1"): cv.string,
        vol.Optional(CONF_INPUT2_NAME, default="INPUT2"): cv.string,
        vol.Optional(CONF_INPUT3_NAME, default="INPUT3"): cv.string,
        vol.Optional(CONF_INPUT4_NAME, default="INPUT4"): cv.string,
    }
)

async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # TODO validate the data can be used to set up a connection.

    # If your PyPI package is not built with async, pass your methods
    # to the executor:
    api = Sw42daApi(data[CONF_HOST], data[CONF_PORT], data[CONF_BAUD_RATE])

    raw = await hass.async_add_executor_job(
        api.send_command, "STATUS"
    )
    result = api.parse_result(raw)

    # hub = PlaceholderHub(data[CONF_HOST], data[CONF_PORT], data[CONF_BAUD_RATE])
    # if not await hub.authenticate(data[CONF_HOST], data[CONF_PORT], data[CONF_BAUD_RATE]):
    #     raise InvalidAuth

    # If you cannot connect:
    # throw CannotConnect
    # If the authentication is wrong:
    # InvalidAuth

    if not result:
        raise CannotConnect

    # Return info that you want to store in the config entry.
    return {
        "title": result["Local"],
        "unique_id": result["Mac"],
        "ip": result["Network"]["IP"],
        "port": int(result["TCP/IP Port"]),
        "baud_rate": int(result["Baud"])
    }


class Sw42DaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Blustream SW42DA."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                _LOGGER.info(info)

                unique_id = format_mac(info["unique_id"])
                _LOGGER.info("SW42DA device found: %s", unique_id)

                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured(updates={
                    CONF_HOST: info["ip"],
                    CONF_PORT: info["port"],
                    CONF_BAUD_RATE: info["baud_rate"]
                })

            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    # async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None):
    #     if user_input is not None:
    #         # TODO: process user input
    #
    #         info = await validate_input(self.hass, user_input)
    #         _LOGGER.info(info)
    #
    #         self.async_set_unique_id(user_id)
    #         self._abort_if_unique_id_mismatch()
    #
    #         return self.async_update_reload_and_abort(
    #             self._get_reconfigure_entry(),
    #             data_updates=data,
    #         )
    #
    #     return self.async_show_form(
    #         step_id="reconfigure",
    #         data_schema=vol.Schema({vol.Required("input_parameter"): str}),
    #     )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
    pass

class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
    pass