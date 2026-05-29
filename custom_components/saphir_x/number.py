"""Number platform for Saphir X setpoints and dosing amounts."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import EntityCategory, UnitOfElectricPotential, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SaphirConfigEntry
from .entity import SaphirEntity


@dataclass(frozen=True, kw_only=True)
class SaphirNumberDescription(NumberEntityDescription):
    number: str
    factor: float = 1.0


NUMBERS: tuple[SaphirNumberDescription, ...] = (
    SaphirNumberDescription(
        key="ph_setpoint", number="200", factor=0.01, translation_key="ph_setpoint",
        device_class=NumberDeviceClass.PH, mode=NumberMode.BOX,
        native_min_value=6.5, native_max_value=8.0, native_step=0.01,
    ),
    SaphirNumberDescription(
        key="cl_setpoint", number="240", factor=0.01, translation_key="cl_setpoint",
        native_unit_of_measurement="mg/L", mode=NumberMode.BOX,
        native_min_value=0.0, native_max_value=3.0, native_step=0.01,
    ),
    SaphirNumberDescription(
        key="redox_target", number="241", factor=1.0, translation_key="redox_target",
        native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT, mode=NumberMode.BOX,
        native_min_value=400, native_max_value=900, native_step=1,
    ),
    SaphirNumberDescription(
        key="temperature_setpoint", number="290", factor=0.1,
        translation_key="temperature_setpoint",
        device_class=NumberDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS, mode=NumberMode.BOX,
        native_min_value=0.0, native_max_value=40.0, native_step=0.1,
    ),
    SaphirNumberDescription(
        key="cl_boost", number="247", factor=0.01, translation_key="cl_boost",
        native_unit_of_measurement="L", mode=NumberMode.BOX,
        native_min_value=0.0, native_max_value=10.0, native_step=0.01,
        entity_category=EntityCategory.CONFIG,
    ),
    SaphirNumberDescription(
        key="h2o2_boost", number="223", factor=0.01, translation_key="h2o2_boost",
        native_unit_of_measurement="L", mode=NumberMode.BOX,
        native_min_value=0.0, native_max_value=10.0, native_step=0.01,
        entity_category=EntityCategory.CONFIG,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: SaphirConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(SaphirNumber(coordinator, desc) for desc in NUMBERS)


class SaphirNumber(SaphirEntity, NumberEntity):
    """A writable Saphir setpoint."""

    entity_description: SaphirNumberDescription

    def __init__(self, coordinator, description: SaphirNumberDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{description.key}"

    @property
    def native_value(self) -> float | None:
        raw = self.coordinator.data.get(self.entity_description.number)
        if raw is None:
            return None
        return round(raw * self.entity_description.factor, 4)

    async def async_set_native_value(self, value: float) -> None:
        raw = int(round(value / self.entity_description.factor))
        await self.coordinator.client.async_write(self.entity_description.number, raw)
        await self.coordinator.async_request_refresh()
