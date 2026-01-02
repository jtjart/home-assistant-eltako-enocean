"""Support for Eltako switches."""

from dataclasses import dataclass
import logging
from typing import Any

from eltakobus.eep import A5_38_08, M5_38_08, CentralCommandSwitching
from eltakobus.message import ESP2Message
from eltakobus.util import AddressExpression

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import EltakoConfigEntry
from .const import CONF_DEVICE_MODEL, CONF_SENDER_ID
from .device import MODELS, SwitchEntities
from .entity import EltakoEntity

_LOGGER = logging.getLogger(__name__)


@dataclass(kw_only=True)
class EltakoSwitchEntityDescription(SwitchEntityDescription):
    """Describes Eltako switch entity."""

    key = ""
    has_entity_name = True
    name = None


class EltakoStandardSwitch(EltakoEntity, SwitchEntity):
    """Representation of an Eltako switch device."""

    entity_description = EltakoSwitchEntityDescription()

    def __init__(self, hass: HomeAssistant, config_entry, gw) -> None:
        """Initialize the Eltako switch device."""
        super().__init__(hass, config_entry, gw)
        self._sender_id: AddressExpression = config_entry.data[CONF_SENDER_ID]

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the switch."""
        address, _ = self._sender_id

        switching = CentralCommandSwitching(0, 1, 0, 0, 1)
        msg = A5_38_08(command=0x01, switching=switching).encode_message(address)
        await self.async_send_message(msg)

        if self.gateway.fast_status_change():
            self._attr_is_on = True
            self.schedule_update_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the switch."""
        address, _ = self._sender_id

        switching = CentralCommandSwitching(0, 1, 0, 0, 0)
        msg = A5_38_08(command=0x01, switching=switching).encode_message(address)
        await self.async_send_message(msg)

        if self.gateway.fast_status_change():
            self._attr_is_on = False
            self.schedule_update_ha_state()

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the switch."""
        decoded = M5_38_08.decode_message(msg)

        self._attr_is_on = decoded.state
        self.schedule_update_ha_state()


ENTITY_CLASS_MAP: dict[SwitchEntities, EltakoEntity] = {
    SwitchEntities.STANDARD: EltakoStandardSwitch,
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: EltakoConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Eltako switch platform."""
    entities: list[EltakoEntity] = []
    gateway = config_entry.runtime_data.gateway

    device_model = MODELS[config_entry.data[CONF_DEVICE_MODEL]]
    for entity_type in device_model.switches:
        sensor_class = ENTITY_CLASS_MAP.get(entity_type)
        if sensor_class:
            entities.append(sensor_class(hass, config_entry, gateway))

    async_add_entities(entities)
