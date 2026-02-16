"""Platform for sensor integration."""
import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Any

from homeassistant.components.binary_sensor import (
    BinarySensorEntity, BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant

from . import Sw42daCoordinator
from .entity import Sw42daEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class Sw42daBinarySensorDescription(BinarySensorEntityDescription):
    state: Callable[[defaultdict], Any] | None = None
    icon_on: str | None = None
    icon_off: str | None = None


BINARY_SENSORS: tuple[Sw42daBinarySensorDescription, ...] = (
    Sw42daBinarySensorDescription(
        key="main_volume_mute",
        name="Main Volume Mute",
        state=lambda data: data["AudioOut"][0]["Mute"]=="On",
        icon_on="mdi:volume-mute",
        icon_off="mdi:volume-low",
    ),
    Sw42daBinarySensorDescription(
        key="multichannel_line_volume_mute",
        name="Multichannel Line Volume Mute",
        state=lambda data: data["AudioOut"][1]["Mute"]=="On",
        icon_on="mdi:volume-mute",
        icon_off="mdi:volume-low",
    ),
    Sw42daBinarySensorDescription(
        key="downmix_line_volume_mute",
        name="Downmix Line Volume Mute",
        state=lambda data: data["AudioOut"][2]["Mute"]=="On",
        icon_on="mdi:volume-mute",
        icon_off="mdi:volume-low",
    ),
    Sw42daBinarySensorDescription(
        key="multichannel_dante_volume_mute",
        name="Multichannel Dante Volume Mute",
        state=lambda data: data["AudioOut"][3]["Mute"]=="On",
        icon_on="mdi:volume-mute",
        icon_off="mdi:volume-low",
    ),
    Sw42daBinarySensorDescription(
        key="downmix_dante_volume_mute",
        name="Downmix Dante Volume Mute",
        state=lambda data: data["AudioOut"][4]["Mute"]=="On",
        icon_on="mdi:volume-mute",
        icon_off="mdi:volume-low",
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities) -> None:
    """Set up the Sw42da binary sensor."""
    coordinator: Sw42daCoordinator = hass.data[DOMAIN][entry.entry_id]
    if coordinator.data is not None:
        async_add_entities(
            Sw42daBinarySensor(
                coordinator=coordinator,
                entity_description=entity_description,
            )
            for entity_description in BINARY_SENSORS
        )


class Sw42daBinarySensor(Sw42daEntity, BinarySensorEntity):
    entity_description: Sw42daBinarySensorDescription
    _attr_has_entity_name = True

    def __init__(
            self,
            *,
            coordinator: Sw42daCoordinator,
            entity_description: Sw42daBinarySensorDescription
    ) -> None:
        super().__init__(coordinator=coordinator)
        self.entity_description = entity_description
        self.entity_id = f"binary_sensor.{DOMAIN}_{entity_description.key}"
        self._attr_unique_id = f"{DOMAIN}_binary_sensor_{entity_description.key}"
        self._attr_name = entity_description.name

    @property
    def icon(self) -> str | None:
        if self.is_on:
            if self.entity_description.icon_on:
                return self.entity_description.icon_on
        else:
            if self.entity_description.icon_off:
                return self.entity_description.icon_off
        return None

    @property
    def is_on(self) -> bool | None:
        if self.entity_description.state is None:
            return None
        return self.entity_description.state(self.coordinator.data)
