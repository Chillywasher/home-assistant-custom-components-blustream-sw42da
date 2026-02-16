"""The Blustream SW42DA integration."""

from __future__ import annotations

import logging

from homeassistant.helpers.typing import ConfigType
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN, CONF_BAUD_RATE, CONF_INPUT1_NAME
from .coordinator import Sw42daCoordinator
from .sw42da_api import Sw42daApi

_LOGGER = logging.getLogger(__name__)

_PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.SWITCH,
    Platform.BUTTON,
    Platform.SELECT,
]



async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Blustream SW42DA from a config entry."""
    controller = Sw42daApi(
        host_ip=entry.data.get(CONF_HOST),
        host_port=entry.data.get(CONF_PORT),
        baud_rate=entry.data.get(CONF_BAUD_RATE)
    )
    # TODO: try connecting and returning firmware version starts with V

    sw42da_coordinator = Sw42daCoordinator(
        hass=hass,
        controller=controller,
        entry=entry,
    )

    await sw42da_coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = sw42da_coordinator
    hass.data[DOMAIN]["controller"] = controller

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    return True


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:

    async def reboot_device(call: ServiceCall) -> None:
        controller: Sw42daApi = hass.data[DOMAIN]["controller"]
        _LOGGER.info("Calling service")
        await hass.async_add_executor_job(controller.send_command, "REBOOT")

    # Register our service with Home Assistant.
    hass.services.async_register(
        domain=DOMAIN,
        service='reboot_device',
        service_func=reboot_device,
    )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, _PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


