"""Constants for the Eltako integration."""

from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "eltako_enocean"
MANUFACTURER: Final = "Eltako"

CONF_DEVICE_MODEL: Final = "device_model"
CONF_FAST_STATUS_CHANGE: Final = "fast_status_change"
CONF_GATEWAY_AUTO_RECONNECT: Final = "auto_reconnect"
CONF_GATEWAY_MESSAGE_DELAY: Final = "message_delay"
CONF_INVERT_SIGNAL: Final = "invert_signal"
CONF_SENDER_ID: Final = "sender_id"
CONF_SERIAL_PORT: Final = "serial_port"
CONF_TIME_CLOSES: Final = "time_closes"
CONF_TIME_OPENS: Final = "time_opens"
CONF_TIME_TILTS: Final = "time_tilts"

ID_REGEX: Final = (
    r"^([0-9a-fA-F]{2})-([0-9a-fA-F]{2})-([0-9a-fA-F]{2})-([0-9a-fA-F]{2})$"
)

PLATFORMS: Final = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.COVER,
    Platform.LIGHT,
    Platform.SENSOR,
    Platform.SWITCH,
]
