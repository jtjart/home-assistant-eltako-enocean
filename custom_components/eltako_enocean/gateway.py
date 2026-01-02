"""Representation of an Eltako gateway."""

from collections.abc import Callable
import logging

from eltakobus.eep import WrongOrgError
from eltakobus.message import (
    EltakoPoll,
    EltakoWrapped1BS,
    EltakoWrapped4BS,
    EltakoWrappedRPS,
    ESP2Message,
    Regular1BSMessage,
    Regular4BSMessage,
    RPSMessage,
)
from eltakobus.serial import RS485SerialInterfaceV2
from eltakobus.util import AddressExpression
from esp2_gateway_adapter.esp3_serial_com import ESP3SerialCommunicator

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ID, CONF_NAME

from .const import (
    CONF_DEVICE_MODEL,
    CONF_FAST_STATUS_CHANGE,
    CONF_GATEWAY_AUTO_RECONNECT,
    CONF_GATEWAY_MESSAGE_DELAY,
    CONF_SERIAL_PORT,
)
from .device import GATEWAY_MODELS

_LOGGER = logging.getLogger(__name__)

type MessageCallback = Callable[[ESP2Message], None]
type GwConnectionCallback = Callable[[bool], None]


class EnOceanGateway:
    """Representation of an Eltako gateway.

    The gateway is responsible for receiving the Eltako frames,
    creating devices if needed, and dispatching messages to platforms.
    """

    address_subscriptions: dict[AddressExpression, list[MessageCallback]] = {}
    general_subscriptions: list[Callable] = []
    connection_state_subscriptons: list[GwConnectionCallback] = []

    def __init__(self, config_entry: ConfigEntry = None) -> None:
        """Initialize the Eltako gateway."""
        self._attr_dev_name = config_entry.data[CONF_NAME]

        _LOGGER.info("Initializes Gateway Device '%s'", self._attr_dev_name)
        _LOGGER.debug(config_entry.data)

        self._device_model = GATEWAY_MODELS[config_entry.data[CONF_DEVICE_MODEL]]
        self._serial_port = str(config_entry.data[CONF_SERIAL_PORT])
        self._base_id = AddressExpression.parse(config_entry.data[CONF_ID])
        self._auto_reconnect_enabled = bool(
            config_entry.data[CONF_GATEWAY_AUTO_RECONNECT]
        )
        self._message_delay = float(config_entry.data[CONF_GATEWAY_MESSAGE_DELAY])
        self._fast_status_change = bool(config_entry.data[CONF_FAST_STATUS_CHANGE])
        self._baud_rate = self._device_model.baud_rate
        self._unique_id = config_entry.unique_id

        self._init_bus()

    def register_address_callback(
        self, address: AddressExpression, callback: MessageCallback
    ):
        """Register a callback for a specific address."""
        self.address_subscriptions.setdefault(address, []).append(callback)
        # Return an "unsubscribe" function
        return lambda: self.address_subscriptions[address].remove(callback)

    def register_message_received_callback(self, callback: Callable):
        """Register a callback for any message."""
        self.general_subscriptions.append(callback)
        # Return an "unsubscribe" function
        return lambda: self.general_subscriptions.remove(callback)

    def register_connection_state_callback(self, callback: GwConnectionCallback):
        """Register a callback for the gateway connection state."""
        self.connection_state_subscriptons.append(callback)
        callback(self._bus.is_active())
        # Return an "unsubscribe" function
        return lambda: self.connection_state_subscriptons.remove(callback)

    def _fire_connection_state_changed_event(self, status):
        for callback in self.connection_state_subscriptons:
            callback(status)

    def _init_bus(self):
        if self._device_model.is_bus_gw:
            self._bus = RS485SerialInterfaceV2(
                self._serial_port,
                baud_rate=self._baud_rate,
                callback=self._callback_receive_message_from_serial_bus,
                delay_message=self._message_delay,
                auto_reconnect=self._auto_reconnect_enabled,
            )
        else:
            self._bus = ESP3SerialCommunicator(
                filename=self._serial_port,
                callback=self._callback_receive_message_from_serial_bus,
                esp2_translation_enabled=True,
                auto_reconnect=self._auto_reconnect_enabled,
            )

        self._bus.set_status_changed_handler(self._fire_connection_state_changed_event)

    def reconnect(self):
        """Reconnecting the gateway."""
        self._bus.stop()
        self._init_bus()
        self._bus.start()

    async def async_setup(self):
        """Initialized serial bus and register callback function on HA event bus."""
        self._bus.start()
        _LOGGER.debug("%s was started", self.unique_id)

    def unload(self):
        """Unload the serial bus."""
        self._bus.stop()
        self._bus.join()
        _LOGGER.debug("%s was stopped", self.unique_id)

    async def async_send_message_to_serial_bus(self, msg):
        """Send a message to the serial bus."""
        if self._bus.is_active():
            if isinstance(msg, ESP2Message):
                _LOGGER.debug("Send message: %s (%s)", msg, msg.serialize().hex())

                await self._bus.send(msg)
        else:
            _LOGGER.warning("Serial port %s is not available", self.serial_port)

    def _callback_receive_message_from_serial_bus(self, msg):
        """Handle incoming EnOcean messages."""

        if isinstance(msg, EltakoPoll):
            return

        _LOGGER.debug("[%s] Received message: %s", self.unique_id, msg)
        for callback in self.general_subscriptions:
            callback()

        msg_classes = (
            EltakoWrappedRPS,
            EltakoWrapped1BS,
            EltakoWrapped4BS,
            RPSMessage,
            Regular1BSMessage,
            Regular4BSMessage,
        )

        if isinstance(msg, msg_classes) and msg.address in self.address_subscriptions:
            for callback in self.address_subscriptions[msg.address]:
                try:
                    callback(msg)
                except WrongOrgError:
                    _LOGGER.warning("Could not decode message: %s", msg)

    @property
    def unique_id(self) -> str:
        """Return the unique id of the gateway."""
        return self._unique_id

    @property
    def serial_port(self) -> str:
        """Return the serial port of the gateway."""
        return self._serial_port

    @property
    def dev_name(self) -> str:
        """Return the device name of the gateway."""
        return self._attr_dev_name

    @property
    def base_id(self) -> AddressExpression:
        """Return the base id of the gateway."""
        return self._base_id

    @property
    def model(self) -> str:
        """Return the model of the gateway."""
        return self._device_model.name

    @property
    def message_delay(self) -> float:
        """Return the message delay of single telegrams to be sent."""
        return self._message_delay

    @property
    def fast_status_change(self) -> bool:
        """Return whether the gateway is set up to change the entities status directly."""
        return self._fast_status_change

    @property
    def auto_reconnect_enabled(self) -> bool:
        """Return if auto connected is enabled."""
        return self._auto_reconnect_enabled
