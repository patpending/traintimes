"""Sensor platform for UK Train Departures."""

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_NUM_DEPARTURES,
    CONF_STATION_CRS,
    CONF_WATCHED_TRAIN_1_TIME,
    CONF_WATCHED_TRAIN_1_DEST,
    CONF_WATCHED_TRAIN_2_TIME,
    CONF_WATCHED_TRAIN_2_DEST,
    CONF_WATCHED_TRAIN_3_TIME,
    CONF_WATCHED_TRAIN_3_DEST,
    DEFAULT_NUM_DEPARTURES,
    DOMAIN,
    STATION_CODES,
    STATUS_CANCELLED,
    STATUS_DELAYED,
    STATUS_ON_TIME,
)
from .coordinator import TrainDeparturesCoordinator


def calculate_delay_minutes(scheduled: str, expected: str) -> int:
    """Calculate delay in minutes between scheduled and expected times."""
    if not scheduled or not expected:
        return 0
    if expected in ("On time", "Delayed", "Cancelled"):
        return 0 if expected == "On time" else -1  # -1 for unknown delay

    try:
        # Parse times (HH:MM format)
        sch_h, sch_m = map(int, scheduled.split(":"))
        exp_h, exp_m = map(int, expected.split(":"))

        sch_mins = sch_h * 60 + sch_m
        exp_mins = exp_h * 60 + exp_m

        # Handle day wraparound
        diff = exp_mins - sch_mins
        if diff < -720:  # More than 12 hours negative = next day
            diff += 1440

        return max(0, diff)
    except (ValueError, AttributeError):
        return 0

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up UK Train Departures sensors from a config entry."""
    coordinator: TrainDeparturesCoordinator = hass.data[DOMAIN][entry.entry_id]
    station_crs = entry.data[CONF_STATION_CRS]
    num_departures = entry.data.get(CONF_NUM_DEPARTURES, DEFAULT_NUM_DEPARTURES)

    # Create a sensor for each departure slot
    sensors = [
        TrainDepartureSensor(
            coordinator=coordinator,
            entry=entry,
            station_crs=station_crs,
            departure_index=i,
        )
        for i in range(num_departures)
    ]

    # Add a summary sensor
    sensors.append(
        TrainDeparturesSummarySensor(
            coordinator=coordinator,
            entry=entry,
            station_crs=station_crs,
        )
    )

    # Add watched train sensors
    for i, (time_key, dest_key) in enumerate([
        (CONF_WATCHED_TRAIN_1_TIME, CONF_WATCHED_TRAIN_1_DEST),
        (CONF_WATCHED_TRAIN_2_TIME, CONF_WATCHED_TRAIN_2_DEST),
        (CONF_WATCHED_TRAIN_3_TIME, CONF_WATCHED_TRAIN_3_DEST),
    ], 1):
        scheduled_time = entry.data.get(time_key, "")
        if scheduled_time:
            destination = entry.data.get(dest_key, "")
            sensors.append(
                WatchedTrainSensor(
                    coordinator=coordinator,
                    entry=entry,
                    station_crs=station_crs,
                    scheduled_time=scheduled_time,
                    destination_filter=destination,
                    train_number=i,
                )
            )

    async_add_entities(sensors)


class TrainDepartureSensor(CoordinatorEntity[TrainDeparturesCoordinator], SensorEntity):
    """Sensor for a single train departure."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TrainDeparturesCoordinator,
        entry: ConfigEntry,
        station_crs: str,
        departure_index: int,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._station_crs = station_crs
        self._departure_index = departure_index
        self._entry = entry

        station_name = STATION_CODES.get(station_crs.upper(), station_crs)
        self._attr_unique_id = f"{entry.entry_id}_departure_{departure_index + 1}"
        self._attr_name = f"Departure {departure_index + 1}"
        self._attr_icon = "mdi:train"

    @property
    def native_value(self) -> str | None:
        """Return the destination of this departure."""
        if not self.coordinator.data:
            return "No train"
        if self._departure_index >= len(self.coordinator.data):
            return "No train"
        service = self.coordinator.data[self._departure_index]
        return service.destination

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes for the sensor."""
        no_service_attrs = {
            "summary": "No train",
            "scheduled_time": None,
            "expected_time": None,
            "platform": None,
            "operator": None,
            "operator_code": None,
            "status": "no_service",
            "is_delayed": False,
            "is_cancelled": False,
            "delay_minutes": 0,
            "cancel_reason": None,
            "delay_reason": None,
            "destination_crs": None,
            "calling_points": [],
            "service_id": None,
            "station_crs": self._station_crs,
        }
        if not self.coordinator.data:
            return no_service_attrs
        if self._departure_index >= len(self.coordinator.data):
            return no_service_attrs

        service = self.coordinator.data[self._departure_index]

        # Format calling points
        calling_points = [
            {
                "station": cp.station_name,
                "crs": cp.crs,
                "scheduled": cp.scheduled_time,
                "expected": cp.expected_time,
            }
            for cp in service.calling_points
        ]

        delay_mins = calculate_delay_minutes(service.scheduled_time, service.expected_time)
        is_delayed = service.status == STATUS_DELAYED or delay_mins > 0

        # Build summary string
        if service.is_cancelled:
            summary = f"{service.scheduled_time} to {service.destination} - CANCELLED"
        elif service.expected_time == "On time":
            summary = f"{service.scheduled_time} to {service.destination} - On time"
        elif delay_mins > 0:
            summary = f"{service.scheduled_time} to {service.destination} - Exp {service.expected_time} ({delay_mins} min late)"
        else:
            summary = f"{service.scheduled_time} to {service.destination} - Exp {service.expected_time}"

        return {
            "summary": summary,
            "scheduled_time": service.scheduled_time,
            "expected_time": service.expected_time,
            "platform": service.platform,
            "operator": service.operator,
            "operator_code": service.operator_code,
            "status": service.status,
            "is_delayed": is_delayed,
            "is_cancelled": service.is_cancelled,
            "delay_minutes": delay_mins,
            "cancel_reason": service.cancel_reason,
            "delay_reason": service.delay_reason,
            "destination_crs": service.destination_crs,
            "calling_points": calling_points,
            "service_id": service.service_id,
            "station_crs": self._station_crs,
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not self.coordinator.last_update_success:
            return False
        if not self.coordinator.data:
            return True  # Available but no trains
        return True


class TrainDeparturesSummarySensor(
    CoordinatorEntity[TrainDeparturesCoordinator], SensorEntity
):
    """Summary sensor for all departures from a station."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TrainDeparturesCoordinator,
        entry: ConfigEntry,
        station_crs: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._station_crs = station_crs
        self._entry = entry

        station_name = STATION_CODES.get(station_crs.upper(), station_crs)
        self._attr_unique_id = f"{entry.entry_id}_summary"
        self._attr_name = f"Departures"
        self._attr_icon = "mdi:train-variant"

    @property
    def native_value(self) -> int:
        """Return the number of departures."""
        if not self.coordinator.data:
            return 0
        return len(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return all departures as attributes."""
        if not self.coordinator.data:
            return {"departures": [], "station_crs": self._station_crs}

        departures = []
        for service in self.coordinator.data:
            calling_points = [
                {
                    "station": cp.station_name,
                    "crs": cp.crs,
                    "scheduled": cp.scheduled_time,
                    "expected": cp.expected_time,
                }
                for cp in service.calling_points
            ]

            departures.append({
                "destination": service.destination,
                "destination_crs": service.destination_crs,
                "scheduled_time": service.scheduled_time,
                "expected_time": service.expected_time,
                "platform": service.platform,
                "operator": service.operator,
                "status": service.status,
                "is_cancelled": service.is_cancelled,
                "cancel_reason": service.cancel_reason,
                "delay_reason": service.delay_reason,
                "calling_points": calling_points,
            })

        # Count statuses
        on_time = sum(1 for d in departures if d["status"] == STATUS_ON_TIME)
        delayed = sum(1 for d in departures if d["status"] == STATUS_DELAYED)
        cancelled = sum(1 for d in departures if d["status"] == STATUS_CANCELLED)

        return {
            "departures": departures,
            "station_crs": self._station_crs,
            "station_name": STATION_CODES.get(self._station_crs.upper(), self._station_crs),
            "on_time_count": on_time,
            "delayed_count": delayed,
            "cancelled_count": cancelled,
        }


class WatchedTrainSensor(CoordinatorEntity[TrainDeparturesCoordinator], SensorEntity):
    """Sensor for a watched/tracked train by scheduled time."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TrainDeparturesCoordinator,
        entry: ConfigEntry,
        station_crs: str,
        scheduled_time: str,
        destination_filter: str,
        train_number: int,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._station_crs = station_crs
        self._scheduled_time = scheduled_time
        self._destination_filter = destination_filter
        self._train_number = train_number
        self._entry = entry

        # Create friendly name
        time_slug = scheduled_time.replace(":", "")
        self._attr_unique_id = f"{entry.entry_id}_watched_{time_slug}"
        self._attr_name = f"{scheduled_time} Train"
        self._attr_icon = "mdi:train-car"

    def _get_watched_train(self):
        """Get the watched train service from coordinator data."""
        return self.coordinator.watched_train_data.get(self._scheduled_time)

    @property
    def native_value(self) -> str | None:
        """Return the status of this watched train."""
        service = self._get_watched_train()
        if not service:
            return "Not found"

        if service.is_cancelled:
            return "Cancelled"

        delay_mins = calculate_delay_minutes(service.scheduled_time, service.expected_time)
        if delay_mins > 0:
            return f"Delayed {delay_mins} min"
        elif service.status == STATUS_DELAYED:
            return "Delayed"

        return "On time"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes for the sensor."""
        service = self._get_watched_train()

        base_attrs = {
            "scheduled_time": self._scheduled_time,
            "destination_filter": self._destination_filter or "Any",
            "found": service is not None,
            "station_crs": self._station_crs,
        }

        if not service:
            return {
                **base_attrs,
                "summary": f"{self._scheduled_time} - Train not found",
                "expected_time": None,
                "platform": None,
                "destination": None,
                "operator": None,
                "status": "not_found",
                "is_delayed": False,
                "is_cancelled": False,
                "delay_minutes": 0,
            }

        delay_mins = calculate_delay_minutes(service.scheduled_time, service.expected_time)
        is_delayed = service.status == STATUS_DELAYED or delay_mins > 0

        # Build summary string
        if service.is_cancelled:
            summary = f"{service.scheduled_time} to {service.destination} - CANCELLED"
        elif service.expected_time == "On time":
            summary = f"{service.scheduled_time} to {service.destination} - On time"
        elif delay_mins > 0:
            summary = f"{service.scheduled_time} to {service.destination} - Exp {service.expected_time} ({delay_mins} min late)"
        else:
            summary = f"{service.scheduled_time} to {service.destination} - Exp {service.expected_time}"

        # Format calling points
        calling_points = [
            {
                "station": cp.station_name,
                "crs": cp.crs,
                "scheduled": cp.scheduled_time,
                "expected": cp.expected_time,
            }
            for cp in service.calling_points
        ]

        return {
            **base_attrs,
            "summary": summary,
            "expected_time": service.expected_time,
            "platform": service.platform,
            "destination": service.destination,
            "destination_crs": service.destination_crs,
            "operator": service.operator,
            "status": service.status,
            "is_delayed": is_delayed,
            "is_cancelled": service.is_cancelled,
            "delay_minutes": delay_mins,
            "delay_reason": service.delay_reason,
            "cancel_reason": service.cancel_reason,
            "calling_points": calling_points,
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success
