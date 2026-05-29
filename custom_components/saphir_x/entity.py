"""Base entity for Saphir X."""

from __future__ import annotations

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SaphirCoordinator


class SaphirEntity(CoordinatorEntity[SaphirCoordinator]):
    """Common base: shared device + coordinator."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SaphirCoordinator) -> None:
        super().__init__(coordinator)
        data = coordinator.data or {}
        serial = data.get("001")
        sw = data.get("004")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.entry_id)},
            name="Saphir X Pool",
            manufacturer="SAPHIR Wassertechnologie",
            model=f"Ultra X (type {data.get('002')})" if data.get("002") else "Ultra X",
            serial_number=f"{serial:05d}" if isinstance(serial, int) else None,
            sw_version=str(sw) if sw is not None else None,
        )
