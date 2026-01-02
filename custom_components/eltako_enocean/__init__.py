"""The Eltako integration."""

from dataclasses import dataclass
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant

from .const import PLATFORMS
from .gateway import EnOceanGateway

_LOGGER = logging.getLogger(__name__)


@dataclass
class EltakoData:
    """Storing Eltako gateway runtime data."""

    gateway: EnOceanGateway


type EltakoConfigEntry = ConfigEntry[EltakoData]


async def async_setup_entry(
    hass: HomeAssistant, config_entry: EltakoConfigEntry
) -> bool:
    """Set up an Eltako gateway and its devices for the given entry."""

    # Set up gateway
    enocean_gateway = EnOceanGateway(config_entry)
    await enocean_gateway.async_setup()
    config_entry.runtime_data = enocean_gateway
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant, config_entry: EltakoConfigEntry
) -> bool:
    """Unload Eltako config entry."""

    _LOGGER.info(
        "Unload %s and all its supported devices!", config_entry.data[CONF_NAME]
    )
    config_entry.runtime_data.unload()

    return True
