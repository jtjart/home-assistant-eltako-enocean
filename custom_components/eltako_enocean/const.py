"""Constants for the Eltako (EnOcean) integration."""

DOMAIN = "eltako_enocean"
MANUFACTURER = "Eltako"

CONF_ASSUMED_STATE = "assumed_state"
CONF_FAST_STATUS_CHANGE = "fast_status_change"
CONF_GATEWAY_AUTO_RECONNECT = "auto_reconnect"
CONF_GATEWAY_MESSAGE_DELAY = "message_delay"
CONF_INVERT_SIGNAL = "invert_signal"
CONF_SENDER_ID = "sender_id"
CONF_SERIAL_PORT = "serial_port"
CONF_TIME_CLOSES = "time_closes"
CONF_TIME_OPENS = "time_opens"
CONF_TIME_TILTS = "time_tilts"

ID_REGEX = r"^([0-9a-fA-F]{2})-([0-9a-fA-F]{2})-([0-9a-fA-F]{2})-([0-9a-fA-F]{2})$"
