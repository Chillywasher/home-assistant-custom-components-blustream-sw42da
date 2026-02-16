"""Platform for sensor integration."""
import logging

from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Any
import voluptuous as vol

import homeassistant.helpers.config_validation as cv

from homeassistant.components.sensor import (
    SensorDeviceClass, SensorStateClass, SensorEntityDescription, SensorEntity
)

from homeassistant.const import CONF_HOST, CONF_PORT, UnitOfTemperature, PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import StateType
from . import CONF_BAUD_RATE
from .entity import Sw42daEntity

from .const import DOMAIN
from .coordinator import Sw42daCoordinator

_LOGGER = logging.getLogger(__name__)

# PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
#     {
#         vol.Required(CONF_HOST): cv.string,
#         vol.Required(CONF_PORT): cv.positive_int,
#         vol.Required(CONF_BAUD_RATE): cv.positive_int,
#     }
# )

@dataclass(frozen=True)
class Sw42daSensorDescription(SensorEntityDescription):
    state: Callable[[defaultdict], Any] | None = None
    format: Callable[[Any], Any] | None = None


SENSORS: tuple[Sw42daSensorDescription, ...] = (
    Sw42daSensorDescription(
        key="temperature",
        name="Temperature",
        icon="mdi:thermometer",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state=lambda data: data["Temp(C)"],
        format=lambda value: value.replace("C", ""),
    ),
    Sw42daSensorDescription(
        key="mac_address",
        name="MAC Address",
        state=lambda data: data["Mac"],
        icon="mdi:network-outline"
    ),
    Sw42daSensorDescription(
        key="source_input",
        name="Source Input",
        state=lambda data: data["Output"][0]["FromIn"],
        icon="mdi:hdmi-port"
    ),
    Sw42daSensorDescription(
        key="local_name",
        name="Local Name",
        state=lambda data: data["Local"],
        icon="mdi:audio-video"
    ),
    Sw42daSensorDescription(
        key="main_volume",
        name="Main Volume",
        state=lambda data: data["AudioOut"][0]["Volume"],
        native_unit_of_measurement=PERCENTAGE,
        icon="volume"
    ),
    Sw42daSensorDescription(
        key="multichannel_line_volume",
        name="Multichannel Line Volume",
        state=lambda data: data["AudioOut"][1]["Volume"],
        native_unit_of_measurement=PERCENTAGE,
        icon="volume"
    ),
    Sw42daSensorDescription(
        key="downmix_line_volume",
        name="Downmix Line Volume",
        state=lambda data: data["AudioOut"][2]["Volume"],
        native_unit_of_measurement=PERCENTAGE,
        icon="volume"
    ),
    Sw42daSensorDescription(
        key="multichannel_dante_volume",
        name="Multichannel Dante Volume",
        state=lambda data: data["AudioOut"][3]["Volume"],
        native_unit_of_measurement=PERCENTAGE,
        icon="volume"
    ),
    Sw42daSensorDescription(
        key="downmix_dante_volume",
        name="Downmix Dante Volume",
        state=lambda data: data["AudioOut"][4]["Volume"],
        native_unit_of_measurement=PERCENTAGE,
        icon="volume"
    ),
)

async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities) -> None:
    """Set up the Sw42da sensor entities."""
    coordinator: Sw42daCoordinator = hass.data[DOMAIN][entry.entry_id]
    if coordinator.data is not None:
        async_add_entities(
            Sw42daSensor(
                coordinator=coordinator,
                entity_description=entity_description,
            )
            for entity_description in SENSORS
        )


class Sw42daSensor(Sw42daEntity, SensorEntity):
    entity_description: Sw42daSensorDescription
    _attr_has_entity_name = True

    def __init__(
            self,
            *,
            coordinator: Sw42daCoordinator,
            entity_description: Sw42daSensorDescription
    ) -> None:
        super().__init__(coordinator=coordinator)

        self.entity_description = entity_description
        self.entity_id = f"sensor.{DOMAIN}_{entity_description.key}"
        self._attr_unique_id = f"{DOMAIN}_sensor_{entity_description.key}"
        self._attr_name = entity_description.name

    @property
    def icon(self) -> str | None:
        if self.entity_description.icon:

            if self.entity_description.icon=="volume":
                if self.native_value >= 66:
                    return "mdi:volume-high"
                elif self.native_value >= 33:
                    return "mdi:volume-medium"
                else:
                    return "mdi:volume-low"

            return self.entity_description.icon

        return None

    @property
    def native_value(self) -> StateType:
        if self.entity_description.state is None:
            return None
        value = self.entity_description.state(self.coordinator.data)
        if self.entity_description.format is not None:
            value = self.entity_description.format(value)
        return value



