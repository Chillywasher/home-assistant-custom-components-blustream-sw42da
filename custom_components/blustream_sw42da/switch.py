"""Platform for sensor integration."""
import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Any

from homeassistant.components.switch import (
    SwitchEntity, SwitchEntityDescription,
)
from homeassistant.core import HomeAssistant

from . import Sw42daCoordinator
from .entity import Sw42daEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class Sw42daSwitchDescription(SwitchEntityDescription):
    state: Callable[[defaultdict], Any] | None = None
    turn_on_command: str | None = None
    turn_off_command: str | None = None


SWITCHES: tuple[Sw42daSwitchDescription, ...] = (
    Sw42daSwitchDescription(
        key="main_volume_mute",
        name="Main Volume Mute",
        state=lambda data: data["AudioOut"][0]["Mute"]=="On",
        turn_on_command="MUTE ON",
        turn_off_command="MUTE OFF",
    ),
    Sw42daSwitchDescription(
        key="multichannel_line_volume_mute",
        name="Multichannel Line Volume Mute",
        state=lambda data: data["AudioOut"][1]["Mute"]=="On",
        turn_on_command="OUT 21 MUTE ON",
        turn_off_command="OUT 21 MUTE OFF",
    ),
    Sw42daSwitchDescription(
        key="downmix_line_volume_mute",
        name="Downmix Line Volume Mute",
        state=lambda data: data["AudioOut"][2]["Mute"]=="On",
        turn_on_command="OUT 22 MUTE ON",
        turn_off_command="OUT 22 MUTE OFF",
    ),
    Sw42daSwitchDescription(
        key="multichannel_dante_volume_mute",
        name="Multichannel Dante Volume Mute",
        state=lambda data: data["AudioOut"][3]["Mute"]=="On",
        turn_on_command="OUT 23 MUTE ON",
        turn_off_command="OUT 23 MUTE OFF",
    ),
    Sw42daSwitchDescription(
        key="downmix_dante_volume_mute",
        name="Downmix Dante Volume Mute",
        state=lambda data: data["AudioOut"][4]["Mute"]=="On",
        turn_on_command="OUT 24 MUTE ON",
        turn_off_command="OUT 24 MUTE OFF",
    ),
    Sw42daSwitchDescription(
        key="key_control",
        name="Key Control",
        state=lambda data: data["Key"] == "On",
        turn_on_command="KEY ON",
        turn_off_command="KEY OFF",
    ),
    Sw42daSwitchDescription(
        key="beep_control",
        name="Onboard Beep",
        state=lambda data: data["Beep"] == "On",
        turn_on_command="BEEP ON",
        turn_off_command="BEEP OFF",
    ),
    Sw42daSwitchDescription(
        key="lcd_always_on",
        name="LCD Always On",
        state=lambda data: data["LCD"] == "On",
        turn_on_command="LCD ON",
        turn_off_command="LCD OFF",
    ),
    Sw42daSwitchDescription(
        key="cec_volume_control",
        name="CEC Volume Control",
        state=lambda data: data["CEC_Control"] == "On",
        turn_on_command="CEC ON",
        turn_off_command="CEC OFF",
    ),
    Sw42daSwitchDescription(
        key="power",
        name="Power",
        state=lambda data: data["Power"] == "On",
        turn_on_command="PON",
        turn_off_command="POFF",
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities) -> None:
    """Set up the Sw42da switch entities."""
    coordinator: Sw42daCoordinator = hass.data[DOMAIN][entry.entry_id]
    if coordinator.data is not None:
        async_add_entities(
            Sw42daSwitch(
                coordinator=coordinator,
                entity_description=entity_description,
            )
            for entity_description in SWITCHES
        )


class Sw42daSwitch(Sw42daEntity, SwitchEntity):
    entity_description: Sw42daSwitchDescription
    _attr_has_entity_name = True

    def __init__(
            self,
            *,
            coordinator: Sw42daCoordinator,
            entity_description: Sw42daSwitchDescription
    ) -> None:
        super().__init__(coordinator=coordinator)
        self.entity_description = entity_description
        self.entity_id = f"switch.{DOMAIN}_{entity_description.key}"
        self._attr_unique_id = f"{DOMAIN}_switch_{entity_description.key}"
        self._attr_name = entity_description.name

    @property
    def is_on(self) -> bool | None:
        if self.entity_description.state is None:
            return None
        return self.entity_description.state(self.coordinator.data)

    async def async_turn_on(self, **kwargs: object) -> None:
        """Turn the switch on."""
        try:
            _LOGGER.debug("Turning ON %s", self._attr_name)
            await self.hass.async_add_executor_job(
                self.send_command, self.entity_description.turn_on_command
            )
            await self.coordinator.async_refresh()
        except Exception as err:
            _LOGGER.error("Failed to turn on %s: %s", self._attr_name, err)
            raise

    async def async_turn_off(self, **kwargs: object) -> None:
        """Turn the switch off."""
        try:
            _LOGGER.debug("Turning OFF %s", self._attr_name)
            await self.hass.async_add_executor_job(
                self.send_command, self.entity_description.turn_off_command
            )
            await self.coordinator.async_refresh()
        except Exception as err:
            _LOGGER.error("Failed to turn off %s: %s", self._attr_name, err)
            raise