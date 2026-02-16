# import logging
#
# from homeassistant.core import HomeAssistant, ServiceCall
# from . import Sw42daApi
#
# _LOGGER = logging.getLogger(__name__)
#
#
# class Sw42daService:
#
#     def __init__(self, hass: HomeAssistant, api: Sw42daApi):
#         """Init."""
#         self.hass: HomeAssistant = hass
#         self.api = api
#
#     async def reboot_device(self, service_call: ServiceCall) -> None:
#         _LOGGER.info("Calling service")
#         self.api.send_command("REBOOT")
