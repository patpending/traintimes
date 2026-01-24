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
    DEFAULT_NUM_DEPARTURES,
    DOMAIN,
    STATION_CODES,
    STATUS_CANCELLED,
    STATUS_DELAYED,
    STATUS_ON_TIME,
)
from .coordinator import TrainDeparturesCoordinator

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
            return None
        if self._departure_index >= len(self.coordinator.data):
            return None
        service = self.coordinator.data[self._departure_index]
        return service.destination

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes for the sensor."""
        if not self.coordinator.data:
            return {}
        if self._departure_index >= len(self.coordinator.data):
            return {"status": "no_service"}

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

        return {
            "scheduled_time": service.scheduled_time,
            "expected_time": service.expected_time,
            "platform": service.platform,
            "operator": service.operator,
            "operator_code": service.operator_code,
            "status": service.status,
            "is_cancelled": service.is_cancelled,
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
