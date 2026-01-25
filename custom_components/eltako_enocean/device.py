"""Support for Eltako Enocean devices."""

from dataclasses import dataclass, field
from enum import Enum, auto


class BinarySensorEntities(Enum):
    """Representation of the different Eltako binary sensor entity types."""

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
    """Representation of the different Eltako button entity types."""


class CoverEntities(Enum):
    """Representation of the different Eltako cover entity types."""

    STANDARD = auto()


class LightEntities(Enum):
    """Representation of the different Eltako light entity types."""

    DIMMABLE = auto()
    SWITCHABLE = auto()
    DUMB = auto()


class SensorEntities(Enum):
    """Representation of the different Eltako sensor entity types."""

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
    """Representation of the different Eltako switch entity types."""

    STANDARD = auto()
    DUMB = auto()


@dataclass
class ModelDefinition:
    """Representation of an Eltako device model."""

    name: str
    binary_sensors: set[BinarySensorEntities] = field(
        default_factory=set[BinarySensorEntities]
    )
    buttons: set[ButtonEntities] = field(default_factory=set[ButtonEntities])
    covers: set[CoverEntities] = field(default_factory=set[CoverEntities])
    lights: set[LightEntities] = field(default_factory=set[LightEntities])
    sensors: set[SensorEntities] = field(default_factory=set[SensorEntities])
    switches: set[SwitchEntities] = field(default_factory=set[SwitchEntities])


@dataclass
class GatewayModelDefinition(ModelDefinition):
    """Representation of an Eltako gateway model."""

    is_bus_gw: bool = True
    baud_rate: int = 57600


GATEWAY_MODELS: dict[str, GatewayModelDefinition] = {
    "FAM14": GatewayModelDefinition("FAM14"),
    "FGW14_USB": GatewayModelDefinition("FGW14USB"),
    "FAM_USB": GatewayModelDefinition("FAMUSB", baud_rate=9600),
    "USB_300": GatewayModelDefinition("USB 300", is_bus_gw=False),
    "ESP3": GatewayModelDefinition("ESP3 Gateway", is_bus_gw=False),
}

COVER_MODELS: dict[str, ModelDefinition] = {
    "FSB14": ModelDefinition("FSB14", covers={CoverEntities.STANDARD}),
    "FSB14_12_24V_DC": ModelDefinition(
        "FSB14/12-24V DC", covers={CoverEntities.STANDARD}
    ),
    "FSB61_230V": ModelDefinition("FSB61-230V", covers={CoverEntities.STANDARD}),
    "FSB61NP_230V": ModelDefinition("FSB61NP-230V", covers={CoverEntities.STANDARD}),
    "FSB71_230V": ModelDefinition("FSB71-230V", covers={CoverEntities.STANDARD}),
    "FSB71_2x-230V": ModelDefinition("FSB71-2x-230V", covers={CoverEntities.STANDARD}),
    "FJ62_230V": ModelDefinition("FJ62-230V", covers={CoverEntities.STANDARD}),
    "FJ62NP_230V": ModelDefinition("FJ62NP-230V", covers={CoverEntities.STANDARD}),
    "FJ62_12_36VDC": ModelDefinition("FJ62/12-36VDC", covers={CoverEntities.STANDARD}),
}

LIGHT_MODELS: dict[str, ModelDefinition] = {
    "FUD14": ModelDefinition("FUD14", lights={LightEntities.DIMMABLE}),
    "FUD14_800W": ModelDefinition("FUD14-800W", lights={LightEntities.DIMMABLE}),
    "FUD61NP_230V": ModelDefinition("FUD61NP-230V", lights={LightEntities.DIMMABLE}),
    "FUD61NPN_230V": ModelDefinition("FUD61NPN-230V", lights={LightEntities.DIMMABLE}),
    "FUD71_230V": ModelDefinition("FUD71-230V", lights={LightEntities.DIMMABLE}),
    "FUD71_1200W_230V": ModelDefinition(
        "FUD71/1200W-230V", lights={LightEntities.DIMMABLE}
    ),
    "FSG14_1_10V": ModelDefinition("FSG14/1-10V", lights={LightEntities.DIMMABLE}),
    "FSG71_1_10V": ModelDefinition("FSG71/1-10V", lights={LightEntities.DIMMABLE}),
    "FDG14": ModelDefinition("FDG14", lights={LightEntities.DIMMABLE}),
    "FDG62_230V": ModelDefinition("FDG62-230V", lights={LightEntities.DIMMABLE}),
    "FDG71L_230V": ModelDefinition("FDG71L-230V", lights={LightEntities.DIMMABLE}),
    "FKLD61": ModelDefinition("FKLD61", lights={LightEntities.DIMMABLE}),
    "FLD61": ModelDefinition("FLD61", lights={LightEntities.DIMMABLE}),
    "FRGBW14": ModelDefinition("FRGBW14", lights={LightEntities.DIMMABLE}),
    "FRGBW71L": ModelDefinition("FRGBW71L", lights={LightEntities.DIMMABLE}),
    "FSUD-230V": ModelDefinition("FSUD-230V", lights={LightEntities.DIMMABLE}),
    "FSR14_2x_l": ModelDefinition("FSR14-2x", lights={LightEntities.SWITCHABLE}),
    "FSR14_4x_l": ModelDefinition("FSR14-4x", lights={LightEntities.SWITCHABLE}),
    "FSR14M_2x_l": ModelDefinition(
        "FSR14M-2x",
        lights={LightEntities.SWITCHABLE},
        sensors={SensorEntities.A5_12_01_POWER},
    ),
    "FSR14SSR_l": ModelDefinition("FSR14SSR", lights={LightEntities.SWITCHABLE}),
    "FSR71_2x_230V_l": ModelDefinition(
        "FSR71-2x-230V", lights={LightEntities.SWITCHABLE}
    ),
    "FSR71NP_230V_l": ModelDefinition(
        "FSR71NP-230V", lights={LightEntities.SWITCHABLE}
    ),
    "FSR71NP_2x_230V_l": ModelDefinition(
        "FSR71NP-2x-230V", lights={LightEntities.SWITCHABLE}
    ),
    "FSR71NP_4x_230V_l": ModelDefinition(
        "FSR71NP-4x-230V", lights={LightEntities.SWITCHABLE}
    ),
    "FMS14_l": ModelDefinition("FMS14", lights={LightEntities.DUMB}),
}

SENSOR_MODELS: dict[str, ModelDefinition] = {
    "FTKE": ModelDefinition(
        "FTKE", binary_sensors={BinarySensorEntities.F6_10_00_WINDOW}
    ),
    "FFTE": ModelDefinition(
        "FFTE", binary_sensors={BinarySensorEntities.F6_10_00_WINDOW}
    ),
    "FWS61": ModelDefinition(
        "FWS61",
        sensors={
            SensorEntities.A5_13_01_WEATHER_STATION_ILLUMINANCE_DAWN,
            SensorEntities.A5_13_01_WEATHER_STATION_TEMPERATURE,
            SensorEntities.A5_13_01_WEATHER_STATION_WIND_SPEED,
            SensorEntities.A5_13_02_WEATHER_STATION_ILLUMINANCE_CENTRAL,
            SensorEntities.A5_13_02_WEATHER_STATION_ILLUMINANCE_EAST,
            SensorEntities.A5_13_02_WEATHER_STATION_ILLUMINANCE_WEST,
        },
    ),
}

SWITCH_MODELS: dict[str, ModelDefinition] = {
    "FSR14_2x": ModelDefinition("FSR14-2x", switches={SwitchEntities.STANDARD}),
    "FSR14_4x": ModelDefinition("FSR14-4x", switches={SwitchEntities.STANDARD}),
    "FSR14M_2x": ModelDefinition(
        "FSR14M-2x",
        switches={SwitchEntities.STANDARD},
        sensors={SensorEntities.A5_12_01_POWER},
    ),
    "FSR14SSR": ModelDefinition("FSR14SSR", switches={SwitchEntities.STANDARD}),
    "FSR71_2x_230V": ModelDefinition(
        "FSR71-2x-230V", switches={SwitchEntities.STANDARD}
    ),
    "FSR71NP_230V": ModelDefinition("FSR71NP-230V", switches={SwitchEntities.STANDARD}),
    "FSR71NP_2x_230V": ModelDefinition(
        "FSR71NP-2x-230V", switches={SwitchEntities.STANDARD}
    ),
    "FSR71NP_4x_230V": ModelDefinition(
        "FSR71NP-4x-230V", switches={SwitchEntities.STANDARD}
    ),
    "FMS14": ModelDefinition("FMS14", switches={SwitchEntities.DUMB}),
}

MODELS = GATEWAY_MODELS | COVER_MODELS | LIGHT_MODELS | SENSOR_MODELS | SWITCH_MODELS
