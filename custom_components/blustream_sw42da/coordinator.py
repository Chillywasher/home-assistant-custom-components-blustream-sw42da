import logging
from collections import defaultdict
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import COORDINATOR_NAME
from .sw42da_api import Sw42daApi

_LOGGER = logging.getLogger(__name__)


class Sw42daCoordinator(DataUpdateCoordinator[defaultdict]):
    """Sw42da Coordinator"""

    def __init__(
            self,
            hass: HomeAssistant,
            entry: ConfigEntry,
            controller: Sw42daApi
    ) -> None:
        """Initialize the coordinator."""

        self.controller = controller
        self.hass = hass

        super().__init__(
            hass,
            _LOGGER,
            name=COORDINATOR_NAME,
            config_entry=entry,
            update_interval=timedelta(seconds=30)
        )

    async def _async_update_data(self) -> defaultdict:
        raw = await self.hass.async_add_executor_job(self.controller.send_command, "STATUS")
        result = self.controller.parse_result(raw)
        return result
