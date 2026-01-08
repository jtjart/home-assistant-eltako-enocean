"""Support for Eltako Enocean covers."""

import asyncio
from dataclasses import dataclass
import logging
from typing import Any

from eltakobus.eep import G5_3F_7F, H5_3F_7F
from eltakobus.message import ESP2Message
from eltakobus.util import AddressExpression

from homeassistant.components.cover import (
    ATTR_POSITION,
    ATTR_TILT_POSITION,
    CoverEntity,
    CoverEntityDescription,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigSubentry
from homeassistant.const import CONF_MODEL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import UndefinedType

from . import EltakoConfigEntry
from .const import CONF_SENDER_ID, CONF_TIME_CLOSES, CONF_TIME_OPENS, CONF_TIME_TILTS
from .device import MODELS, CoverEntities
from .entity import EltakoEntity

_LOGGER = logging.getLogger(__name__)

DIRECTION_UP = "UP"
DIRECTION_DOWN = "DOWN"


@dataclass(frozen=True)
class EltakoCoverEntityDescription(CoverEntityDescription):
    """Describes Eltako switch entity."""

    key: str = ""
    has_entity_name: bool = True
    name: str | UndefinedType | None = None


class EltakoStandardCover(EltakoEntity, CoverEntity):
    """Representation of an Eltako cover device."""

    entity_description = EltakoCoverEntityDescription()

    def __init__(
        self, config_entry: EltakoConfigEntry, subentry: ConfigSubentry
    ) -> None:
        """Initialize the Eltako cover device."""
        super().__init__(config_entry, subentry)
        self._sender_id = AddressExpression.parse(subentry.data[CONF_SENDER_ID])
        self._time_closes: int | None = None
        self._time_opens: int | None = None
        self._time_tilts: float | None = None

        self._attr_is_closed = None  # means undefined state

        self._attr_supported_features = (
            CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP
        )

        if CONF_TIME_CLOSES in subentry.data and CONF_TIME_OPENS in subentry.data:
            self._attr_supported_features |= CoverEntityFeature.SET_POSITION
            self._time_closes = int(subentry.data[CONF_TIME_CLOSES])
            self._time_opens = int(subentry.data[CONF_TIME_OPENS])

        if CONF_TIME_TILTS in subentry.data:
            self._attr_supported_features |= CoverEntityFeature.SET_TILT_POSITION
            self._time_tilts = float(subentry.data[CONF_TIME_TILTS])

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        if self._time_opens is not None:
            moving_time = self._time_opens + 1
        else:
            moving_time = 255

        address, _ = self._sender_id

        msg = H5_3F_7F(moving_time, 0x01, 1).encode_message(address)
        await self.async_send_message(msg)

        if self.gateway.fast_status_change:
            self._attr_is_opening = True
            self._attr_is_closing = False
            self.schedule_update_ha_state()

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close cover."""
        if self._time_closes is not None:
            moving_time = self._time_closes + 1
        else:
            moving_time = 255

        await self.async_send_message(
            H5_3F_7F(moving_time, 0x02, 1).encode_message(self._sender_id[0])
        )

        if self.gateway.fast_status_change:
            self._attr_is_closing = True
            self._attr_is_opening = False

            self.schedule_update_ha_state()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific position."""
        position = kwargs[ATTR_POSITION]

        if self._time_closes is None or self._time_opens is None:
            return
        if self._attr_current_cover_position is None:
            return
        if position == self._attr_current_cover_position:
            return

        if position == 100:
            direction = DIRECTION_UP
            moving_time = self._time_opens + 1
        elif position == 0:
            direction = DIRECTION_DOWN
            moving_time = -(self._time_closes + 1)
        elif position > self._attr_current_cover_position:
            direction = DIRECTION_UP
            moving_time = int(
                ((position - self._attr_current_cover_position) / 100.0)
                * self._time_opens
            )
        elif position < self._attr_current_cover_position:
            direction = DIRECTION_DOWN
            moving_time = int(
                ((self._attr_current_cover_position - position) / 100.0)
                * self._time_closes
            )
        else:
            return

        command = 0x01 if direction == DIRECTION_UP else 0x02
        moving_time = max(1, min(moving_time, 255))
        await self.async_send_message(
            H5_3F_7F(moving_time, command, 1).encode_message(self._sender_id[0])
        )

        if self.gateway.fast_status_change:
            if direction == DIRECTION_UP:
                self._attr_is_opening = True
                self._attr_is_closing = False
            elif direction == DIRECTION_DOWN:
                self._attr_is_closing = True
                self._attr_is_opening = False
            self.schedule_update_ha_state()

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover."""
        await self.async_send_message(
            H5_3F_7F(0, 0x00, 1).encode_message(self._sender_id[0])
        )

        if self.gateway.fast_status_change:
            self._attr_is_closing = False
            self._attr_is_opening = False
            self.schedule_update_ha_state()

    async def async_set_cover_tilt_position(self, **kwargs: Any) -> None:
        """Move the cover tilt to a specific position."""
        if self._time_tilts is None:
            return
        if self._attr_current_cover_tilt_position is None:
            return

        tilt_position = int(kwargs[ATTR_TILT_POSITION])
        tilt_diff = tilt_position - self._attr_current_cover_tilt_position

        if tilt_diff > 0:
            direction = DIRECTION_UP
        elif tilt_diff < 0:
            direction = DIRECTION_DOWN
        else:
            return
        sleeptime = abs(tilt_diff) / 100.0 * self._time_tilts

        address = self._sender_id[0]
        command = 0x01 if direction == DIRECTION_UP else 0x02  # up or down
        msg = H5_3F_7F(0, command, 1).encode_message(address)
        await self.async_send_message(msg)
        await asyncio.sleep(min(sleeptime, 255))
        msg = H5_3F_7F(0, 0x00, 1).encode_message(address)
        await self.async_send_message(msg)

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the cover."""
        decoded = G5_3F_7F.decode_message(msg)

        if msg.org == 0x05:
            match decoded.state:
                case 0x02:  # down
                    self._attr_is_closing = True
                    self._attr_is_opening = False
                    self._attr_is_closed = False
                case 0x50:  # closed
                    self._attr_is_opening = False
                    self._attr_is_closing = False
                    self._attr_is_closed = True
                    self._attr_current_cover_position = 0
                    self._attr_current_cover_tilt_position = 0
                case 0x01:  # up
                    self._attr_is_opening = True
                    self._attr_is_closing = False
                    self._attr_is_closed = False
                case 0x70:  # open
                    self._attr_is_opening = False
                    self._attr_is_closing = False
                    self._attr_is_closed = False
                    self._attr_current_cover_position = 100
                    self._attr_current_cover_tilt_position = 100

        elif msg.org == 0x07:
            if decoded.time is None:
                return
            time_in_seconds = int(decoded.time) / 10.0
            self._attr_is_opening = False
            self._attr_is_closing = False

            if decoded.direction == 0x01:  # up
                self._attr_is_closed = False
                if self._time_opens:
                    if self._attr_current_cover_position is None:
                        self._attr_current_cover_position = 0  # guessing
                    self._attr_current_cover_position = min(
                        self._attr_current_cover_position
                        + int(time_in_seconds / self._time_opens * 100.0),
                        100,
                    )
                    if self._time_tilts:
                        if self._attr_current_cover_tilt_position is None:
                            self._attr_current_cover_tilt_position = 0  # guessing
                        self._attr_current_cover_tilt_position = min(
                            self._attr_current_cover_tilt_position
                            + int(time_in_seconds / self._time_tilts * 100.0),
                            100,
                        )

            else:  # down
                self._attr_is_closed = True
                if self._time_closes:
                    if self._attr_current_cover_position is None:
                        self._attr_current_cover_position = 100  # guessing
                    self._attr_current_cover_position = max(
                        self._attr_current_cover_position
                        - int(time_in_seconds / self._time_closes * 100.0),
                        0,
                    )
                    if self._time_tilts:
                        if self._attr_current_cover_tilt_position is None:
                            self._attr_current_cover_tilt_position = 100  # guessing
                        self._attr_current_cover_tilt_position = max(
                            self._attr_current_cover_tilt_position
                            - int(time_in_seconds / self._time_tilts * 100.0),
                            0,
                        )
                    self._attr_is_closed = self._attr_current_cover_position == 0

        self.schedule_update_ha_state()


ENTITY_CLASS_MAP: dict[CoverEntities, type[EltakoEntity]] = {
    CoverEntities.STANDARD: EltakoStandardCover,
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: EltakoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Eltako cover platform."""

    # Add devices' entities
    for subentry_id, subentry in config_entry.subentries.items():
        subentry_entities: list[EltakoEntity] = []
        device_model = MODELS[subentry.data[CONF_MODEL]]
        for entity_type in device_model.covers:
            sensor_class = ENTITY_CLASS_MAP.get(entity_type)
            if sensor_class:
                subentry_entities.append(sensor_class(config_entry, subentry))
        async_add_entities(subentry_entities, config_subentry_id=subentry_id)
