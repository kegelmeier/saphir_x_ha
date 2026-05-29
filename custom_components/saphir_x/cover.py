"""Cover platform for the Saphir X pool cover (Rollo)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.cover import (
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SaphirConfigEntry
from .const import RELAY_BITCODE, RELAY_REGISTER
from .entity import SaphirEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: SaphirConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([SaphirCover(entry.runtime_data)])


class SaphirCover(SaphirEntity, CoverEntity):
    """Pool cover driven by ROLLO_OPEN (32) / ROLLO_CLOSE (64) relay pulses.

    The controller exposes momentary relays with no position feedback, so this
    is an assumed-state cover.
    """

    _attr_assumed_state = True
    _attr_device_class = CoverDeviceClass.SHADE
    _attr_translation_key = "cover"
    _attr_supported_features = CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_cover"
        self._closed: bool | None = None

    @property
    def is_closed(self) -> bool | None:
        return self._closed

    async def async_open_cover(self, **kwargs: Any) -> None:
        await self.coordinator.client.async_pulse_relay(
            RELAY_BITCODE["cover_open"], RELAY_REGISTER
        )
        self._closed = False
        self.async_write_ha_state()

    async def async_close_cover(self, **kwargs: Any) -> None:
        await self.coordinator.client.async_pulse_relay(
            RELAY_BITCODE["cover_close"], RELAY_REGISTER
        )
        self._closed = True
        self.async_write_ha_state()
