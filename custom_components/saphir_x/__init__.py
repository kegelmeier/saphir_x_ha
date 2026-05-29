"""The Saphir X Pool integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import SaphirCoordinator
from .saphir import SaphirClient

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.NUMBER,
    Platform.SWITCH,
    Platform.COVER,
    Platform.BUTTON,
]

type SaphirConfigEntry = ConfigEntry[SaphirCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: SaphirConfigEntry) -> bool:
    """Set up Saphir X from a config entry."""
    client = SaphirClient(
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
    )
    coordinator = SaphirCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: SaphirConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
