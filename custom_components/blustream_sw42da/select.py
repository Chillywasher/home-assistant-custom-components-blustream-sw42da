"""Platform for sensor integration."""
import logging

from homeassistant.components.fish_audio.error import UnexpectedError
from homeassistant.components.select import (
    SelectEntity, SelectEntityDescription,
)
from homeassistant.core import HomeAssistant, callback

from . import Sw42daCoordinator, CONF_INPUT1_NAME
from .entity import Sw42daEntity
from .const import DOMAIN, CONF_INPUT2_NAME, CONF_INPUT3_NAME, CONF_INPUT4_NAME
from .model import source_select_command

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities) -> None:
    """Set up the Sw42da select entities."""
    coordinator: Sw42daCoordinator = hass.data[DOMAIN][entry.entry_id]
    if coordinator.data is not None:

        options: list =[
            entry.data.get(CONF_INPUT1_NAME),
            entry.data.get(CONF_INPUT2_NAME),
            entry.data.get(CONF_INPUT3_NAME),
            entry.data.get(CONF_INPUT4_NAME),
        ]
        entity_description: SelectEntityDescription = SelectEntityDescription(
            key="source_input",
            name="Source Input"
        )
        async_add_entities([
            Sw42daSelect(
                coordinator=coordinator,
                entity_description=entity_description,
                options=options
            ),
            ]
        )


class Sw42daSelect(Sw42daEntity, SelectEntity):
    """ Representation of an Sw42da select entity. """

    entity_description: SelectEntityDescription
    _attr_has_entity_name = True

    def __init__(
            self,
            coordinator: Sw42daCoordinator,
            options: list,
            entity_description: SelectEntityDescription,

    ) -> None:
        super().__init__(coordinator=coordinator)

        self.entity_description = entity_description
        self.entity_id = f"select.{DOMAIN}_{entity_description.key}"

        self._attr_unique_id = f"{DOMAIN}_select_{entity_description.key}"
        self._attr_name = "Source Input"
        self._attr_options = options
        self._attr_current_option: str | None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update attributes when the coordinator updates."""
        self._async_update_attrs()
        # selected = int(self.coordinator.data["Output"][0]["FromIn"])
        # _LOGGER.info(f"Source number {selected} is selected")
        # _LOGGER.info(f"Option selected should be {self._attr_options[selected-1]}")
        # self._attr_current_option = self._attr_options[selected-1]
        super()._handle_coordinator_update()

    def _get_current_option(self) -> str | None:
        """Get current selected option."""
        selected = int(self.coordinator.data["Output"][0]["FromIn"])
        return self._attr_options[selected - 1]

    @callback
    def _async_update_attrs(self) -> None:
        """Update select attributes."""
        self._attr_current_option = self._get_current_option()

    @property
    def current_option(self) -> str | None:
        """Return the current option."""
        return self._get_current_option()

    async def async_select_option(self, option: str) -> None:
        """Update the current value."""
        command = ""
        try:
            _LOGGER.info("Selecting option for %s", self._attr_name)
            for i in range(len(self._attr_options)):
                if option == self._attr_options[i]:
                    command = list(source_select_command.values())[i]
        except Exception as err:
            _LOGGER.error(
                "Failed to set option for %s to %s: %s",
                self._attr_name,
                option,
                err,
            )
            raise
        if command:
            await self.hass.async_add_executor_job(
                self.send_command, command
            )
        self._attr_current_option = option
        await self.coordinator.async_refresh()
