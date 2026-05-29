"""DataUpdateCoordinator for Saphir X."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, POLL_NUMBERS
from .saphir import SaphirClient, SaphirError

_LOGGER = logging.getLogger(__name__)


class SaphirCoordinator(DataUpdateCoordinator[dict[str, int]]):
    """Polls the controller and exposes a {data_number: raw_value} mapping."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: SaphirClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Saphir X",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = client
        self.entry = entry

    async def _async_update_data(self) -> dict[str, int]:
        try:
            return await self.client.async_read(list(POLL_NUMBERS))
        except SaphirError as err:
            raise UpdateFailed(str(err)) from err
