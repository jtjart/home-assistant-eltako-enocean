"""Config flows for the Eltako integration."""

import logging
from typing import Any

import serial
import serial.tools.list_ports
import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentryFlow,
    SubentryFlowResult,
)
from homeassistant.const import CONF_ID, CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.schema_config_entry_flow import SchemaFlowError
from homeassistant.helpers.selector import AreaSelector

from .const import (
    CONF_AREA,
    CONF_DEVICE_MODEL,
    CONF_FAST_STATUS_CHANGE,
    CONF_GATEWAY_AUTO_RECONNECT,
    CONF_GATEWAY_MESSAGE_DELAY,
    CONF_SENDER_ID,
    CONF_SERIAL_PORT,
    CONF_TIME_CLOSES,
    CONF_TIME_OPENS,
    CONF_TIME_TILTS,
    DOMAIN,
    ID_REGEX,
)
from .device import COVER_MODELS, GATEWAY_MODELS, LIGHT_MODELS, SWITCH_MODELS

_LOGGER = logging.getLogger(__name__)


def _validate_enocean_id(user_input, key):
    try:
        cv.matches_regex(ID_REGEX)(user_input[key])
    except vol.Invalid as e:
        raise SchemaFlowError(key, "invalid_id") from e


def _validate_cover_times(user_input):
    has_closes = CONF_TIME_CLOSES in user_input
    has_opens = CONF_TIME_OPENS in user_input

    if has_closes != has_opens:
        raise SchemaFlowError(CONF_TIME_OPENS, "invalid_cover_time")


def _validate_gateway_path(user_input: dict[str, Any]):
    """Return True if the provided path points to a valid serial port, False otherwise."""

    serial_path: str = user_input[CONF_SERIAL_PORT]
    gw_model = GATEWAY_MODELS[user_input[CONF_DEVICE_MODEL]]

    try:
        serial.serial_for_url(serial_path, gw_model.baud_rate, timeout=0.1)
    except serial.SerialException as exception:
        _LOGGER.warning("Gateway path %s is invalid: %s", serial_path, str(exception))
        raise SchemaFlowError(CONF_SERIAL_PORT, "invalid_gateway_path") from exception


# TODO add options for message delay, auto reconnect, serial path
class EltakoFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle the Eltako config flows."""

    VERSION = 1
    MINOR_VERSION = 1

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        """Configure an Eltako Gateway."""
        errors: dict[str, str] = {}

        ports = await self.hass.async_add_executor_job(serial.tools.list_ports.comports)
        serial_ports = {p.device: f"{p.description} ({p.device})" for p in ports}
        if not serial_ports:
            errors[CONF_SERIAL_PORT] = "no_serial_ports"

        if user_input is not None:
            port = next(p for p in ports if p.device == user_input[CONF_SERIAL_PORT])
            await self.async_set_unique_id(port.serial_number)
            self._abort_if_unique_id_configured()
            try:
                _validate_enocean_id(user_input, CONF_ID)
                _validate_gateway_path(user_input)
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )
            except SchemaFlowError as e:
                errors[e.args[0]] = e.args[1]

        gateway_options = {key: model.name for key, model in GATEWAY_MODELS.items()}

        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default="Eltako Gateway"): str,
                vol.Required(CONF_DEVICE_MODEL): vol.In(gateway_options),
                vol.Required(CONF_SERIAL_PORT): vol.In(serial_ports),
                # TODO should have 00-00 for BUS and FF for transmitter
                vol.Required(CONF_ID, default="00-00-B0-00"): str,
                vol.Required(CONF_GATEWAY_AUTO_RECONNECT, default=True): bool,
                vol.Required(CONF_GATEWAY_MESSAGE_DELAY, default=0.01): vol.All(
                    vol.Coerce(float), vol.Range(min=0.0)
                ),
                vol.Required(CONF_FAST_STATUS_CHANGE, default=False): bool,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    @classmethod
    @callback
    def async_get_supported_subentry_types(
        cls, config_entry: ConfigEntry
    ) -> dict[str, type[ConfigSubentryFlow]]:
        """Return subentries supported by this integration."""
        return {"device": DeviceSubentryFlowHandler}


class DeviceSubentryFlowHandler(ConfigSubentryFlow):
    """Handle subentry flow for adding and modifying a device."""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """User flow to add a new device."""
        return self.async_show_menu(
            step_id="user",
            menu_options=["sensor", "actuator"],
        )

    # TODO
    async def async_step_sensor(self, user_input=None) -> SubentryFlowResult:
        """Add a sensor device."""
        return self.async_abort(reason="not_implemented yet")

    async def async_step_actuator(self, user_input=None) -> SubentryFlowResult:
        """Select the actuator type to add."""
        return self.async_show_menu(
            step_id="actuator",
            menu_options=[
                "cover",
                "switch",
                "light",
            ],
        )

    async def async_step_cover(self, user_input=None) -> SubentryFlowResult:
        """Add a cover device."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                _validate_enocean_id(user_input, CONF_ID)
                _validate_enocean_id(user_input, CONF_SENDER_ID)
                _validate_cover_times(user_input)
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=user_input,
                    unique_id=str(user_input[CONF_ID]).replace(" ", "-").upper(),
                )
            except SchemaFlowError as e:
                errors[e.args[0]] = e.args[1]

        device_options = {key: model.name for key, model in COVER_MODELS.items()}

        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME): cv.string,
                vol.Required(CONF_ID, default="00-00-00-01"): str,
                vol.Required(CONF_DEVICE_MODEL): vol.In(device_options),
                vol.Required(CONF_SENDER_ID, default="00-00-B0-01"): str,
                vol.Optional(CONF_AREA): AreaSelector(),
                vol.Optional(CONF_TIME_CLOSES): vol.All(
                    vol.Coerce(float), vol.Range(min=1, max=255)
                ),
                vol.Optional(CONF_TIME_OPENS): vol.All(
                    vol.Coerce(float), vol.Range(min=1, max=255)
                ),
                vol.Optional(CONF_TIME_TILTS): vol.All(
                    vol.Coerce(float), vol.Range(min=1, max=255)
                ),
            }
        )

        return self.async_show_form(
            step_id="cover", data_schema=data_schema, errors=errors
        )

    async def async_step_switch(self, user_input=None) -> SubentryFlowResult:
        """Add a switch device."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                _validate_enocean_id(user_input, CONF_ID)
                _validate_enocean_id(user_input, CONF_SENDER_ID)
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=user_input,
                    unique_id=str(user_input[CONF_ID]).replace(" ", "-").upper(),
                )
            except SchemaFlowError as e:
                errors[e.args[0]] = e.args[1]

        device_options = {key: model.name for key, model in SWITCH_MODELS.items()}

        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME): cv.string,
                vol.Required(CONF_ID, default="00-00-00-01"): str,
                vol.Required(CONF_DEVICE_MODEL): vol.In(device_options),
                vol.Required(CONF_SENDER_ID, default="00-00-B0-01"): str,
                vol.Optional(CONF_AREA): AreaSelector(),
            }
        )

        return self.async_show_form(
            step_id="switch", data_schema=data_schema, errors=errors
        )

    async def async_step_light(self, user_input=None) -> SubentryFlowResult:
        """Add a light device."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                _validate_enocean_id(user_input, CONF_ID)
                _validate_enocean_id(user_input, CONF_SENDER_ID)
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=user_input,
                    unique_id=str(user_input[CONF_ID]).replace(" ", "-").upper(),
                )
            except SchemaFlowError as e:
                errors[e.args[0]] = e.args[1]

        device_options = {key: model.name for key, model in LIGHT_MODELS.items()}

        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME): cv.string,
                vol.Required(CONF_ID, default="00-00-00-01"): str,
                vol.Required(CONF_DEVICE_MODEL): vol.In(device_options),
                vol.Required(CONF_SENDER_ID, default="00-00-B0-01"): str,
                vol.Optional(CONF_AREA): AreaSelector(),
            }
        )

        return self.async_show_form(
            step_id="light", data_schema=data_schema, errors=errors
        )
