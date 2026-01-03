"""Support for Eltako devices."""

from dataclasses import dataclass, field
from enum import Enum, auto


class BinarySensorEntities(Enum):
    """Representation of the different Eltako binary sensor enitity types."""

    A5_07_01_OCCUPANCY = auto()
    A5_08_01_OCCUPANCY = auto()
    A5_13_01_WEATHER_STATION_RAIN = auto()
    A5_30_01_CONTACT = auto()
    A5_30_01_LOW_BATTERY = auto()
    A5_30_03_DIGITAL_INPUT_0 = auto()
    A5_30_03_DIGITAL_INPUT_1 = auto()
    A5_30_03_DIGITAL_INPUT_2 = auto()
    A5_30_03_DIGITAL_INPUT_3 = auto()
    A5_30_03_STATE_OF_WAKE = auto()
    F6_10_00_WINDOW = auto()
    F6_10_00_WINDOW_TILT = auto()
    D5_00_01_CONTACT = auto()


class ButtonEntities(Enum):
    """Representation of the different Eltako button enitity types."""


class CoverEntities(Enum):
    """Representation of the different Eltako cover enitity types."""

    STANDARD = auto()


class LightEntities(Enum):
    """Representation of the different Eltako light enitity types."""

    DIMMABLE = auto()
    SWITCHABLE = auto()


class SensorEntities(Enum):
    """Representation of the different Eltako sensor enitity types."""

    A5_04_01_TEMPERATURE = auto()
    A5_04_01_HUMIDITY = auto()
    A5_04_02_TEMPERATURE = auto()
    A5_04_02_HUMIDITY = auto()
    A5_04_03_TEMPERATURE = auto()
    A5_04_03_HUMIDITY = auto()
    A5_06_01_ILLUMINATION = auto()
    A5_07_01_PIR = auto()
    A5_07_01_VOLTAGE = auto()
    A5_08_01_TEMPERATURE = auto()
    A5_08_01_ILLUMINATION = auto()
    A5_08_01_BATTERY_VOLTAGE = auto()
    A5_09_0C_VOC = auto()
    A5_10_03_TEMPERATURE = auto()
    A5_10_03_TARGET_TEMPERATURE = auto()
    A5_10_06_TEMPERATURE = auto()
    A5_10_06_TARGET_TEMPERATURE = auto()
    A5_10_12_TEMPERATURE = auto()
    A5_10_12_HUMIDITY = auto()
    A5_10_12_TARGET_TEMPERATURE = auto()
    A5_12_01_ELECTRIC_ENERGY_0 = auto()
    A5_12_01_ELECTRIC_ENERGY_1 = auto()
    A5_12_01_POWER = auto()
    A5_12_02_GAS_METER = auto()
    A5_12_02_GAS_FLOW_RATE = auto()
    A5_12_03_WATER_METER = auto()
    A5_12_03_WATER_FLOW_RATE = auto()
    A5_13_01_WEATHER_STATION_ILLUMINANCE_DAWN = auto()
    A5_13_01_WEATHER_STATION_TEMPERATURE = auto()
    A5_13_01_WEATHER_STATION_WIND_SPEED = auto()
    A5_13_02_WEATHER_STATION_ILLUMINANCE_EAST = auto()
    A5_13_02_WEATHER_STATION_ILLUMINANCE_CENTRAL = auto()
    A5_13_02_WEATHER_STATION_ILLUMINANCE_WEST = auto()


class SwitchEntities(Enum):
    """Representation of the different Eltako switch enitity types."""

    STANDARD = auto()


@dataclass
class ModelDefinition:
    """Representation of an Eltako device model."""

    name: str
    # TODO maybe only one list of entities
    binary_sensors: list[BinarySensorEntities] = field(default_factory=list)
    buttons: list[ButtonEntities] = field(default_factory=list)
    covers: list[CoverEntities] = field(default_factory=list)
    lights: list[LightEntities] = field(default_factory=list)
    sensors: list[SensorEntities] = field(default_factory=list)
    switches: list[SwitchEntities] = field(default_factory=list)


@dataclass
class GatewayModelDefinition(ModelDefinition):
    """Representation of an Eltako gateway model."""

    is_bus_gw: bool = True
    baud_rate: int = 57600


GATEWAY_MODELS: dict[str, GatewayModelDefinition] = {
    "FAM14": GatewayModelDefinition(name="FAM14"),
    "FGW14USB": GatewayModelDefinition(name="FGW14USB"),
    "FAMUSB": GatewayModelDefinition(name="FAMUSB", baud_rate=9600),
    "USB300": GatewayModelDefinition(name="USB300", is_bus_gw=False),
    "ESP3": GatewayModelDefinition(name="ESP3 Gateway", is_bus_gw=False),
}

COVER_MODELS: dict[str, ModelDefinition] = {
    "FSB14": ModelDefinition(name="FSB14", covers=[CoverEntities.STANDARD]),
    "FSB14_12_24V_DC": ModelDefinition(
        name="FSB14/12-24V DC", covers=[CoverEntities.STANDARD]
    ),
    "FSB61_230V": ModelDefinition(name="FSB61-230V", covers=[CoverEntities.STANDARD]),
    "FSB61NP_230V": ModelDefinition(
        name="FSB61NP-230V", covers=[CoverEntities.STANDARD]
    ),
    "FSB71_230V": ModelDefinition(name="FSB71-230V", covers=[CoverEntities.STANDARD]),
    "FSB71_2x-230V": ModelDefinition(
        name="FSB71-2x-230V", covers=[CoverEntities.STANDARD]
    ),
    "FJ62_230V": ModelDefinition(name="FJ62-230V", covers=[CoverEntities.STANDARD]),
    "FJ62NP_230V": ModelDefinition(name="FJ62NP-230V", covers=[CoverEntities.STANDARD]),
    "FJ62_12_36VDC": ModelDefinition(
        name="FJ62/12-36VDC", covers=[CoverEntities.STANDARD]
    ),
}

LIGHT_MODELS: dict[str, ModelDefinition] = {
    "FSR14_2x_l": ModelDefinition(name="FSR14-2x", lights=[LightEntities.SWITCHABLE]),
    "FSR14_4x_l": ModelDefinition(name="FSR14-4x", lights=[LightEntities.SWITCHABLE]),
    "FSR14M_2x_l": ModelDefinition(
        name="FSR14M-2x",
        lights=[LightEntities.SWITCHABLE],
        sensors=SensorEntities.A5_12_01_POWER,
    ),
    "FSR14SSR_l": ModelDefinition(name="FSR14SSR", lights=[LightEntities.SWITCHABLE]),
    "FSR71_2x_230V_l": ModelDefinition(
        name="FSR71-2x-230V", lights=[LightEntities.SWITCHABLE]
    ),
    "FSR71NP_230V_l": ModelDefinition(
        name="FSR71NP-230V", lights=[LightEntities.SWITCHABLE]
    ),
    "FSR71NP_2x_230V_l": ModelDefinition(
        name="FSR71NP-2x-230V", lights=[LightEntities.SWITCHABLE]
    ),
    "FSR71NP_4x_230V_l": ModelDefinition(
        name="FSR71NP-4x-230V", lights=[LightEntities.SWITCHABLE]
    ),
    "FUD14": ModelDefinition(name="FUD14", lights=[LightEntities.DIMMABLE]),
    "FUD14_800W": ModelDefinition(name="FUD14-800W", lights=[LightEntities.DIMMABLE]),
    "FUD61NP_230V": ModelDefinition(
        name="FUD61NP-230V", lights=[LightEntities.DIMMABLE]
    ),
    "FUD61NPN_230V": ModelDefinition(
        name="FUD61NPN-230V", lights=[LightEntities.DIMMABLE]
    ),
    "FUD71_230V": ModelDefinition(name="FUD71-230V", lights=[LightEntities.DIMMABLE]),
    "FUD71_1200W_230V": ModelDefinition(
        name="FUD71/1200W-230V", lights=[LightEntities.DIMMABLE]
    ),
    "FSG14_1_10V": ModelDefinition(name="FSG14/1-10V", lights=[LightEntities.DIMMABLE]),
    "FSG71_1_10V": ModelDefinition(name="FSG71/1-10V", lights=[LightEntities.DIMMABLE]),
    "FDG14": ModelDefinition(name="FDG14", lights=[LightEntities.DIMMABLE]),
    "FDG62_230V": ModelDefinition(name="FDG62-230V", lights=[LightEntities.DIMMABLE]),
    "FDG71L_230V": ModelDefinition(name="FDG71L-230V", lights=[LightEntities.DIMMABLE]),
    "FKLD61": ModelDefinition(name="FKLD61", lights=[LightEntities.DIMMABLE]),
    "FLD61": ModelDefinition(name="FLD61", lights=[LightEntities.DIMMABLE]),
    "FRGBW14": ModelDefinition(name="FRGBW14", lights=[LightEntities.DIMMABLE]),
    "FRGBW71L": ModelDefinition(name="FRGBW71L", lights=[LightEntities.DIMMABLE]),
    "FSUD-230V": ModelDefinition(name="FSUD-230V", lights=[LightEntities.DIMMABLE]),
}

SENSOR_MODELS: dict[str, ModelDefinition] = {
    "FTKE": ModelDefinition(
        name="FTKE", binary_sensors=[BinarySensorEntities.F6_10_00_WINDOW]
    ),
    "FFTE": ModelDefinition(
        name="FFTE", binary_sensors=[BinarySensorEntities.F6_10_00_WINDOW]
    ),
    "FWS61": ModelDefinition(
        name="FWS61",
        sensors=[
            SensorEntities.A5_13_01_WEATHER_STATION_ILLUMINANCE_DAWN,
            SensorEntities.A5_13_01_WEATHER_STATION_TEMPERATURE,
            SensorEntities.A5_13_01_WEATHER_STATION_WIND_SPEED,
            SensorEntities.A5_13_02_WEATHER_STATION_ILLUMINANCE_CENTRAL,
            SensorEntities.A5_13_02_WEATHER_STATION_ILLUMINANCE_EAST,
            SensorEntities.A5_13_02_WEATHER_STATION_ILLUMINANCE_WEST,
        ],
    ),
}

SWITCH_MODELS: dict[str, ModelDefinition] = {
    "FSR14_2x": ModelDefinition(name="FSR14-2x", switches=[SwitchEntities.STANDARD]),
    "FSR14_4x": ModelDefinition(name="FSR14-4x", switches=[SwitchEntities.STANDARD]),
    "FSR14M_2x": ModelDefinition(
        name="FSR14M-2x",
        switches=[SwitchEntities.STANDARD],
        sensors=[SensorEntities.A5_12_01_POWER],
    ),
    "FSR14SSR": ModelDefinition(name="FSR14SSR", switches=[SwitchEntities.STANDARD]),
    "FSR71_2x_230V": ModelDefinition(
        name="FSR71-2x-230V", switches=[SwitchEntities.STANDARD]
    ),
    "FSR71NP_230V": ModelDefinition(
        name="FSR71NP-230V", switches=[SwitchEntities.STANDARD]
    ),
    "FSR71NP_2x_230V": ModelDefinition(
        name="FSR71NP-2x-230V", switches=[SwitchEntities.STANDARD]
    ),
    "FSR71NP_4x_230V": ModelDefinition(
        name="FSR71NP-4x-230V", switches=[SwitchEntities.STANDARD]
    ),
}

MODELS = GATEWAY_MODELS | COVER_MODELS | LIGHT_MODELS | SENSOR_MODELS | SWITCH_MODELS
