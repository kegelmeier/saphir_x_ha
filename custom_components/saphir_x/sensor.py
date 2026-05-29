"""Sensor platform for Saphir X."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SaphirConfigEntry
from .const import ERROR_CODES, SENTINEL_NA
from .entity import SaphirEntity

PERCENTAGE = "%"


@dataclass(frozen=True, kw_only=True)
class SaphirSensorDescription(SensorEntityDescription):
    """Sensor description with the data number and scale factor."""

    number: str
    factor: float = 1.0
    # if True, a SENTINEL_NA raw value means "not installed" -> unavailable
    na_sentinel: bool = False


SENSORS: tuple[SaphirSensorDescription, ...] = (
    SaphirSensorDescription(
        key="water_temperature", number="006", factor=0.1,
        translation_key="water_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1,
    ),
    SaphirSensorDescription(
        key="ph", number="007", factor=0.01, translation_key="ph",
        device_class=SensorDeviceClass.PH,
        state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=2,
    ),
    SaphirSensorDescription(
        key="redox", number="008", factor=1.0, translation_key="redox",
        native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT, na_sentinel=True,
    ),
    SaphirSensorDescription(
        key="chlorine", number="009", factor=0.001, translation_key="chlorine",
        native_unit_of_measurement="mg/L",
        state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3,
        na_sentinel=True,
    ),
    SaphirSensorDescription(
        key="h2o2", number="010", factor=0.1, translation_key="h2o2",
        native_unit_of_measurement="mg/L",
        state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1,
        na_sentinel=True,
    ),
    SaphirSensorDescription(
        key="current", number="011", factor=0.01, translation_key="current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=2,
        entity_registry_enabled_default=False,
    ),
    SaphirSensorDescription(
        key="voltage", number="012", factor=0.1, translation_key="voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1,
        entity_registry_enabled_default=False,
    ),
    SaphirSensorDescription(
        key="fill_cu", number="020", factor=0.01, translation_key="fill_cu",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1,
    ),
    SaphirSensorDescription(
        key="fill_ph", number="021", factor=0.01, translation_key="fill_ph",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1,
    ),
    SaphirSensorDescription(
        key="fill_h2o2", number="022", factor=0.01, translation_key="fill_h2o2",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1,
    ),
    SaphirSensorDescription(
        key="fill_cl", number="023", factor=0.01, translation_key="fill_cl",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1,
    ),
    SaphirSensorDescription(
        key="fault", number="030", translation_key="fault",
        device_class=SensorDeviceClass.ENUM,
        options=sorted(set(ERROR_CODES.values()) | {"unknown"}),
    ),
    SaphirSensorDescription(
        key="serial_number", number="001", translation_key="serial_number",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: SaphirConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(SaphirSensor(coordinator, desc) for desc in SENSORS)


class SaphirSensor(SaphirEntity, SensorEntity):
    """A read-only Saphir value."""

    entity_description: SaphirSensorDescription

    def __init__(self, coordinator, description: SaphirSensorDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{description.key}"

    @property
    def available(self) -> bool:
        if not super().available:
            return False
        raw = self.coordinator.data.get(self.entity_description.number)
        if raw is None:
            return False
        if self.entity_description.na_sentinel and raw == SENTINEL_NA:
            return False
        return True

    @property
    def native_value(self):
        raw = self.coordinator.data.get(self.entity_description.number)
        if raw is None:
            return None
        if self.entity_description.key == "fault":
            return ERROR_CODES.get(raw, "unknown")
        if self.entity_description.key == "serial_number":
            return f"{raw:05d}"
        return round(raw * self.entity_description.factor, 4)
