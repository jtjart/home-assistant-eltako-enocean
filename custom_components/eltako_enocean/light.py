"""Support for Eltako Enocean light sources."""

from dataclasses import dataclass
import logging
from typing import Any

from eltakobus.eep import (
    A5_38_08,
    F6_02_01,
    M5_38_08,
    CentralCommandDimming,
    CentralCommandSwitching,
)
from eltakobus.message import ESP2Message
from eltakobus.util import AddressExpression

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_TRANSITION,
    ColorMode,
    LightEntity,
    LightEntityDescription,
    LightEntityFeature,
)
from homeassistant.config_entries import ConfigSubentry
from homeassistant.const import CONF_MODEL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import UndefinedType
from homeassistant.util.scaling import scale_ranged_value_to_int_range

from . import EltakoConfigEntry
from .const import CONF_SENDER_ID
from .device import MODELS, LightEntities
from .entity import EltakoEntity

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class EltakoLightEntityDescription(LightEntityDescription):
    """Describes Eltako light entity."""

    key: str = ""
    has_entity_name: bool = True
    name: str | UndefinedType | None = None


class EltakoDimmableLight(EltakoEntity, LightEntity):
    """Representation of a dimmable Eltako light."""

    entity_description = EltakoLightEntityDescription()
    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_supported_features = LightEntityFeature.TRANSITION

    def __init__(
        self, config_entry: EltakoConfigEntry, subentry: ConfigSubentry
    ) -> None:
        """Initialize the dimmable Eltako light."""
        super().__init__(config_entry, subentry)
        self._sender_id = AddressExpression.parse(subentry.data[CONF_SENDER_ID])

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on or sets a specific dimmer value."""
        transition = min(int(kwargs.get(ATTR_TRANSITION, 0)), 255)
        brightness = kwargs.get(ATTR_BRIGHTNESS, 255)
        address, _ = self._sender_id

        brightness_percent = scale_ranged_value_to_int_range(
            (1, 255), (1, 100), brightness
        )

        dimming = CentralCommandDimming(brightness_percent, transition, 1, 0, 0, 1)
        msg = A5_38_08(command=0x02, dimming=dimming).encode_message(address)
        await self.async_send_message(msg)

        if self.gateway.fast_status_change:
            self._attr_brightness = brightness
            self._attr_is_on = True
            self.schedule_update_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        transition = min(int(kwargs.get(ATTR_TRANSITION, 0)), 255)
        address, _ = self._sender_id

        dimming = CentralCommandDimming(0, transition, 1, 0, 0, 0)
        msg = A5_38_08(command=0x02, dimming=dimming).encode_message(address)
        await self.async_send_message(msg)

        if self.gateway.fast_status_change:
            self._attr_brightness = 0
            self._attr_is_on = False
            self.schedule_update_ha_state()

    def value_changed(self, msg: ESP2Message) -> None:
        """Update the internal state of this device."""
        if msg.org == 0x05:
            _LOGGER.debug(
                "Device %s is outputing the switch confitmation telegram", self.dev_id
            )
            return
        decoded = A5_38_08.decode_message(msg)

        if isinstance(decoded.switching, CentralCommandSwitching):
            if decoded.switching.learn_button != 1:
                return
            self._attr_is_on = decoded.switching.switching_command

        elif isinstance(decoded.dimming, CentralCommandDimming):
            if decoded.dimming.learn_button != 1:
                return
            if decoded.dimming.dimming_range == 0:
                self._attr_brightness = scale_ranged_value_to_int_range(
                    (1, 100), (1, 255), decoded.dimming.dimming_value
                )
            elif decoded.dimming.dimming_range == 1:
                self._attr_brightness = decoded.dimming.dimming_value
            self._attr_is_on = decoded.dimming.switching_command

        else:
            return

        self.schedule_update_ha_state()


class EltakoSwitchableLight(EltakoEntity, LightEntity):
    """Representation of a switchable Eltako light."""

    entity_description = EltakoLightEntityDescription()
    _attr_color_mode = ColorMode.ONOFF
    _attr_supported_color_modes = {ColorMode.ONOFF}

    def __init__(
        self, config_entry: EltakoConfigEntry, subentry: ConfigSubentry
    ) -> None:
        """Initialize the Eltako light."""
        super().__init__(config_entry, subentry)
        self._sender_id = AddressExpression.parse(subentry.data[CONF_SENDER_ID])

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        address, _ = self._sender_id

        switching = CentralCommandSwitching(0, 1, 0, 0, 1)
        msg = A5_38_08(command=0x01, switching=switching).encode_message(address)
        await self.async_send_message(msg)

        if self.gateway.fast_status_change:
            self._attr_is_on = True
            self.schedule_update_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        address, _ = self._sender_id

        switching = CentralCommandSwitching(0, 1, 0, 0, 0)
        msg = A5_38_08(command=0x01, switching=switching).encode_message(address)
        await self.async_send_message(msg)

        if self.gateway.fast_status_change:
            self._attr_is_on = False
            self.schedule_update_ha_state()

    def value_changed(self, msg: ESP2Message) -> None:
        """Update the internal state of this device."""
        decoded = M5_38_08.decode_message(msg)

        self._attr_is_on = decoded.state
        self.schedule_update_ha_state()


class EltakoDumbLight(EltakoSwitchableLight):
    """Representation of a dumb switchable Eltako light.

    This is for devices, which do not support the controller telegrams (e.g. FMS14).
    Therefore pressing a button is simulated.
    """

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        address, _ = self._sender_id

        msg = F6_02_01(3, 1, 0, 0).encode_message(address)  # push button
        await self.async_send_message(msg)
        msg = F6_02_01(3, 0, 0, 0).encode_message(address)  # release button
        await self.async_send_message(msg)

        if self.gateway.fast_status_change:
            self._attr_is_on = True
            self.schedule_update_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        address, _ = self._sender_id

        msg = F6_02_01(2, 1, 0, 0).encode_message(address)  # push button
        await self.async_send_message(msg)
        msg = F6_02_01(2, 0, 0, 0).encode_message(address)  # release button
        await self.async_send_message(msg)

        if self.gateway.fast_status_change:
            self._attr_is_on = False
            self.schedule_update_ha_state()


ENTITY_CLASS_MAP: dict[LightEntities, type[EltakoEntity]] = {
    LightEntities.DIMMABLE: EltakoDimmableLight,
    LightEntities.DUMB: EltakoDumbLight,
    LightEntities.SWITCHABLE: EltakoSwitchableLight,
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: EltakoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Eltako light platform."""

    # Add devices' entities
    for subentry_id, subentry in config_entry.subentries.items():
        subentry_entities: list[EltakoEntity] = []
        device_model = MODELS[subentry.data[CONF_MODEL]]
        for entity_type in device_model.lights:
            sensor_class = ENTITY_CLASS_MAP.get(entity_type)
            if sensor_class:
                subentry_entities.append(sensor_class(config_entry, subentry))
        async_add_entities(subentry_entities, config_subentry_id=subentry_id)
