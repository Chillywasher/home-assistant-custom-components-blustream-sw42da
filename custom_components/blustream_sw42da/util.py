import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceEntry, DeviceRegistry

from . import Sw42daCoordinator
from .error import ServiceError
from .const import DATA, DOMAIN


_LOGGER = logging.getLogger(__name__)

async def get_coordinator_by_device_id(
        hass: HomeAssistant, device_id: str
) -> "Sw42daCoordinator":
    """Get the ConfigEntry."""
    registry: DeviceRegistry = dr.async_get(hass)
    dev_entry: DeviceEntry = registry.async_get(device_id)

    config_entry = hass.config_entries.async_get_entry(
        list(dev_entry.config_entries)[0]
    )
    return await get_coordinator(hass, config_entry)

async def get_coordinator(
        hass: HomeAssistant, config_entry: ConfigEntry
) -> "Sw42daCoordinator":
    """Get the Sw42daCoordinator."""
    if config_entry.domain != DOMAIN:
        raise ServiceError("Integration domain mismatch")

    if config_entry.entry_id not in hass.data.get(DOMAIN, {}):
        raise ServiceError("Integration not loaded for this config entry")

    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    data = entry_data.get(DATA)

    if data is None or data.coordinator is None:
        raise ServiceError("Coordinator not available")

    return data.coordinator