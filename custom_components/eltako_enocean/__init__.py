"""The Eltako (EnOcean) integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_MODEL, CONF_NAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers import device_registry as dr

from .const import (
    CONF_FAST_STATUS_CHANGE,
    CONF_GATEWAY_AUTO_RECONNECT,
    CONF_GATEWAY_MESSAGE_DELAY,
    CONF_SERIAL_PORT,
    DOMAIN,
    MANUFACTURER,
)
from .device import GATEWAY_MODELS, MODELS
from .gateway import EnOceanGateway

_LOGGER = logging.getLogger(__name__)
_PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.COVER,
    Platform.LIGHT,
    Platform.SENSOR,
    Platform.SWITCH,
]

type EltakoConfigEntry = ConfigEntry[EnOceanGateway]


async def async_setup_entry(hass: HomeAssistant, entry: EltakoConfigEntry) -> bool:
    """Set up Eltako (EnOcean) from a config entry."""

    # Set up gateway
    enocean_gateway = EnOceanGateway(
        hass,
        GATEWAY_MODELS[entry.data[CONF_MODEL]],
        entry.data[CONF_SERIAL_PORT],
        entry.data[CONF_GATEWAY_AUTO_RECONNECT],
        entry.data[CONF_GATEWAY_MESSAGE_DELAY],
        entry.data[CONF_FAST_STATUS_CHANGE],
    )
    try:
        await enocean_gateway.async_setup()
    except Exception as e:
        raise ConfigEntryError(
            translation_domain=DOMAIN, translation_key="gateway_setup_failed"
        ) from e
    entry.runtime_data = enocean_gateway

    # Register gateway
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        manufacturer=MANUFACTURER,
        model=MODELS[entry.data[CONF_MODEL]].name,
        name=entry.data[CONF_NAME],
    )
    # Register devices
    for subentry in entry.subentries.values():
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            config_subentry_id=subentry.subentry_id,
            identifiers={(DOMAIN, f"{entry.entry_id}_{subentry.subentry_id}")},
            manufacturer=MANUFACTURER,
            model=MODELS[subentry.data[CONF_MODEL]].name,
            name=subentry.data[CONF_NAME],
            via_device=(DOMAIN, entry.entry_id),
        )

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    return True


async def async_reload_entry(hass: HomeAssistant, entry: EltakoConfigEntry) -> None:
    """Handle an options or subentry update by reloading the integration."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: EltakoConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)

    if unload_ok:
        _LOGGER.debug("Unloading Eltako gateway: %s", entry.data[CONF_NAME])
        await entry.runtime_data.async_unload()

    return unload_ok
