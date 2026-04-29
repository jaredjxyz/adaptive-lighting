import datetime as dt
import zoneinfo

import pytest
import voluptuous as vol
from astral import LocationInfo
from astral.location import Location
from custom_components.adaptive_lighting.const import (
    COLOR_TEMP_MODE_DEFAULT,
    COLOR_TEMP_MODE_DUSK_RAMP,
    COLOR_TEMP_MODE_SCHEMA,
    _DOMAIN_SCHEMA,
)
from homeassistant.components.adaptive_lighting.color_and_brightness import (
    SunEvent,
    SunEvents,
    SunLightSettings,
)

# Create a mock astral_location object
location = Location(LocationInfo())

LAT_LONG_TZS = [
    (52.379189, 4.899431, "Europe/Amsterdam"),
    (32.87336, -117.22743, "US/Pacific"),
    (60, 50, "GMT"),
    (60, 50, "UTC"),
]


@pytest.fixture(params=LAT_LONG_TZS)
def tzinfo_and_location(request):
    lat, long, timezone = request.param
    tzinfo = zoneinfo.ZoneInfo(timezone)
    location = Location(
        LocationInfo(
            name="name",
            region="region",
            timezone=timezone,
            latitude=lat,
            longitude=long,
        ),
    )
    return tzinfo, location


def _make_settings(**overrides):
    """Build a SunLightSettings with defaults plus overrides."""
    location = Location(
        LocationInfo(
            name="test",
            region="region",
            timezone="UTC",
            latitude=37.0,
            longitude=-122.0,
        )
    )
    base = dict(
        name="test",
        astral_location=location,
        adapt_until_sleep=False,
        max_brightness=100,
        max_color_temp=6500,
        min_brightness=1,
        min_color_temp=2200,
        sleep_brightness=1,
        sleep_rgb_or_color_temp="color_temp",
        sleep_color_temp=1000,
        sleep_rgb_color=(255, 0, 0),
        sunrise_time=None,
        min_sunrise_time=None,
        max_sunrise_time=None,
        sunset_time=None,
        min_sunset_time=None,
        max_sunset_time=None,
        brightness_mode_time_dark=dt.timedelta(),
        brightness_mode_time_light=dt.timedelta(),
        timezone=zoneinfo.ZoneInfo("UTC"),
    )
    base.update(overrides)
    return SunLightSettings(**base)


def test_replace_time(tzinfo_and_location):
    tzinfo, location = tzinfo_and_location
    sun_events = SunEvents(
        name="test",
        astral_location=location,
        sunrise_time=None,
        min_sunrise_time=None,
        max_sunrise_time=None,
        sunset_time=None,
        min_sunset_time=None,
        max_sunset_time=None,
        timezone=tzinfo,
    )

    new_time = dt.time(5, 30)
    datetime = dt.datetime(2022, 1, 1)
    replaced_time_utc = sun_events._replace_time(datetime.date(), new_time)
    assert replaced_time_utc.astimezone(tzinfo).time() == new_time


def test_sunrise_without_offset(tzinfo_and_location):
    tzinfo, location = tzinfo_and_location

    sun_events = SunEvents(
        name="test",
        astral_location=location,
        sunrise_time=None,
        min_sunrise_time=None,
        max_sunrise_time=None,
        sunset_time=None,
        min_sunset_time=None,
        max_sunset_time=None,
        timezone=tzinfo,
    )
    date = dt.datetime(2022, 1, 1).date()
    result = sun_events.sunrise(date)
    assert result == location.sunrise(date)


def test_sun_position_no_fixed_sunset_and_sunrise(tzinfo_and_location):
    tzinfo, location = tzinfo_and_location
    sun_events = SunEvents(
        name="test",
        astral_location=location,
        sunrise_time=None,
        min_sunrise_time=None,
        max_sunrise_time=None,
        sunset_time=None,
        min_sunset_time=None,
        max_sunset_time=None,
        timezone=tzinfo,
    )
    date = dt.datetime(2022, 1, 1).date()
    sunset = location.sunset(date)
    position = sun_events.sun_position(sunset)
    assert position == 0
    sunrise = location.sunrise(date)
    position = sun_events.sun_position(sunrise)
    assert position == 0
    noon = location.noon(date)
    position = sun_events.sun_position(noon)
    assert position == 1
    midnight = location.midnight(date)
    position = sun_events.sun_position(midnight)
    assert position == -1


def test_sun_position_fixed_sunset_and_sunrise(tzinfo_and_location):
    tzinfo, location = tzinfo_and_location
    sun_events = SunEvents(
        name="test",
        astral_location=location,
        sunrise_time=dt.time(6, 0),
        min_sunrise_time=None,
        max_sunrise_time=None,
        sunset_time=dt.time(18, 0),
        min_sunset_time=None,
        max_sunset_time=None,
        timezone=tzinfo,
    )
    date = dt.datetime(2022, 1, 1).date()
    sunset = sun_events.sunset(date)
    position = sun_events.sun_position(sunset)
    assert position == 0
    sunrise = sun_events.sunrise(date)
    position = sun_events.sun_position(sunrise)
    assert position == 0
    noon, midnight = sun_events.noon_and_midnight(date)
    position = sun_events.sun_position(noon)
    assert position == 1
    position = sun_events.sun_position(midnight)
    assert position == -1


def test_noon_and_midnight(tzinfo_and_location):
    tzinfo, location = tzinfo_and_location
    sun_events = SunEvents(
        name="test",
        astral_location=location,
        sunrise_time=None,
        min_sunrise_time=None,
        max_sunrise_time=None,
        sunset_time=None,
        min_sunset_time=None,
        max_sunset_time=None,
        timezone=tzinfo,
    )
    date = dt.datetime(2022, 1, 1)
    noon, midnight = sun_events.noon_and_midnight(date)
    assert noon == location.noon(date)
    assert midnight == location.midnight(date)


def test_sun_events(tzinfo_and_location):
    tzinfo, location = tzinfo_and_location
    sun_events = SunEvents(
        name="test",
        astral_location=location,
        sunrise_time=None,
        min_sunrise_time=None,
        max_sunrise_time=None,
        sunset_time=None,
        min_sunset_time=None,
        max_sunset_time=None,
        timezone=tzinfo,
    )

    date = dt.datetime(2022, 1, 1)
    events = sun_events.sun_events(date)
    assert len(events) == 4
    assert (SunEvent.SUNRISE, location.sunrise(date).timestamp()) in events


def test_prev_and_next_events(tzinfo_and_location):
    tzinfo, location = tzinfo_and_location
    sun_events = SunEvents(
        name="test",
        astral_location=location,
        sunrise_time=None,
        min_sunrise_time=None,
        max_sunrise_time=None,
        sunset_time=None,
        min_sunset_time=None,
        max_sunset_time=None,
        timezone=tzinfo,
    )
    datetime = dt.datetime(2022, 1, 1, 10, 0)
    after_sunrise = sun_events.sunrise(datetime.date()) + dt.timedelta(hours=1)
    prev_event, next_event = sun_events.prev_and_next_events(after_sunrise)
    assert prev_event[0] == SunEvent.SUNRISE
    assert next_event[0] == SunEvent.NOON


def test_closest_event(tzinfo_and_location):
    tzinfo, location = tzinfo_and_location
    sun_events = SunEvents(
        name="test",
        astral_location=location,
        sunrise_time=None,
        min_sunrise_time=None,
        max_sunrise_time=None,
        sunset_time=None,
        min_sunset_time=None,
        max_sunset_time=None,
        timezone=tzinfo,
    )
    datetime = dt.datetime(2022, 1, 1, 6, 0)
    sunrise = sun_events.sunrise(datetime.date())
    event_name, ts = sun_events.closest_event(sunrise)
    assert event_name == SunEvent.SUNRISE
    assert ts == location.sunrise(sunrise.date()).timestamp()


class TestColorTempModeSchema:
    def test_accepts_string_default(self):
        assert COLOR_TEMP_MODE_SCHEMA("default") == "default"

    def test_accepts_dict_default(self):
        assert COLOR_TEMP_MODE_SCHEMA({"type": "default"}) == {"type": "default"}

    def test_accepts_dusk_ramp_with_horizon(self):
        result = COLOR_TEMP_MODE_SCHEMA(
            {"type": "dusk_ramp", "horizon_color_temp": 2700}
        )
        assert result == {"type": "dusk_ramp", "horizon_color_temp": 2700}

    def test_rejects_dusk_ramp_without_horizon(self):
        with pytest.raises(vol.Invalid):
            COLOR_TEMP_MODE_SCHEMA({"type": "dusk_ramp"})

    def test_rejects_horizon_outside_dusk_ramp(self):
        with pytest.raises(vol.Invalid):
            COLOR_TEMP_MODE_SCHEMA(
                {"type": "default", "horizon_color_temp": 2700}
            )

    def test_rejects_horizon_below_range(self):
        with pytest.raises(vol.Invalid):
            COLOR_TEMP_MODE_SCHEMA(
                {"type": "dusk_ramp", "horizon_color_temp": 999}
            )

    def test_rejects_horizon_above_range(self):
        with pytest.raises(vol.Invalid):
            COLOR_TEMP_MODE_SCHEMA(
                {"type": "dusk_ramp", "horizon_color_temp": 10001}
            )

    def test_rejects_unknown_mode(self):
        with pytest.raises(vol.Invalid):
            COLOR_TEMP_MODE_SCHEMA({"type": "rainbow"})


class TestDomainSchemaColorTempMode:
    def _base(self):
        return {
            "name": "x",
            "lights": [],
        }

    def test_no_mode_set_defaults_to_default_string(self):
        cfg = _DOMAIN_SCHEMA(self._base())
        assert cfg["color_temp_mode"] == "default"

    def test_dusk_ramp_passes_through(self):
        cfg = self._base()
        cfg["color_temp_mode"] = {
            "type": "dusk_ramp",
            "horizon_color_temp": 2700,
        }
        result = _DOMAIN_SCHEMA(cfg)
        assert result["color_temp_mode"]["type"] == "dusk_ramp"
        assert result["color_temp_mode"]["horizon_color_temp"] == 2700


class TestSunLightSettingsColorTempFields:
    def test_default_color_temp_mode(self):
        s = _make_settings()
        assert s.color_temp_mode == "default"
        assert s.horizon_color_temp is None

    def test_dusk_ramp_fields(self):
        s = _make_settings(color_temp_mode="dusk_ramp", horizon_color_temp=2700)
        assert s.color_temp_mode == "dusk_ramp"
        assert s.horizon_color_temp == 2700


class TestColorTempKelvinDefaultUnchanged:
    """Pin upstream behavior: with default mode, color_temp_kelvin returns
    the same values it always has. dt is now passed but unused in default mode."""

    def test_daytime_interpolation(self):
        s = _make_settings(min_color_temp=2200, max_color_temp=6500)
        # sun_position=1 → max
        assert s.color_temp_kelvin(1.0, dt.datetime(2026, 6, 1, 12, tzinfo=dt.UTC)) == 6500
        # sun_position=0 → min
        assert s.color_temp_kelvin(0.0, dt.datetime(2026, 6, 1, 12, tzinfo=dt.UTC)) == 2200
        # sun_position=0.5 → midpoint
        midpoint = 5 * round(((6500 - 2200) * 0.5 + 2200) / 5)
        assert s.color_temp_kelvin(0.5, dt.datetime(2026, 6, 1, 12, tzinfo=dt.UTC)) == midpoint

    def test_night_returns_min_when_not_adapt_until_sleep(self):
        s = _make_settings(min_color_temp=2200, adapt_until_sleep=False)
        assert s.color_temp_kelvin(-0.5, dt.datetime(2026, 6, 1, 12, tzinfo=dt.UTC)) == 2200

    def test_night_interpolates_to_sleep_when_adapt_until_sleep(self):
        s = _make_settings(
            min_color_temp=2200, sleep_color_temp=1000, adapt_until_sleep=True
        )
        # sun_position=-1 → sleep_color_temp
        assert s.color_temp_kelvin(-1.0, dt.datetime(2026, 6, 1, 12, tzinfo=dt.UTC)) == 1000
        # sun_position=0 → min_color_temp
        assert s.color_temp_kelvin(0.0, dt.datetime(2026, 6, 1, 12, tzinfo=dt.UTC)) == 2200


class TestTwilightAnchors:
    def test_returns_four_timestamps_in_order(self):
        s = _make_settings()
        # Pick a date when civil dusk/dawn definitely occur at 37°N.
        sample = dt.datetime(2026, 6, 1, 23, 0, tzinfo=dt.UTC)
        sunset_ts, dusk_ts, dawn_ts, sunrise_ts = s._twilight_anchors(sample)
        assert sunset_ts < dusk_ts < dawn_ts < sunrise_ts

    def test_civil_dusk_is_about_30min_after_sunset_in_summer(self):
        s = _make_settings()
        sample = dt.datetime(2026, 6, 1, 23, 0, tzinfo=dt.UTC)
        sunset_ts, dusk_ts, _, _ = s._twilight_anchors(sample)
        # At 37°N in June, civil twilight ≈ 28-32 min after sunset.
        delta_min = (dusk_ts - sunset_ts) / 60
        assert 20 < delta_min < 45

    def test_picks_correct_night_when_called_before_sunset(self):
        """At 10am UTC, anchors should describe the upcoming night, not last night."""
        s = _make_settings()
        morning = dt.datetime(2026, 6, 1, 10, 0, tzinfo=dt.UTC)
        sunset_ts, dusk_ts, dawn_ts, sunrise_ts = s._twilight_anchors(morning)
        # All anchors should be in the future relative to `morning`.
        assert sunset_ts > morning.timestamp()

    def test_picks_correct_night_when_called_after_midnight(self):
        """At 04:00 UTC after a sunset, anchors should still describe the night surrounding that sunset."""
        s = _make_settings()
        late = dt.datetime(2026, 6, 2, 4, 0, tzinfo=dt.UTC)  # well after midnight UTC
        sunset_ts, _, _, sunrise_ts = s._twilight_anchors(late)
        # The relevant sunset was on 2026-06-01; sunrise on 2026-06-02.
        assert sunset_ts < late.timestamp() < sunrise_ts
