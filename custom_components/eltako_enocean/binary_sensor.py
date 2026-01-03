"""Support for Eltako binary sensors."""
# TODO add invert option

from __future__ import annotations

from dataclasses import dataclass
import logging

from eltakobus.eep import (
    A5_07_01,
    A5_08_01,
    A5_13_01,
    A5_30_01,
    A5_30_03,
    D5_00_01,
    F6_10_00,
    WindowHandlePosition,
)
from eltakobus.message import ESP2Message

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import EltakoConfigEntry
from .const import CONF_DEVICE_MODEL, DOMAIN
from .device import MODELS, BinarySensorEntities
from .entity import EltakoEntity
from .gateway import EnOceanGateway

_LOGGER = logging.getLogger(__name__)


@dataclass
class EltakoBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes Eltako binary sensor entity."""

    has_entity_name = True


class EltakoOccupancySensor(EltakoEntity, BinarySensorEntity):
    """Representation of an Eltako occupancy sensor."""

    entity_description = EltakoBinarySensorEntityDescription(
        key="occupancy",
        device_class=BinarySensorDeviceClass.MOTION,
    )


class EltakoOccupancySensor_A5_07_01(EltakoOccupancySensor):
    """Representation of an Eltako occupancy sensor (A5-07-01)."""

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        decoded = A5_07_01.decode_message(msg)
        if decoded.learn_button == 0:
            return
        self._attr_is_on = decoded.pir_status_on == 1
        self.schedule_update_ha_state()


class EltakoOccupancySensor_A5_08_01(EltakoOccupancySensor):
    """Representation of an Eltako occupancy sensor (A5-08-01)."""

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        decoded = A5_08_01.decode_message(msg)
        if decoded.learn_button == 0:
            return
        self._attr_is_on = decoded.pir_status == 1
        self.schedule_update_ha_state()


class EltakoContactSensor_A5_30_01(EltakoEntity, BinarySensorEntity):
    """Representation of an Eltako contact sensor (A5-30-01)."""

    entity_description = EltakoBinarySensorEntityDescription(
        key="contact", translation_key="contact"
    )

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""

        decoded = A5_30_01.decode_message(msg)
        if decoded.learn_button == 0:
            return
        self._attr_is_on = decoded.contact_closed
        self.schedule_update_ha_state()


class EltakoContactSensor_D5_00_01(EltakoEntity, BinarySensorEntity):
    """Representation of an Eltako contact sensor (D5-00-01)."""

    entity_description = EltakoBinarySensorEntityDescription(
        key="contact", translation_key="contact"
    )

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        decoded = D5_00_01.decode_message(msg)
        if decoded.learn_button == 0:
            return
        self._attr_is_on = decoded.contact
        self.schedule_update_ha_state()


class EltakoLowBatterySensor_A5_30_01(EltakoEntity, BinarySensorEntity):
    """Representation of an Eltako low battery sensor (A5-30-01)."""

    entity_description = EltakoBinarySensorEntityDescription(
        key="low_battery",
        device_class=BinarySensorDeviceClass.BATTERY,
    )

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""

        decoded = A5_30_01.decode_message(msg)
        if decoded.learn_button == 0:
            return
        self._attr_is_on = decoded.low_battery
        self.schedule_update_ha_state()


class EltakoDigitalInputSensor_0_A5_30_03(EltakoEntity, BinarySensorEntity):
    """Representation of an Eltako digital input sensor 0 (A5-30-03)."""

    entity_description = EltakoBinarySensorEntityDescription(
        key="digital_input_0",
        translation_key="digital_input",
        translation_placeholders={"index": "0"},
    )

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""

        decoded = A5_30_03.decode_message(msg)
        if decoded.learn_button == 0:
            return
        self._attr_is_on = decoded.digital_input_0
        self.schedule_update_ha_state()


class EltakoDigitalInputSensor_1_A5_30_03(EltakoEntity, BinarySensorEntity):
    """Representation of an Eltako digital input sensor 1 (A5-30-03)."""

    entity_description = EltakoBinarySensorEntityDescription(
        key="digital_input_1",
        translation_key="digital_input",
        translation_placeholders={"index": "1"},
    )

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""

        decoded = A5_30_03.decode_message(msg)
        if decoded.learn_button == 0:
            return
        self._attr_is_on = decoded.digital_input_1
        self.schedule_update_ha_state()


class EltakoDigitalInputSensor_2_A5_30_03(EltakoEntity, BinarySensorEntity):
    """Representation of an Eltako digital input sensor 2 (A5-30-03)."""

    entity_description = EltakoBinarySensorEntityDescription(
        key="digital_input_2",
        translation_key="digital_input",
        translation_placeholders={"index": "2"},
    )

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""

        decoded = A5_30_03.decode_message(msg)
        if decoded.learn_button == 0:
            return
        self._attr_is_on = decoded.digital_input_0
        self.schedule_update_ha_state()


class EltakoDigitalInputSensor_3_A5_30_03(EltakoEntity, BinarySensorEntity):
    """Representation of an Eltako digital input sensor 3 (A5-30-03)."""

    entity_description = EltakoBinarySensorEntityDescription(
        key="digital_input_3",
        translation_key="digital_input",
        translation_placeholders={"index": "3"},
    )

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""

        decoded = A5_30_03.decode_message(msg)
        if decoded.learn_button == 0:
            return
        self._attr_is_on = decoded.digital_input_3
        self.schedule_update_ha_state()


class EltakoWakeSensor_A5_30_03(EltakoEntity, BinarySensorEntity):
    """Representation of an Eltako wake sensor (A5-30-03)."""

    entity_description = EltakoBinarySensorEntityDescription(
        key="status_of_wake", translation_key="status_of_wake"
    )

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""

        decoded = A5_30_03.decode_message(msg)
        if decoded.learn_button == 0:
            return
        self._attr_is_on = decoded.status_of_wake
        self.schedule_update_ha_state()


class EltakoWindowSensor_F6_10_00(EltakoEntity, BinarySensorEntity):
    """Representation of an Eltako window sensor (F6-10-00)."""

    entity_description = EltakoBinarySensorEntityDescription(
        key="window", device_class=BinarySensorDeviceClass.WINDOW
    )

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""

        decoded = F6_10_00.decode_message(msg)
        self._attr_is_on = decoded.handle_position != WindowHandlePosition.CLOSED
        self.schedule_update_ha_state()


class EltakoWindowTiltSensor_F6_10_00(EltakoEntity, BinarySensorEntity):
    """Representation of an Eltako window tilt sensor (F6-10-00)."""

    entity_description = EltakoBinarySensorEntityDescription(
        key="window_tilt",
        translation_key="window_tilt",
        device_class=BinarySensorDeviceClass.WINDOW,
    )

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""

        decoded = F6_10_00.decode_message(msg)
        self._attr_is_on = decoded.handle_position == WindowHandlePosition.TILT
        self.schedule_update_ha_state()


class EltakoWeatherStationRainSensor(EltakoEntity, BinarySensorEntity):
    """Representation of an Eltako weather station rain sensor (A5-13-01)."""

    entity_description = EltakoBinarySensorEntityDescription(
        key="weather_station_rain",
        translation_key="weather_station_rain",
        device_class=BinarySensorDeviceClass.MOISTURE,
    )

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        decoded = A5_13_01.decode_message(msg)
        if decoded.learn_button != 1:
            return
        if decoded.identifier != 0x01:  # check if A5-13-01
            return
        self._attr_is_on = decoded.rain_indication
        self.schedule_update_ha_state()


class GatewayConnectionState(BinarySensorEntity):
    """Protocols last time when message received."""

    entity_description = EltakoBinarySensorEntityDescription(
        key="connection_state",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
    )

    def __init__(self, config_entry: ConfigEntry, gw: EnOceanGateway) -> None:
        """Initialize the Eltako gateway connection state sensor."""
        self._attr_gateway = gw
        self._attr_unique_id = f"{config_entry.unique_id}_{self.entity_description.key}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, gw.unique_id)})

    async def async_added_to_hass(self) -> None:
        """Call when entity about to be added to hass. Register callback."""
        self.async_on_remove(
            self._attr_gateway.register_connection_state_callback(self.state_changed)
        )

    def state_changed(self, state: bool) -> None:
        """Update the current state."""
        _LOGGER.debug("Gateway %s connected: %s", self._attr_gateway.unique_id, state)
        self._attr_is_on = state
        self.schedule_update_ha_state()


ENTITY_CLASS_MAP: dict[BinarySensorEntities, EltakoEntity] = {
    BinarySensorEntities.A5_07_01_OCCUPANCY: EltakoOccupancySensor_A5_07_01,
    BinarySensorEntities.A5_08_01_OCCUPANCY: EltakoOccupancySensor_A5_08_01,
    BinarySensorEntities.A5_13_01_WEATHER_STATION_RAIN: EltakoWeatherStationRainSensor,
    BinarySensorEntities.A5_30_01_CONTACT: EltakoContactSensor_A5_30_01,
    BinarySensorEntities.A5_30_01_LOW_BATTERY: EltakoLowBatterySensor_A5_30_01,
    BinarySensorEntities.A5_30_03_DIGITAL_INPUT_0: EltakoDigitalInputSensor_0_A5_30_03,
    BinarySensorEntities.A5_30_03_DIGITAL_INPUT_1: EltakoDigitalInputSensor_1_A5_30_03,
    BinarySensorEntities.A5_30_03_DIGITAL_INPUT_2: EltakoDigitalInputSensor_2_A5_30_03,
    BinarySensorEntities.A5_30_03_DIGITAL_INPUT_3: EltakoDigitalInputSensor_3_A5_30_03,
    BinarySensorEntities.A5_30_03_STATE_OF_WAKE: EltakoWakeSensor_A5_30_03,
    BinarySensorEntities.F6_10_00_WINDOW: EltakoWindowSensor_F6_10_00,
    BinarySensorEntities.F6_10_00_WINDOW_TILT: EltakoWindowTiltSensor_F6_10_00,
    BinarySensorEntities.D5_00_01_CONTACT: EltakoContactSensor_D5_00_01,
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: EltakoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Binary Sensor platform for Eltako."""
    gateway = config_entry.runtime_data

    # Add gateway's entities
    entities: list[BinarySensorEntity] = []
    entities.append(GatewayConnectionState(config_entry, gateway))
    async_add_entities(entities)

    # Add devices' entities
    for subentry_id, subentry in config_entry.subentries.items():
        subentry_entities: list[EltakoEntity] = []
        device_model = MODELS[subentry.data[CONF_DEVICE_MODEL]]
        for entity_type in device_model.binary_sensors:
            sensor_class = ENTITY_CLASS_MAP.get(entity_type)
            if sensor_class:
                subentry_entities.append(sensor_class(hass, subentry, gateway))
        async_add_entities(subentry_entities, config_subentry_id=subentry_id)
