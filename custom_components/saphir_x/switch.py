"""Switch platform for Saphir X (relay toggles + sleepmode)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SaphirConfigEntry
from .const import RELAY_BITCODE, RELAY_REGISTER
from .entity import SaphirEntity

# Relay toggles: writing the bitcode toggles the relay. State is not reliably
# readable, so these are optimistic (assumed_state) switches.
RELAY_SWITCHES = ("light", "massage", "counter_current")


async def async_setup_entry(
    hass: HomeAssistant, entry: SaphirConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    entities: list[SwitchEntity] = [
        SaphirRelaySwitch(coordinator, key) for key in RELAY_SWITCHES
    ]
    entities.append(SaphirSleepmodeSwitch(coordinator))
    async_add_entities(entities)


class SaphirRelaySwitch(SaphirEntity, SwitchEntity):
    """Optimistic relay toggle (light / massage / counter-current)."""

    _attr_assumed_state = True

    def __init__(self, coordinator, key: str) -> None:
        super().__init__(coordinator)
        self._key = key
        self._bitcode = RELAY_BITCODE[key]
        self._attr_translation_key = key
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{key}"
        self._attr_is_on = False

    async def _pulse(self) -> None:
        await self.coordinator.client.async_pulse_relay(self._bitcode, RELAY_REGISTER)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._pulse()
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._pulse()
        self._attr_is_on = False
        self.async_write_ha_state()


class SaphirSleepmodeSwitch(SaphirEntity, SwitchEntity):
    """Sleepmode (data 110, 0/1) — real readable state."""

    _attr_translation_key = "sleepmode"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_sleepmode"

    @property
    def is_on(self) -> bool | None:
        raw = self.coordinator.data.get("110")
        return None if raw is None else raw == 1

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.client.async_write("110", 1)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.client.async_write("110", 0)
        await self.coordinator.async_request_refresh()
