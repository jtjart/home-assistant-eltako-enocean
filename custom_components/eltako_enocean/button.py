"""Support for Eltako Enocean buttons."""

from dataclasses import dataclass
import logging

from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import EltakoConfigEntry
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class EltakoButtonEntityDescription(ButtonEntityDescription):
    """Describes Eltako button entity."""

    has_entity_name: bool = True


class EltakoGatewayReconnectButton(ButtonEntity):
    """Button for reconnecting serial bus."""

    entity_description = EltakoButtonEntityDescription(
        key="reconnect",
        translation_key="reconnect_gateway",
        device_class=ButtonDeviceClass.RESTART,
        entity_category=EntityCategory.CONFIG,
    )

    def __init__(self, config_entry: EltakoConfigEntry) -> None:
        """Initialize the Eltako gateway connection state sensor."""
        self._attr_gateway = config_entry.runtime_data
        self._attr_unique_id = f"{config_entry.entry_id}_{self.entity_description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)}
        )

    async def async_press(self) -> None:
        """Reconnect serial bus."""
        self._attr_gateway._reconnect()


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: EltakoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up an Eltako buttons."""

    # Add gateway's entities
    entities: list[ButtonEntity] = []
    entities.append(EltakoGatewayReconnectButton(config_entry))
    async_add_entities(entities)
