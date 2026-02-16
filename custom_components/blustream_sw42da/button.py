"""Platform for sensor integration."""
import asyncio
import logging

from dataclasses import dataclass


from homeassistant.components.button import (
    ButtonEntity, ButtonEntityDescription,
)
from homeassistant.core import HomeAssistant

from . import Sw42daCoordinator, CONF_INPUT1_NAME
from .entity import Sw42daEntity
from .const import DOMAIN, CONF_INPUT2_NAME, CONF_INPUT3_NAME, CONF_INPUT4_NAME, INPUT1, INPUT2, INPUT3, INPUT4
from .model import source_select_command

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class Sw42daButtonDescription(ButtonEntityDescription):
    press_command: str | None = None

BUTTONS: tuple[Sw42daButtonDescription, ...] = (
    Sw42daButtonDescription(
        key=INPUT1,
        name=INPUT1.upper(),
        press_command=source_select_command.get(INPUT1),
    ),
    Sw42daButtonDescription(
        key=INPUT2,
        name=INPUT2.upper(),
        press_command=source_select_command.get(INPUT2),
    ),
    Sw42daButtonDescription(
        key=INPUT3,
        name=INPUT3.upper(),
        press_command=source_select_command.get(INPUT3),
    ),
    Sw42daButtonDescription(
        key=INPUT4,
        name=INPUT4.upper(),
        press_command=source_select_command.get(INPUT4),
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities) -> None:
    """Set up the Sw42da button entity."""
    coordinator: Sw42daCoordinator = hass.data[DOMAIN][entry.entry_id]
    if coordinator.data is not None:
        source_inputs: tuple = (
            entry.data.get(CONF_INPUT1_NAME),
            entry.data.get(CONF_INPUT2_NAME),
            entry.data.get(CONF_INPUT3_NAME),
            entry.data.get(CONF_INPUT4_NAME),
        )
        async_add_entities(
            Sw42daButton(
                coordinator=coordinator,
                entity_description=entity_description,
                source_inputs=source_inputs
            )
            for entity_description in BUTTONS
        )


class Sw42daButton(Sw42daEntity, ButtonEntity):
    """ Representation of an Sw42da button """

    entity_description: Sw42daButtonDescription
    _attr_has_entity_name = True

    def __init__(
            self,
            coordinator: Sw42daCoordinator,
            source_inputs: tuple,
            entity_description: Sw42daButtonDescription,

    ) -> None:
        super().__init__(coordinator=coordinator)
        self.source_inputs = source_inputs
        self.entity_description = entity_description
        self.entity_id = f"button.{DOMAIN}_{entity_description.key}"
        self._attr_unique_id = f"{DOMAIN}_button_{entity_description.key}"
        self._attr_name = self._get_name()

    def _get_name(self):
        name =  self.entity_description.name
        if name.startswith("INPUT"):
            n = name.replace("INPUT","")
            return self.source_inputs[int(n)-1]
        return self.entity_description.name

    async def async_press(self, **kwargs: object) -> None:
        """Press button."""
        try:
            _LOGGER.debug("Pressing button %s", self._attr_name)
            await self.hass.async_add_executor_job(
                self.send_command, self.entity_description.press_command
            )
            await asyncio.sleep(1)
            await self.coordinator.async_refresh()
        except Exception as err:
            _LOGGER.error("Failed to press %s: %s", self._attr_name, err)
            raise
