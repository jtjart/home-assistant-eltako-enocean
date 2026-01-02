"""Support for Eltako sensors."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from eltakobus.eep import (
    A5_04_01,
    A5_04_02,
    A5_04_03,
    A5_06_01,
    A5_07_01,
    A5_08_01,
    A5_09_0C,
    A5_10_03,
    A5_10_06,
    A5_10_12,
    A5_12_01,
    A5_12_02,
    A5_12_03,
    A5_13_01,
    VOC_SubstancesType,
)
from eltakobus.message import ESP2Message

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.const import (
    LIGHT_LUX,
    PERCENTAGE,
    EntityCategory,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfVolume,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from . import EltakoConfigEntry
from .const import CONF_DEVICE_MODEL, DOMAIN
from .device import MODELS, SensorEntities
from .entity import EltakoEntity
from .gateway import EnOceanGateway

_LOGGER = logging.getLogger(__name__)


@dataclass
class EltakoSensorEntityDescription(SensorEntityDescription):
    """Describes Eltako sensor entity."""

    has_entity_name = True


class EltakoSensor(EltakoEntity, SensorEntity):
    """Representation of an  Eltako sensor device such as a power meter."""

    _attr_native_value = None


class EltakoPirSensor_A5_07_01(EltakoSensor):
    """Occupancy Sensor."""

    entity_description = EltakoSensorEntityDescription(
        key="pir",
        translation_key="pir",
        state_class=SensorStateClass.MEASUREMENT,
    )

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        decoded = A5_07_01.decode_message(msg)
        self._attr_native_value = decoded.pir_status
        self.schedule_update_ha_state()


class EltakoVoltageSensor_A5_07_01(EltakoSensor):
    """Voltage Sensor (A5-07-01)."""

    entity_description = EltakoSensorEntityDescription(
        key="voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    )

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        decoded = A5_07_01.decode_message(msg)
        self._attr_native_value = decoded.support_voltage
        self.schedule_update_ha_state()


class EltakoPowerSensor_A5_12_01(EltakoSensor):
    """Representation of an Eltako power sensor (A5-12-01)."""

    entity_description = EltakoSensorEntityDescription(
        key="power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    )

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        decoded = A5_12_01.decode_message(msg)
        if decoded.learn_button != 1:
            return
        if not decoded.data_type:
            return  # commulative
        if msg.data[3] == 0x8F:
            return  # transmitting serial number of meter

        self._attr_native_value = round(decoded.meter_reading / 10**decoded.divisor, 2)
        self.schedule_update_ha_state()


class EltakoElectricEnergySensor_A5_12_01(EltakoSensor):
    """Representation of an Eltako electric enery sensor (A5-12-01)."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigSubentry,
        gw: EnOceanGateway,
        tariff: int,
    ) -> None:
        """Initialize the Eltako electric energy sensor."""
        self.entity_description = EltakoSensorEntityDescription(
            key=f"electric_energy_{tariff}",
            native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
            device_class=SensorDeviceClass.ENERGY,
            state_class=SensorStateClass.TOTAL_INCREASING,
        )
        super().__init__(hass, config_entry, gw)
        self._tariff = tariff
        # TODO disable as standard

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        decoded = A5_12_01.decode_message(msg)

        if decoded.learn_button != 1:
            return
        if decoded.data_type:
            return  # Not commulative

        if self._tariff == decoded.measurement_channel:
            calculatedValue = decoded.meter_reading / 10**decoded.divisor
            self._attr_native_value = round(calculatedValue, 2)
            self.schedule_update_ha_state()


class EltakoElectricEnergySensor_A5_12_01_0(EltakoElectricEnergySensor_A5_12_01):
    """Representation of an Eltako electric enery sensor (A5-12-01 Tariff 0)."""

    def __init__(
        self, hass: HomeAssistant, config_entry: ConfigSubentry, gw: EnOceanGateway
    ) -> None:
        """Initialize the Eltako electric energy sensor."""
        super().__init__(hass, config_entry, gw, 0)


class EltakoElectricEnergySensor_A5_12_01_1(EltakoElectricEnergySensor_A5_12_01):
    """Representation of an Eltako electric enery sensor (A5-12-01 Tariff 1)."""

    def __init__(
        self, hass: HomeAssistant, config_entry: ConfigSubentry, gw: EnOceanGateway
    ) -> None:
        """Initialize the Eltako electric energy sensor."""
        super().__init__(hass, config_entry, gw, 1)


class EltakoGasFlowRateSensor_A5_12_02(EltakoSensor):
    """Representation of an Eltako gas flow rate sensor (A5-12-02)."""

    entity_description = EltakoSensorEntityDescription(
        key="gas_flow_rate",
        translation_key="gas_flow_rate",
        native_unit_of_measurement=UnitOfVolumeFlowRate.LITERS_PER_SECOND,
        device_class=SensorDeviceClass.VOLUME_FLOW_RATE,
        state_class=SensorStateClass.MEASUREMENT,
    )

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        decoded = A5_12_02.decode_message(msg)
        if decoded.learn_button != 1:
            return
        if not decoded.data_type:
            return  # commulative

        self._attr_native_value = round(decoded.meter_reading / 10**decoded.divisor, 2)
        self.schedule_update_ha_state()


class EltakoGasMeterSensor_A5_12_02(EltakoSensor):
    """Representation of an Eltako gas meter sensor (A5-12-02)."""

    entity_description = EltakoSensorEntityDescription(
        key="gas_meter",
        translation_key="gas_meter",
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        device_class=SensorDeviceClass.GAS,
        state_class=SensorStateClass.TOTAL_INCREASING,
    )

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        decoded = A5_12_02.decode_message(msg)
        if decoded.learn_button != 1:
            return
        if decoded.data_type:
            return  # Not commulative
        if decoded.measurement_channel != 0:
            _LOGGER.warning("Tariffs currently not supported for gas meters")
            return

        self._attr_native_value = round(decoded.meter_reading / 10**decoded.divisor, 2)
        self.schedule_update_ha_state()


class EltakoWaterFlowRateSensor_A5_12_03(EltakoSensor):
    """Representation of an Eltako water flow rate sensor (A5-12-03)."""

    entity_description = EltakoSensorEntityDescription(
        key="water_flow_rate",
        translation_key="water_flow_rate",
        native_unit_of_measurement=UnitOfVolumeFlowRate.LITERS_PER_SECOND,
        device_class=SensorDeviceClass.VOLUME_FLOW_RATE,
        state_class=SensorStateClass.MEASUREMENT,
    )

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        decoded = A5_12_03.decode_message(msg)
        if decoded.learn_button != 1:
            return
        if not decoded.data_type:
            return  # commulative

        self._attr_native_value = round(decoded.meter_reading / 10**decoded.divisor, 2)
        self.schedule_update_ha_state()


class EltakoWaterMeterSensor_A5_12_03(EltakoSensor):
    """Representation of an Eltako water meter sensor (A5-12-03)."""

    entity_description = EltakoSensorEntityDescription(
        key="water_meter",
        translation_key="water_meter",
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL_INCREASING,
    )

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        decoded = A5_12_03.decode_message(msg)
        if decoded.learn_button != 1:
            return
        if decoded.data_type:
            return  # Not commulative
        if decoded.measurement_channel != 0:
            _LOGGER.warning("Tariffs currently not supported for water meters")
            return

        self._attr_native_value = round(decoded.meter_reading / 10**decoded.divisor, 2)
        self.schedule_update_ha_state()


class EltakoWeatherStationIlluminanceDawnSensor(EltakoSensor):
    """Representation of an Eltako weather station illuminance dawn sensor (A5-13-01)."""

    entity_description = EltakoSensorEntityDescription(
        key="weather_station_illuminance_dawn",
        translation_key="weather_station_illuminance_dawn",
        native_unit_of_measurement=LIGHT_LUX,
        device_class=SensorDeviceClass.ILLUMINANCE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    )

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        decoded = A5_13_01.decode_message(msg)
        if decoded.learn_button != 1:
            return
        if decoded.identifier != 0x01:  # check if A5-13-01
            return
        self._attr_native_value = decoded.dawn_sensor
        self.schedule_update_ha_state()


class EltakoWeatherStationTemperatureSensor(EltakoSensor):
    """Representation of an Eltako weather station temperature sensor (A5-13-01)."""

    entity_description = EltakoSensorEntityDescription(
        key="weather_station_temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    )

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        decoded = A5_13_01.decode_message(msg)
        if decoded.learn_button != 1:
            return
        if decoded.identifier != 0x01:  # check if A5-13-01
            return
        self._attr_native_value = decoded.temperature
        self.schedule_update_ha_state()


class EltakoWeatherStationWindSpeedSensor(EltakoSensor):
    """Representation of an Eltako weather station wind speed sensor (A5-13-01)."""

    entity_description = EltakoSensorEntityDescription(
        key="weather_station_wind_speed",
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    )

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        decoded = A5_13_01.decode_message(msg)
        if decoded.learn_button != 1:
            return
        if decoded.identifier != 0x01:  # check if A5-13-01
            return
        self._attr_native_value = decoded.wind_speed
        self.schedule_update_ha_state()


class EltakoWeatherStationIlluminanceWestSensor(EltakoSensor):
    """Representation of an Eltako weather station illuminance west sensor (A5-13-02)."""

    entity_description = EltakoSensorEntityDescription(
        key="weather_station_illuminance_west",
        translation_key="weather_station_illuminance_west",
        native_unit_of_measurement=LIGHT_LUX,
        device_class=SensorDeviceClass.ILLUMINANCE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    )

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        decoded = A5_13_01.decode_message(msg)  # actually A5_13_02
        if decoded.learn_button != 1:
            return
        if decoded.identifier != 0x02:  # check if A5-13-02
            return
        self._attr_native_value = decoded.sun_west * 1000.0
        self.schedule_update_ha_state()


class EltakoWeatherStationIlluminanceCentralSensor(EltakoSensor):
    """Representation of an Eltako weather station illuminance central sensor (A5-13-02)."""

    entity_description = EltakoSensorEntityDescription(
        key="weather_station_illuminance_central",
        translation_key="weather_station_illuminance_central",
        native_unit_of_measurement=LIGHT_LUX,
        device_class=SensorDeviceClass.ILLUMINANCE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    )

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        decoded = A5_13_01.decode_message(msg)  # actually A5_13_02
        if decoded.learn_button != 1:
            return
        if decoded.identifier != 0x02:  # check if A5-13-02
            return
        self._attr_native_value = decoded.sun_south * 1000.0
        self.schedule_update_ha_state()


class EltakoWeatherStationIlluminanceEastSensor(EltakoSensor):
    """Representation of an Eltako weather station illuminance east sensor (A5-13-02)."""

    entity_description = EltakoSensorEntityDescription(
        key="weather_station_illuminance_east",
        translation_key="weather_station_illuminance_east",
        native_unit_of_measurement=LIGHT_LUX,
        device_class=SensorDeviceClass.ILLUMINANCE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    )

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        decoded = A5_13_01.decode_message(msg)  # actually A5_13_02
        if decoded.learn_button != 1:
            return
        if decoded.identifier != 0x02:  # check if A5-13-02
            return
        self._attr_native_value = decoded.sun_east * 1000.0
        self.schedule_update_ha_state()


TEMPERATURE_DESCRIPTION = EltakoSensorEntityDescription(
    key="temperature",
    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    device_class=SensorDeviceClass.TEMPERATURE,
    state_class=SensorStateClass.MEASUREMENT,
    suggested_display_precision=1,
)


class EltakoTemperatureSensor_A5_04_01(EltakoSensor):
    """Representation of an Eltako temperature sensor (A5-04-01)."""

    entity_description = TEMPERATURE_DESCRIPTION

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        decoded = A5_04_01.decode_message(msg)
        self._attr_native_value = decoded.current_temperature
        self.schedule_update_ha_state()


class EltakoTemperatureSensor_A5_04_02(EltakoSensor):
    """Representation of an Eltako temperature sensor (A5-04-02)."""

    entity_description = TEMPERATURE_DESCRIPTION

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        decoded = A5_04_02.decode_message(msg)
        self._attr_native_value = decoded.current_temperature
        self.schedule_update_ha_state()


class EltakoTemperatureSensor_A5_04_03(EltakoSensor):
    """Representation of an Eltako temperature sensor (A5-04-03)."""

    entity_description = TEMPERATURE_DESCRIPTION

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        decoded = A5_04_03.decode_message(msg)
        self._attr_native_value = decoded.current_temperature
        self.schedule_update_ha_state()


class EltakoTemperatureSensor_A5_08_01(EltakoSensor):
    """Representation of an Eltako temperature sensor (A5-08-01)."""

    entity_description = TEMPERATURE_DESCRIPTION

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        decoded = A5_08_01.decode_message(msg)
        self._attr_native_value = decoded.current_temperature
        self.schedule_update_ha_state()


class EltakoTemperatureSensor_A5_10_03(EltakoSensor):
    """Representation of an Eltako temperature sensor (A5-10-03)."""

    entity_description = TEMPERATURE_DESCRIPTION

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        decoded = A5_10_03.decode_message(msg)
        self._attr_native_value = decoded.current_temperature
        self.schedule_update_ha_state()


class EltakoTemperatureSensor_A5_10_06(EltakoSensor):
    """Representation of an Eltako temperature sensor (A5-10-06)."""

    entity_description = TEMPERATURE_DESCRIPTION

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        decoded = A5_10_06.decode_message(msg)
        self._attr_native_value = decoded.current_temperature
        self.schedule_update_ha_state()


class EltakoTemperatureSensor_A5_10_12(EltakoSensor):
    """Representation of an Eltako temperature sensor (A5-10-12)."""

    entity_description = TEMPERATURE_DESCRIPTION

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        decoded = A5_10_12.decode_message(msg)
        self._attr_native_value = decoded.current_temperature
        self.schedule_update_ha_state()


ILLUMNATION_DESCRIPTION = EltakoSensorEntityDescription(
    key="illuminance",
    native_unit_of_measurement=LIGHT_LUX,
    device_class=SensorDeviceClass.ILLUMINANCE,
    state_class=SensorStateClass.MEASUREMENT,
    suggested_display_precision=0,
)


class EltakoIlluminationSensor_A5_06_01(EltakoSensor):
    """Representation of an Eltako brightness sensor (A5-06-01)."""

    entity_description = ILLUMNATION_DESCRIPTION

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        decoded = A5_06_01.decode_message(msg)
        self._attr_native_value = decoded.illumination
        self.schedule_update_ha_state()


class EltakoIlluminationSensor_A5_08_01(EltakoSensor):
    """Representation of an Eltako brightness sensor (A5-08-01)."""

    entity_description = ILLUMNATION_DESCRIPTION

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        decoded = A5_08_01.decode_message(msg)
        self._attr_native_value = decoded.illumination
        self.schedule_update_ha_state()


class EltakoBatteryVoltageSensor_A5_08_01(EltakoSensor):
    """Representation of an Eltako battery sensor."""

    entity_description = EltakoSensorEntityDescription(
        key="battery_voltage",
        name="Battery Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        icon="mdi:lightning-bolt",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    )

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        decoded = A5_08_01.decode_message(msg)
        self._attr_native_value = decoded.supply_voltage
        self.schedule_update_ha_state()


TARGET_TEMPERATURE_DESCRIPTION = EltakoSensorEntityDescription(
    key="target_temperature",
    translation_key="target_temperature",
    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    device_class=SensorDeviceClass.TEMPERATURE,
    state_class=SensorStateClass.MEASUREMENT,
    suggested_display_precision=1,
)


class EltakoTargetTemperatureSensor_A5_10_03(EltakoSensor):
    """Representation of an Eltako target temperature sensor (A5-10-03)."""

    entity_description = TARGET_TEMPERATURE_DESCRIPTION

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        decoded = A5_10_03.decode_message(msg)
        self._attr_native_value = round(2 * decoded.target_temperature, 0) / 2
        self.schedule_update_ha_state()


class EltakoTargetTemperatureSensor_A5_10_06(EltakoSensor):
    """Representation of an Eltako target temperature sensor (A5-10-06)."""

    entity_description = TARGET_TEMPERATURE_DESCRIPTION

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        decoded = A5_10_06.decode_message(msg)
        self._attr_native_value = round(2 * decoded.target_temperature, 0) / 2
        self.schedule_update_ha_state()


class EltakoTargetTemperatureSensor_A5_10_12(EltakoSensor):
    """Representation of an Eltako target temperature sensor (A5-10-12)."""

    entity_description = TARGET_TEMPERATURE_DESCRIPTION

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        decoded = A5_10_12.decode_message(msg)
        self._attr_native_value = round(2 * decoded.target_temperature, 0) / 2
        self.schedule_update_ha_state()


HUMIDITY_DESCRIPTION = EltakoSensorEntityDescription(
    key="humidity",
    native_unit_of_measurement=PERCENTAGE,
    device_class=SensorDeviceClass.HUMIDITY,
    state_class=SensorStateClass.MEASUREMENT,
    suggested_display_precision=1,
)


class EltakoHumiditySensor_A5_04_01(EltakoSensor):
    """Representation of an Eltako humidity sensor (A5-04-01)."""

    entity_description = HUMIDITY_DESCRIPTION

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        decoded = A5_04_01.decode_message(msg)
        self._attr_native_value = decoded.humidity
        self.schedule_update_ha_state()


class EltakoHumiditySensor_A5_04_02(EltakoSensor):
    """Representation of an Eltako humidity sensor (A5-04-02)."""

    entity_description = HUMIDITY_DESCRIPTION

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        decoded = A5_04_02.decode_message(msg)
        self._attr_native_value = decoded.humidity
        self.schedule_update_ha_state()


class EltakoHumiditySensor_A5_04_03(EltakoSensor):
    """Representation of an Eltako humidity sensor (A5-04-03)."""

    entity_description = HUMIDITY_DESCRIPTION

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        decoded = A5_04_03.decode_message(msg)
        self._attr_native_value = decoded.humidity
        self.schedule_update_ha_state()


class EltakoHumiditySensor_A5_10_12(EltakoSensor):
    """Representation of an Eltako humidity sensor (A5-10-12)."""

    entity_description = HUMIDITY_DESCRIPTION

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        decoded = A5_10_12.decode_message(msg)
        self._attr_native_value = decoded.humidity
        self.schedule_update_ha_state()


class EltakoVOCSensor_A5_09_0C(EltakoSensor):
    """Representation of an Eltako volatile organic Compound (VOC) sensor (A5-09-0C)."""

    def __init__(self, hass: HomeAssistant, config_entry, gw) -> None:
        """Initialize the Eltako VOC sensor."""
        # TODO get voc_type from eep.VOC_SubstancesType
        self._voc_type = VOC_SubstancesType.VOCT_TOTAL
        _voc_type_name = (
            self._voc_type.name_de
            if "de" in hass.config.language
            else self._voc_type.name_en
        )
        self.entity_description = EltakoSensorEntityDescription(
            key="voc_sensor_" + _voc_type_name.lower(),
            device_class=SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS,
            # device_class=SensorDeviceClass.AQI,
            name=_voc_type_name,  # TODO naming generic
            native_unit_of_measurement=self._voc_type.unit,  # TODO get unit from msg
            state_class=SensorStateClass.MEASUREMENT,
        )
        super().__init__(hass, config_entry, gw)
        # self._attr_suggested_unit_of_measurement = voc_type.unit

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        decoded = A5_09_0C.decode_message(msg)
        if decoded.voc_type.index == self._voc_type.index:
            self._attr_native_value = decoded.concentration
        self.schedule_update_ha_state()


class GatewayLastReceivedMessage(SensorEntity):
    """Protocols last time when message received."""

    entity_description = EltakoSensorEntityDescription(
        key="last_message_received",
        translation_key="last_message_received",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
    )

    def __init__(self, config_entry: ConfigEntry, gw: EnOceanGateway) -> None:
        """Initialize the Eltako gateway last message received sensor."""
        self._attr_gateway = gw
        self._attr_unique_id = f"{config_entry.unique_id}_{self.entity_description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.unique_id)}
        )
        self._attr_native_value = None

    async def async_added_to_hass(self) -> None:
        """Call when entity about to be added to hass. Register callback."""
        self.async_on_remove(
            self._attr_gateway.register_message_received_callback(self.update_to_now)
        )

    def update_to_now(self) -> None:
        """Update the current value to now."""
        self._attr_native_value = dt_util.now()
        self.schedule_update_ha_state()


class GatewayReceivedMessagesInActiveSession(SensorEntity):
    """Protocols amount of messages per session."""

    entity_description = EltakoSensorEntityDescription(
        key="received_messages_per_session",
        translation_key="received_messages_per_session",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.TOTAL_INCREASING,
    )

    def __init__(self, config_entry: ConfigEntry, gw: EnOceanGateway) -> None:
        """Initialize the Eltako gateway received message count sensor."""
        self._attr_gateway = gw
        self._attr_unique_id = f"{config_entry.unique_id}_{self.entity_description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.unique_id)}
        )
        self._attr_native_value = 0

    async def async_added_to_hass(self) -> None:
        """Call when entity about to be added to hass. Register callback."""
        self.async_on_remove(
            self._attr_gateway.register_message_received_callback(self.count_up)
        )

    def count_up(self) -> None:
        """Increase the current value by one."""
        self.native_value += 1
        self.schedule_update_ha_state()


# TODO maybe improve type hint of EltakoSensor like callback
ENTITY_CLASS_MAP: dict[SensorEntities, EltakoSensor] = {
    SensorEntities.A5_04_01_TEMPERATURE: EltakoTemperatureSensor_A5_04_01,
    SensorEntities.A5_04_01_HUMIDITY: EltakoHumiditySensor_A5_04_01,
    SensorEntities.A5_04_02_TEMPERATURE: EltakoTemperatureSensor_A5_04_02,
    SensorEntities.A5_04_02_HUMIDITY: EltakoHumiditySensor_A5_04_02,
    SensorEntities.A5_04_03_TEMPERATURE: EltakoTemperatureSensor_A5_04_03,
    SensorEntities.A5_04_03_HUMIDITY: EltakoHumiditySensor_A5_04_03,
    SensorEntities.A5_06_01_ILLUMINATION: EltakoIlluminationSensor_A5_06_01,
    SensorEntities.A5_07_01_PIR: EltakoPirSensor_A5_07_01,
    SensorEntities.A5_07_01_VOLTAGE: EltakoVoltageSensor_A5_07_01,
    SensorEntities.A5_08_01_TEMPERATURE: EltakoTemperatureSensor_A5_08_01,
    SensorEntities.A5_08_01_ILLUMINATION: EltakoIlluminationSensor_A5_08_01,
    SensorEntities.A5_08_01_BATTERY_VOLTAGE: EltakoBatteryVoltageSensor_A5_08_01,
    SensorEntities.A5_09_0C_VOC: EltakoVOCSensor_A5_09_0C,
    SensorEntities.A5_10_03_TEMPERATURE: EltakoTemperatureSensor_A5_10_03,
    SensorEntities.A5_10_03_TARGET_TEMPERATURE: EltakoTargetTemperatureSensor_A5_10_03,
    SensorEntities.A5_10_06_TEMPERATURE: EltakoTemperatureSensor_A5_10_06,
    SensorEntities.A5_10_06_TARGET_TEMPERATURE: EltakoTargetTemperatureSensor_A5_10_06,
    SensorEntities.A5_10_12_TEMPERATURE: EltakoTemperatureSensor_A5_10_12,
    SensorEntities.A5_10_12_HUMIDITY: EltakoHumiditySensor_A5_10_12,
    SensorEntities.A5_10_12_TARGET_TEMPERATURE: EltakoTargetTemperatureSensor_A5_10_12,
    SensorEntities.A5_12_01_ELECTRIC_ENERGY_0: EltakoElectricEnergySensor_A5_12_01_0,
    SensorEntities.A5_12_01_ELECTRIC_ENERGY_1: EltakoElectricEnergySensor_A5_12_01_1,
    SensorEntities.A5_12_01_POWER: EltakoPowerSensor_A5_12_01,
    SensorEntities.A5_12_02_GAS_METER: EltakoGasMeterSensor_A5_12_02,
    SensorEntities.A5_12_02_GAS_FLOW_RATE: EltakoGasFlowRateSensor_A5_12_02,
    SensorEntities.A5_12_03_WATER_METER: EltakoWaterMeterSensor_A5_12_03,
    SensorEntities.A5_12_03_WATER_FLOW_RATE: EltakoWaterFlowRateSensor_A5_12_03,
    SensorEntities.A5_13_01_WEATHER_STATION_ILLUMINANCE_DAWN: EltakoWeatherStationIlluminanceDawnSensor,
    SensorEntities.A5_13_01_WEATHER_STATION_TEMPERATURE: EltakoWeatherStationTemperatureSensor,
    SensorEntities.A5_13_01_WEATHER_STATION_WIND_SPEED: EltakoWeatherStationWindSpeedSensor,
    SensorEntities.A5_13_02_WEATHER_STATION_ILLUMINANCE_EAST: EltakoWeatherStationIlluminanceEastSensor,
    SensorEntities.A5_13_02_WEATHER_STATION_ILLUMINANCE_CENTRAL: EltakoWeatherStationIlluminanceCentralSensor,
    SensorEntities.A5_13_02_WEATHER_STATION_ILLUMINANCE_WEST: EltakoWeatherStationIlluminanceWestSensor,
    # TODO F6_...
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: EltakoConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up an Eltako sensor device."""
    entities: list[EltakoEntity] = []
    gateway = config_entry.runtime_data

    for subentry in config_entry.subentries.values():
        device_model = MODELS[subentry.data[CONF_DEVICE_MODEL]]
        for entity_type in device_model.sensors:
            sensor_class = ENTITY_CLASS_MAP.get(entity_type)
            if sensor_class:
                entities.append(sensor_class(hass, subentry, gateway))

    entities.append(GatewayLastReceivedMessage(config_entry, gateway))
    entities.append(GatewayReceivedMessagesInActiveSession(config_entry, gateway))

    async_add_entities(entities)
