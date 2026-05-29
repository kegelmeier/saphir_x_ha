"""Button platform for Saphir X one-shot actions."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SaphirConfigEntry
from .entity import SaphirEntity


@dataclass(frozen=True, kw_only=True)
class SaphirButtonDescription(ButtonEntityDescription):
    number: str
    value: int = 1


BUTTONS: tuple[SaphirButtonDescription, ...] = (
    SaphirButtonDescription(
        key="backwash", number="270", value=1, translation_key="backwash"
    ),
    SaphirButtonDescription(
        key="quit_error", number="100", value=1, translation_key="quit_error",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: SaphirConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(SaphirButton(coordinator, desc) for desc in BUTTONS)


class SaphirButton(SaphirEntity, ButtonEntity):
    entity_description: SaphirButtonDescription

    def __init__(self, coordinator, description: SaphirButtonDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{description.key}"

    async def async_press(self) -> None:
        await self.coordinator.client.async_write(
            self.entity_description.number, self.entity_description.value
        )
        await self.coordinator.async_request_refresh()
