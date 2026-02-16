from __future__ import annotations

import logging

from datetime import datetime

from homeassistant.core import State
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .import Sw42daCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class Sw42daEntity(CoordinatorEntity[Sw42daCoordinator], RestoreEntity):

    last_updated: datetime | None = None
    restored_state: State | None = None

    def send_command(self, command: str):
        _LOGGER.info("Roger that command: " + command)
        coordinator = self.coordinator
        coordinator.controller.send_command(command)

    @property
    def device_info(self) -> dict[str, object]:
        """Return the device_info of the device."""
        data = self.coordinator.data
        return {
            "identifiers": {(DOMAIN, data["Mac"])},
            "name": "SW42DA",
            "manufacturer": "Blustream",
            "model": "SW42DA",
            "sw_version": data["FW Version"],
            "serial_number": data["Mac"],
        }
