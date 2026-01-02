"""The Eltako integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import CONF_DEVICE_MODEL, DOMAIN, MANUFACTURER, PLATFORMS
from .device import MODELS
from .gateway import EnOceanGateway

_LOGGER = logging.getLogger(__name__)


type EltakoConfigEntry = ConfigEntry[EnOceanGateway]


async def async_setup_entry(
    hass: HomeAssistant, config_entry: EltakoConfigEntry
) -> bool:
    """Set up an Eltako gateway and its devices for the given entry."""

    # Set up gateway
    enocean_gateway = EnOceanGateway(config_entry)
    await enocean_gateway.async_setup()
    config_entry.runtime_data = enocean_gateway

    # Register gateway and devices
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, config_entry.unique_id)},
        manufacturer=MANUFACTURER,
        model=MODELS[config_entry.data[CONF_DEVICE_MODEL]].name,
        name=config_entry.data[CONF_NAME],
    )
    for subentry in config_entry.subentries.values():
        device_registry.async_get_or_create(
            config_entry_id=config_entry.entry_id,
            config_subentry_id=subentry.subentry_id,
            identifiers={(DOMAIN, f"{config_entry.unique_id}_{subentry.unique_id}")},
            manufacturer=MANUFACTURER,
            model=MODELS[subentry.data[CONF_DEVICE_MODEL]].name,
            name=subentry.data[CONF_NAME],
            via_device=(DOMAIN, config_entry.unique_id),
        )

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
