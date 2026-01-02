"""Support for Eltako light sources."""

from dataclasses import dataclass
import logging
from typing import Any

from eltakobus.eep import (
    A5_38_08,
    M5_38_08,
    CentralCommandDimming,
    CentralCommandSwitching,
)
from eltakobus.util import AddressExpression

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ColorMode,
    LightEntity,
    LightEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import EltakoConfigEntry
from .const import CONF_DEVICE_MODEL, CONF_SENDER_ID
from .device import MODELS, LightEntities
from .entity import EltakoEntity

_LOGGER = logging.getLogger(__name__)


@dataclass(kw_only=True)
class EltakoLightEntityDescription(LightEntityDescription):
    """Describes Eltako light entity."""

    key = ""
    has_entity_name = True
    name = None


class EltakoDimmableLight(EltakoEntity, LightEntity):
    """Representation of an Eltako light source."""

    entity_description = EltakoLightEntityDescription()
    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}

    def __init__(self, hass: HomeAssistant, config_entry, gw) -> None:
        """Initialize the Eltako light source."""
        super().__init__(hass, config_entry, gw)
        self._sender_id = AddressExpression.parse(config_entry.data[CONF_SENDER_ID])

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light source on or sets a specific dimmer value."""
        brightness = kwargs.get(ATTR_BRIGHTNESS, 255)

        address, _ = self._sender_id

        dimming = CentralCommandDimming(int(brightness / 255.0 * 100.0), 0, 1, 0, 0, 1)
        msg = A5_38_08(command=0x02, dimming=dimming).encode_message(address)
        await self.async_send_message(msg)

        if self.gateway.fast_status_change:
            self._attr_brightness = brightness
            self._attr_is_on = True
            self.schedule_update_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light source off."""
        address, _ = self._sender_id

        dimming = CentralCommandDimming(0, 0, 1, 0, 0, 0)
        msg = A5_38_08(command=0x02, dimming=dimming).encode_message(address)
        await self.async_send_message(msg)

        if self.gateway.fast_status_change:
            self._attr_brightness = 0
            self._attr_is_on = False
            self.schedule_update_ha_state()

    def value_changed(self, msg):
        """Update the internal state of this device.

        Dimmer devices like Eltako FUD61 send telegram in different RORGs.
        We only care about the 4BS (0xA5).
        """
        decoded = A5_38_08.decode_message(msg)

        if isinstance(decoded.switching, CentralCommandSwitching):
            if decoded.switching.learn_button != 1:
                return
            self._attr_is_on = decoded.switching.switching_command

        elif isinstance(decoded.dimming, CentralCommandDimming):
            if decoded.dimming.learn_button != 1:
                return
            if decoded.dimming.dimming_range == 0:
                self._attr_brightness = int(decoded.dimming.dimming_value * 100 / 255)
            elif decoded.dimming.dimming_range == 1:
                self._attr_brightness = decoded.dimming.dimming_value
            self._attr_is_on = decoded.dimming.switching_command

        else:
            return

        self.schedule_update_ha_state()


class EltakoSwitchableLight(EltakoEntity, LightEntity):
    """Representation of a switchable Eltako light source."""

    entity_description = EltakoLightEntityDescription()
    _attr_color_mode = ColorMode.ONOFF
    _attr_supported_color_modes = {ColorMode.ONOFF}

    def __init__(self, hass: HomeAssistant, config_entry, gw) -> None:
        """Initialize the Eltako light source."""
        super().__init__(hass, config_entry, gw)
        self._sender_id = AddressExpression.parse(config_entry.data[CONF_SENDER_ID])

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light source on or sets a specific dimmer value."""
        address, _ = self._sender_id

        switching = CentralCommandSwitching(0, 1, 0, 0, 1)
        msg = A5_38_08(command=0x01, switching=switching).encode_message(address)
        await self.async_send_message(msg)

        if self.gateway.fast_status_change:
            self._attr_is_on = True
            self.schedule_update_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light source off."""
        address, _ = self._sender_id

        switching = CentralCommandSwitching(0, 1, 0, 0, 0)
        msg = A5_38_08(command=0x01, switching=switching).encode_message(address)
        await self.async_send_message(msg)

        if self.gateway.fast_status_change:
            self._attr_is_on = False
            self.schedule_update_ha_state()

    def value_changed(self, msg):
        """Update the internal state of this device."""
        decoded = M5_38_08.decode_message(msg)

        self._attr_is_on = decoded.state
        self.schedule_update_ha_state()


ENTITY_CLASS_MAP: dict[LightEntities, EltakoEntity] = {
    LightEntities.DIMMABLE: EltakoDimmableLight,
    LightEntities.SWITCHABLE: EltakoSwitchableLight,
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: EltakoConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Eltako light platform."""
    entities: list[EltakoEntity] = []
    gateway = config_entry.runtime_data

    for subentry in config_entry.subentries.values():
        device_model = MODELS[subentry.data[CONF_DEVICE_MODEL]]
        for entity_type in device_model.lights:
            sensor_class = ENTITY_CLASS_MAP.get(entity_type)
            if sensor_class:
                entities.append(sensor_class(hass, subentry, gateway))

    async_add_entities(entities)
