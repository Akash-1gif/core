"""Support for showing the time and places in multiple time zones."""
from __future__ import annotations

from datetime import tzinfo
from typing import Optional

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import CONF_NAME, CONF_TIME_ZONE
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
import homeassistant.util.dt as dt_util
from homeassistant.helpers.event import async_track_state_change

import pytz
from datetime import datetime

from pytz import timezone as tz
import smtplib
from email.mime.text import MIMEText

CONF_SECOND_TIME_ZONE = "second_time_zone"
CONF_FIRST_CITY_NAME = "first_city_name"
CONF_SECOND_CITY_NAME = "second_city_name"
CONF_TIME_FORMAT = "time_format"
CONF_SENDER = "sender"
CONF_RECEIVER = "receiver"
CONF_PASSWORD = "password"

DEFAULT_NAME = "Worldclock Sensor"
DEFAULT_TIME_STR_FORMAT = "%H:%M"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_TIME_ZONE): cv.time_zone,
        vol.Required(CONF_SECOND_TIME_ZONE): cv.time_zone,
        vol.Optional(CONF_FIRST_CITY_NAME): cv.string,
        vol.Optional(CONF_SECOND_CITY_NAME): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_TIME_FORMAT, default=DEFAULT_TIME_STR_FORMAT): cv.string,
        vol.Optional(CONF_SENDER): cv.string,
        vol.Optional(CONF_RECEIVER): cv.string,
        vol.Optional(CONF_PASSWORD): cv.string,
    }
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the World clock sensor."""
    time_zone = dt_util.get_time_zone(config[CONF_TIME_ZONE])

    # Retrieve the selected time from input_datetime.custom_time_secondary_zone
    selected_time_entity_id = "input_datetime.custom_time_secondary_zone"
    selected_time_state = hass.states.get(selected_time_entity_id)
    selected_time = selected_time_state.state

    # Extract hours and minutes from the selected time
    time_string = selected_time
    time_list = [int(x) for x in time_string.split(":")]
    h1 = time_list[0]
    m1 = time_list[1]

    # Retrieve email notification configuration
    sender = config.get(CONF_SENDER)
    receiver = config.get(CONF_RECEIVER)
    password = config.get(CONF_PASSWORD)

    # Initial setup
    await update_sensor(
        hass, time_zone, config, async_add_entities, h1, m1, sender, receiver, password
    )

    # Register callback for future updates
    async_track_state_change(
        hass,
        selected_time_entity_id,
        lambda entity_id, old_state, new_state: hass.async_create_task(
            update_sensor(
                hass,
                time_zone,
                config,
                async_add_entities,
                h1,
                m1,
                sender,
                receiver,
                password,
            )
        ),
    )


async def update_sensor(
    hass: HomeAssistant,
    time_zone,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    h1: int,
    m1: int,
    sender: str,
    receiver: str,
    password: str,
) -> None:
    """Update the World clock sensor."""
    selected_secondary_time_zone = hass.states.get(
        "input_select.world_clock_secondary_time_zone"
    ).state
    second_time_zone = dt_util.get_time_zone(selected_secondary_time_zone)

    first_city_name = config.get(CONF_FIRST_CITY_NAME)
    second_city_name = config.get(CONF_SECOND_CITY_NAME)

    async_add_entities(
        [
            WorldClockSensor(
                time_zone,
                second_time_zone,
                first_city_name,
                second_city_name,
                config[CONF_NAME],
                config[CONF_TIME_FORMAT],
                h1,
                m1,
                sender,
                receiver,
                password,
            )
        ],
        True,
    )


class WorldClockSensor(SensorEntity):
    """Representation of a World clock sensor."""

    _attr_icon = "mdi:clock"

    def __init__(
        self,
        time_zone: tzinfo | None,
        second_time_zone: tzinfo | None,
        first_city_name: str | None,
        second_city_name: str | None,
        name: str,
        time_format: str,
        h1: int,
        m1: int,
        sender: str,
        receiver: str,
        password: str,
    ) -> None:
        """Initialize the sensor."""
        self._attr_name = name
        self._time_zone = time_zone
        self._second_time_zone = second_time_zone
        self._first_city_name = first_city_name
        self._second_city_name = second_city_name
        self._time_format = time_format
        self._h1 = h1
        self._m1 = m1
        self._sender = sender
        self._receiver = receiver
        self._password = password

    async def async_update(self) -> None:
        """Get the time and update the states."""
        current_time = dt_util.now(time_zone=self._time_zone)
        second_time = dt_util.now(time_zone=self._second_time_zone)
        first_city_display = (
            f"{self._first_city_name}: {current_time.strftime(self._time_format)}"
            if self._first_city_name
            else current_time.strftime(self._time_format)
        )
        second_city_display = (
            f"{self._second_city_name}: {second_time.strftime(self._time_format)}"
            if self._second_city_name
            else second_time.strftime(self._time_format)
        )

        self._attr_native_value = f"{first_city_display} / {second_city_display}"

        # Access the stored values of hours and minutes
        h1 = self._h1
        m1 = self._m1
        secondary_time_zone = self._second_time_zone

        off_shore_time = second_time.time()
        hours = off_shore_time.hour
        minutes = off_shore_time.minute

        if (hours == h1) and (minutes == m1):
            # retrieving credentials:
            sender = self._sender
            receiver = self._receiver
            password = self._password
            # Your email notification logic goes here
            sub = "Notification from homeassistant"
            msg = f"a reminder from homeassistant to check your work, ir is {h1}:{m1} at {secondary_time_zone}"
            try:
                server = smtplib.SMTP("smtp.outlook.com", 587)
                server.starttls()
                server.login(sender, password)
                msg = MIMEText(msg)
                msg["Subject"] = sub
                msg["From"] = sender
                msg["To"] = receiver
                msg.set_param("importance", "high value")
                server.sendmail(sender, receiver, msg.as_string())
                print(f"email to {receiver} has been sent")
            except:
                print("there is some problem in sending emails. Please try again")
