"""Support for Eltako Enocean buttons."""

from dataclasses import dataclass
import logging

from eltakobus.eep import A5_38_08, CentralCommandSwitching
from eltakobus.message import ESP2Message
from eltakobus.util import AddressExpression

from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.config_entries import ConfigSubentry
from homeassistant.const import CONF_MODEL, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import EltakoConfigEntry
from .const import CONF_SENDER_ID, DOMAIN
from .device import MODELS, ButtonEntities
from .entity import EltakoEntity

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
        await self._attr_gateway.async_reconnect()


class EltakoButton(EltakoEntity, ButtonEntity):
    """Representation of an Eltako button device."""

    def __init__(
        self, config_entry: EltakoConfigEntry, subentry: ConfigSubentry
    ) -> None:
        """Initialize the Eltako button device."""
        super().__init__(config_entry, subentry)
        self._sender_id = AddressExpression.parse(subentry.data[CONF_SENDER_ID])

    def value_changed(self, msg: ESP2Message) -> None:
        """Do nothing."""


class EltakoPriorityOnButton_A5_38_08(EltakoButton):
    """Button for tunring on a switch with priority."""

    entity_description = EltakoButtonEntityDescription(
        key="priority_on",
        translation_key="priority_on",
        entity_category=EntityCategory.CONFIG,
    )

    async def async_press(self) -> None:
        """Turn on the switch with priority."""
        address, _ = self._sender_id

        switching = CentralCommandSwitching(0, 1, 1, 0, 1)
        msg = A5_38_08(command=0x01, switching=switching).encode_message(address)
        await self.async_send_message(msg)


class EltakoPriorityOffButton_A5_38_08(EltakoButton):
    """Button for tunring off a switch with priority."""

    entity_description = EltakoButtonEntityDescription(
        key="priority_off",
        translation_key="priority_off",
        entity_category=EntityCategory.CONFIG,
    )

    async def async_press(self) -> None:
        """Turn off the switch with priority."""
        address, _ = self._sender_id

        switching = CentralCommandSwitching(0, 1, 1, 0, 0)
        msg = A5_38_08(command=0x01, switching=switching).encode_message(address)
        await self.async_send_message(msg)


ENTITY_CLASS_MAP: dict[ButtonEntities, type[EltakoEntity]] = {
    ButtonEntities.A5_38_08_PRIORITY_ON: EltakoPriorityOnButton_A5_38_08,
    ButtonEntities.A5_38_08_PRIORITY_OFF: EltakoPriorityOffButton_A5_38_08,
}


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

    # Add devices's entities
    for subentry_id, subentry in config_entry.subentries.items():
        device_model = MODELS[subentry.data[CONF_MODEL]]
        subentry_entities = [
            ENTITY_CLASS_MAP[entity_type](config_entry, subentry)
            for entity_type in device_model.buttons
            if ENTITY_CLASS_MAP.get(entity_type)
        ]
        async_add_entities(subentry_entities, config_subentry_id=subentry_id)
