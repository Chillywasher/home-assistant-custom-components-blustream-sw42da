"""Platform for sensor integration."""
import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Any

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant

from . import Sw42daCoordinator
from .entity import Sw42daEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class Sw42daNumberDescription(NumberEntityDescription):
    update_command: str | None = None
    state: Callable[[defaultdict], Any] | None = None

NUMBERS: tuple[Sw42daNumberDescription, ...] = (
    Sw42daNumberDescription(
        key="main_volume",
        name="Main Volume",
        native_unit_of_measurement=PERCENTAGE,
        state=lambda data: data["AudioOut"][0]["Volume"],
        update_command="VOL XX",
    ),
    Sw42daNumberDescription(
        key="multichannel_line_volume",
        name="Multichannel Line Volume",
        native_unit_of_measurement=PERCENTAGE,
        state=lambda data: data["AudioOut"][1]["Volume"],
        update_command="OUT 21 VOL XX",
    ),
    Sw42daNumberDescription(
        key="downmix_line_volume",
        name="Downmix Line Volume",
        native_unit_of_measurement=PERCENTAGE,
        state=lambda data: data["AudioOut"][2]["Volume"],
        update_command="OUT 22 VOL XX",
    ),
    Sw42daNumberDescription(
        key="multichannel_dante_volume",
        name="Multichannel Dante Volume",
        native_unit_of_measurement=PERCENTAGE,
        state=lambda data: data["AudioOut"][3]["Volume"],
        update_command="OUT 23 VOL XX",
    ),
    Sw42daNumberDescription(
        key="downmix_dante_volume",
        name="Downmix Dante Volume",
        native_unit_of_measurement=PERCENTAGE,
        state=lambda data: data["AudioOut"][4]["Volume"],
        update_command="OUT 24 VOL XX",
    ),
)

async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities) -> None:
    """Set up the Sw42da number entity."""
    coordinator: Sw42daCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        Sw42daNumber(
            coordinator=coordinator,
            entity_description=entity_description,
        )
        for entity_description in NUMBERS
    )


class Sw42daNumber(Sw42daEntity, NumberEntity):
    entity_description: Sw42daNumberDescription
    _attr_has_entity_name = True

    def __init__(
            self,
            *,
            coordinator: Sw42daCoordinator,
            entity_description: Sw42daNumberDescription
    ) -> None:
        super().__init__(coordinator=coordinator)
        self.entity_description = entity_description
        self.entity_id = f"number.{DOMAIN}_{entity_description.key}"
        self._attr_unique_id = f"{DOMAIN}_number_{entity_description.key}"
        self._attr_name = entity_description.name
        self._attr_native_min_value = 0
        self._attr_native_max_value = 100
        self._attr_native_step = 1
        self._attr_native_unit_of_measurement = entity_description.unit_of_measurement

    @property
    def native_value(self) -> float | None:
        """Return the entity value to represent the entity state."""
        if self.entity_description.state is None:
            return None
        value = float(self.entity_description.state(self.coordinator.data))
        return value

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        try:
            _LOGGER.info("The number has changed, update Api")
            await self.hass.async_add_executor_job(
                self.send_command, self.entity_description.update_command.replace("XX", str(int(value)))
            )
            await self.coordinator.async_refresh()

        except Exception as err:
            _LOGGER.error(
                "Failed to set value for %s to %s: %s",
                self._attr_unique_id,
                value,
                err,
            )
            raise
