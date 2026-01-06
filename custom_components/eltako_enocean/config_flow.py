"""Config flows for the Eltako Enocean integration."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
import logging
from typing import Any

import serial
import serial.tools.list_ports
import voluptuous as vol

from homeassistant.config_entries import (
    SOURCE_RECONFIGURE,
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentryFlow,
    SubentryFlowResult,
)
from homeassistant.const import CONF_ID, CONF_MODEL, CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.schema_config_entry_flow import SchemaFlowError

from .const import (
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
from .device import (
    COVER_MODELS,
    GATEWAY_MODELS,
    LIGHT_MODELS,
    SENSOR_MODELS,
    SWITCH_MODELS,
    ModelDefinition,
)

_LOGGER = logging.getLogger(__name__)


def _validate_enocean_id(user_input, key):
    try:
        cv.matches_regex(ID_REGEX)(user_input[key])
    except vol.Invalid as e:
        raise SchemaFlowError(key, "invalid_id") from e


def _validate_sender(user_input):
    _validate_enocean_id(user_input, CONF_SENDER_ID)


def _validate_cover(user_input):
    _validate_enocean_id(user_input, CONF_SENDER_ID)

    has_closes = CONF_TIME_CLOSES in user_input
    has_opens = CONF_TIME_OPENS in user_input
    if has_closes != has_opens:
        raise SchemaFlowError(CONF_TIME_OPENS, "invalid_cover_time")


def _validate_none(_):
    pass


def _validate_gateway_path(user_input: dict[str, Any]):
    """Return True if the provided path points to a valid serial port, False otherwise."""

    serial_path: str = user_input[CONF_SERIAL_PORT]
    gw_model = GATEWAY_MODELS[user_input[CONF_MODEL]]

    try:
        serial.serial_for_url(serial_path, gw_model.baud_rate, timeout=0.1)
    except serial.SerialException as exception:
        _LOGGER.warning("Gateway path %s is invalid: %s", serial_path, str(exception))
        raise SchemaFlowError(CONF_SERIAL_PORT, "invalid_gateway_path") from exception


def _get_model_options(models: Mapping[str, ModelDefinition]):
    return {key: model.name for key, model in models.items()}


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
            self._async_abort_entries_match(
                {CONF_SERIAL_PORT: user_input[CONF_SERIAL_PORT]}
            )
            try:
                _validate_enocean_id(user_input, CONF_ID)
                _validate_gateway_path(user_input)
            except SchemaFlowError as e:
                errors[e.args[0]] = e.args[1]
            else:
                if self.source == SOURCE_RECONFIGURE:
                    return self.async_update_reload_and_abort(
                        self._get_reconfigure_entry(), data_updates=user_input
                    )
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME): str,
                vol.Required(CONF_ID): str,
                vol.Required(CONF_MODEL): vol.In(_get_model_options(GATEWAY_MODELS)),
                vol.Required(CONF_SERIAL_PORT): vol.In(serial_ports),
                vol.Required(CONF_GATEWAY_AUTO_RECONNECT): bool,
                vol.Required(CONF_FAST_STATUS_CHANGE): bool,
                vol.Required(CONF_GATEWAY_MESSAGE_DELAY): vol.All(
                    vol.Coerce(float), vol.Range(min=0.0)
                ),
            }
        )
        suggested_values = {
            CONF_NAME: "Eltako Gateway",
            CONF_ID: "00-00-B0-00",
            CONF_GATEWAY_AUTO_RECONNECT: True,
            CONF_FAST_STATUS_CHANGE: True,
            CONF_GATEWAY_MESSAGE_DELAY: 0.01,
        }

        if user_input:
            data_schema = self.add_suggested_values_to_schema(data_schema, user_input)
        elif self.source == SOURCE_RECONFIGURE:
            data_schema = self.add_suggested_values_to_schema(
                data_schema, self._get_reconfigure_entry().data
            )
        else:
            data_schema = self.add_suggested_values_to_schema(
                data_schema, suggested_values
            )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors, last_step=True
        )

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None):
        """Reconfigure an Eltako Gateway."""
        return await self.async_step_user(user_input)

    @classmethod
    @callback
    def async_get_supported_subentry_types(
        cls, config_entry: ConfigEntry
    ) -> dict[str, type[ConfigSubentryFlow]]:
        """Return subentries supported by this integration."""
        return {"device": DeviceSubentryFlowHandler}


@dataclass(frozen=True)
class DeviceTypeConfig:
    """A class to configure the differet Eltako device types, that can be set up."""

    step_name: str
    models: Mapping[str, ModelDefinition]
    extra_schema: dict
    extra_validate: Callable[[dict], None]


class DeviceSubentryFlowHandler(ConfigSubentryFlow):
    """Handle subentry flow for adding and modifying an device."""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Select the devoce type to add."""
        return self.async_show_menu(
            step_id="user", menu_options=["cover", "switch", "light", "sensor"]
        )

    async def async_step_cover(self, user_input=None) -> SubentryFlowResult:
        """Add a cover device."""
        device_type_config = DeviceTypeConfig(
            step_name="cover",
            models=COVER_MODELS,
            extra_schema={
                vol.Required(CONF_SENDER_ID): str,
                vol.Optional(CONF_TIME_CLOSES): vol.All(
                    vol.Coerce(float), vol.Range(min=1, max=255)
                ),
                vol.Optional(CONF_TIME_OPENS): vol.All(
                    vol.Coerce(float), vol.Range(min=1, max=255)
                ),
                vol.Optional(CONF_TIME_TILTS): vol.All(
                    vol.Coerce(float), vol.Range(min=1, max=255)
                ),
            },
            extra_validate=_validate_cover,
        )
        return await self._async_step_device_type(device_type_config, user_input)

    async def async_step_switch(self, user_input=None) -> SubentryFlowResult:
        """Add a switch device."""
        device_type_config = DeviceTypeConfig(
            step_name="switch",
            models=SWITCH_MODELS,
            extra_schema={vol.Required(CONF_SENDER_ID): str},
            extra_validate=_validate_sender,
        )
        return await self._async_step_device_type(device_type_config, user_input)

    async def async_step_light(self, user_input=None) -> SubentryFlowResult:
        """Add a light device."""
        device_type_config = DeviceTypeConfig(
            step_name="light",
            models=LIGHT_MODELS,
            extra_schema={vol.Required(CONF_SENDER_ID): str},
            extra_validate=_validate_sender,
        )
        return await self._async_step_device_type(device_type_config, user_input)

    async def async_step_sensor(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Add a sensor device."""
        device_type_config = DeviceTypeConfig(
            step_name="sensor",
            models=SENSOR_MODELS,
            extra_schema={},
            extra_validate=_validate_none,
        )
        return await self._async_step_device_type(device_type_config, user_input)

    async def _async_step_device_type(
        self, device_type_config: DeviceTypeConfig, user_input
    ):
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                self._error_entries_match(user_input)
                _validate_enocean_id(user_input, CONF_ID)
                device_type_config.extra_validate(user_input)
            except SchemaFlowError as e:
                errors[e.args[0]] = e.args[1]
            else:
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )

        model_options = _get_model_options(device_type_config.models)
        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME): cv.string,
                vol.Required(CONF_ID): str,
                vol.Required(CONF_MODEL): vol.In(model_options),
            }
        )
        data_schema.extend(device_type_config.extra_schema)
        suggested_values = {
            CONF_ID: "00-00-00-01",
            CONF_SENDER_ID: "00-00-B0-01",
        }
        data_schema = self.add_suggested_values_to_schema(data_schema, suggested_values)

        return self.async_show_form(
            step_id=device_type_config.step_name,
            data_schema=data_schema,
            errors=errors,
            last_step=True,
        )

    def _error_entries_match(self, user_input):
        for subentry in self._get_entry().subentries.values():
            if str(user_input[CONF_ID]).lower() == str(subentry.data[CONF_ID]).lower():
                raise SchemaFlowError(CONF_ID, "already_configured")
