"""Support for Eltako buttons."""

from dataclasses import dataclass
import logging

from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import EltakoConfigEntry
from .entity import EltakoEntity

_LOGGER = logging.getLogger(__name__)


@dataclass(kw_only=True)
class EltakoButtonEntityDescription(ButtonEntityDescription):
    """Describes Eltako button entity."""

    has_entity_name = True


class EltakoGatewayReconnectButton(EltakoEntity, ButtonEntity):
    """Button for reconnecting serial bus."""

    entity_description = EltakoButtonEntityDescription(
        key="reconnect",
        translation_key="reconnect_gateway",
        device_class=ButtonDeviceClass.RESTART,
        entity_category=EntityCategory.CONFIG,
    )

    async def async_press(self) -> None:
        """Reconnect serial bus."""
        self.gateway.reconnect()


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: EltakoConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up an Eltako buttons."""
    entities: list[EltakoEntity] = []
    gateway = config_entry.runtime_data

    entities.append(EltakoGatewayReconnectButton(hass, config_entry, gateway))

    async_add_entities(entities)
