import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
from pytz import timezone as tz

from homeassistant.core import HomeAssistant
from homeassistant.util.dt import now
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity_platform import EntityPlatform
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from ..worldclock.sensor import WorldClockSensor, async_setup_platform, update_sensor


class TestWorldClockSensor(unittest.TestCase):
    def setUp(self):
        self.hass = MagicMock(spec=HomeAssistant)
        self.config = {
            "time_zone": "America/New_York",
            "second_time_zone": "Europe/London",
            "first_city_name": "New York",
            "second_city_name": "London",
            "name": "World Clock",
            "time_format": "%H:%M",
            "sender": "test@example.com",
            "receiver": "test@example.com",
            "password": "password",
        }
        self.add_entities = MagicMock()
        self.h1 = 10
        self.m1 = 30

    @patch(
        "homeassistant.components.worldclock.sensor.dt_util.now",
        return_value=datetime(2022, 1, 1, 10, 30, tzinfo=tz("America/New_York")),
    )
    @patch(
        "homeassistant.components.worldclock.sensor.dt_util.get_time_zone",
        return_value=tz("America/New_York"),
    )
    @patch(
        "homeassistant.components.worldclock.sensor.async_track_state_change",
        return_value=None,
    )
    @patch(
        "homeassistant.components.worldclock.sensor.hass.states.get",
        return_value=MagicMock(state="10:30"),
    )
    async def test_async_setup_platform(
        self,
        mock_hass_states_get,
        mock_async_track_state_change,
        mock_get_time_zone,
        mock_now,
    ):
        await async_setup_platform(
            self.hass, self.config, self.add_entities, discovery_info=None
        )
        self.add_entities.assert_called_once()

    @patch(
        "homeassistant.components.worldclock.sensor.dt_util.now",
        return_value=datetime(2022, 1, 1, 10, 30, tzinfo=tz("America/New_York")),
    )
    @patch(
        "homeassistant.components.worldclock.sensor.dt_util.get_time_zone",
        return_value=tz("America/New_York"),
    )
    @patch(
        "homeassistant.components.worldclock.sensor.async_track_state_change",
        return_value=None,
    )
    @patch(
        "homeassistant.components.worldclock.sensor.hass.states.get",
        return_value=MagicMock(state="10:30"),
    )
    async def test_update_sensor(
        self,
        mock_hass_states_get,
        mock_async_track_state_change,
        mock_get_time_zone,
        mock_now,
    ):
        await update_sensor(
            self.hass,
            tz("America/New_York"),
            self.config,
            self.add_entities,
            self.h1,
            self.m1,
            self.config["sender"],
            self.config["receiver"],
            self.config["password"],
        )
        self.add_entities.assert_called_once()

    @patch(
        "homeassistant.components.worldclock.sensor.dt_util.now",
        return_value=datetime(2022, 1, 1, 10, 30, tzinfo=tz("America/New_York")),
    )
    @patch(
        "homeassistant.components.worldclock.sensor.dt_util.get_time_zone",
        return_value=tz("America/New_York"),
    )
    def test_world_clock_sensor(self, mock_get_time_zone, mock_now):
        sensor = WorldClockSensor(
            tz("America/New_York"),
            tz("Europe/London"),
            "New York",
            "London",
            "World Clock",
            "%H:%M",
            self.h1,
            self.m1,
            self.config["sender"],
            self.config["receiver"],
            self.config["password"],
        )
        sensor.async_update()


if __name__ == "__main__":
    unittest.main()
