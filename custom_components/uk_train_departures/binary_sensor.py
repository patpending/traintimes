"""Binary sensor platform for UK Train Departures."""

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_STATION_CRS,
    CONF_WATCHED_TRAIN_1_TIME,
    CONF_WATCHED_TRAIN_1_DEST,
    CONF_WATCHED_TRAIN_2_TIME,
    CONF_WATCHED_TRAIN_2_DEST,
    CONF_WATCHED_TRAIN_3_TIME,
    CONF_WATCHED_TRAIN_3_DEST,
    DOMAIN,
    STATUS_DELAYED,
)
from .coordinator import TrainDeparturesCoordinator
from .sensor import calculate_delay_minutes

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up UK Train Departures binary sensors from a config entry."""
    coordinator: TrainDeparturesCoordinator = hass.data[DOMAIN][entry.entry_id]
    station_crs = entry.data[CONF_STATION_CRS]

    entities = []

    # Add binary sensors for each watched train
    for i, (time_key, dest_key) in enumerate([
        (CONF_WATCHED_TRAIN_1_TIME, CONF_WATCHED_TRAIN_1_DEST),
        (CONF_WATCHED_TRAIN_2_TIME, CONF_WATCHED_TRAIN_2_DEST),
        (CONF_WATCHED_TRAIN_3_TIME, CONF_WATCHED_TRAIN_3_DEST),
    ], 1):
        scheduled_time = entry.data.get(time_key, "")
        if scheduled_time:
            destination = entry.data.get(dest_key, "")
            # Delayed binary sensor
            entities.append(
                WatchedTrainDelayedBinarySensor(
                    coordinator=coordinator,
                    entry=entry,
                    station_crs=station_crs,
                    scheduled_time=scheduled_time,
                    destination_filter=destination,
                    train_number=i,
                )
            )
            # Cancelled binary sensor
            entities.append(
                WatchedTrainCancelledBinarySensor(
                    coordinator=coordinator,
                    entry=entry,
                    station_crs=station_crs,
                    scheduled_time=scheduled_time,
                    destination_filter=destination,
                    train_number=i,
                )
            )

    async_add_entities(entities)


class WatchedTrainDelayedBinarySensor(
    CoordinatorEntity[TrainDeparturesCoordinator], BinarySensorEntity
):
    """Binary sensor indicating if a watched train is delayed."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(
        self,
        coordinator: TrainDeparturesCoordinator,
        entry: ConfigEntry,
        station_crs: str,
        scheduled_time: str,
        destination_filter: str,
        train_number: int,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._station_crs = station_crs
        self._scheduled_time = scheduled_time
        self._destination_filter = destination_filter
        self._train_number = train_number
        self._entry = entry

        time_slug = scheduled_time.replace(":", "")
        self._attr_unique_id = f"{entry.entry_id}_watched_{time_slug}_delayed"
        self._attr_name = f"{scheduled_time} Train Delayed"
        self._attr_icon = "mdi:train-car"

    def _get_watched_train(self):
        """Get the watched train service from coordinator data."""
        return self.coordinator.watched_train_data.get(self._scheduled_time)

    @property
    def is_on(self) -> bool:
        """Return true if the train is delayed."""
        service = self._get_watched_train()
        if not service:
            return False

        if service.is_cancelled:
            return False  # Cancelled is separate

        delay_mins = calculate_delay_minutes(service.scheduled_time, service.expected_time)
        return service.status == STATUS_DELAYED or delay_mins > 0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        service = self._get_watched_train()
        if not service:
            return {
                "scheduled_time": self._scheduled_time,
                "delay_minutes": 0,
                "found": False,
            }

        delay_mins = calculate_delay_minutes(service.scheduled_time, service.expected_time)
        return {
            "scheduled_time": self._scheduled_time,
            "expected_time": service.expected_time,
            "delay_minutes": delay_mins,
            "delay_reason": service.delay_reason,
            "destination": service.destination,
            "found": True,
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success


class WatchedTrainCancelledBinarySensor(
    CoordinatorEntity[TrainDeparturesCoordinator], BinarySensorEntity
):
    """Binary sensor indicating if a watched train is cancelled."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(
        self,
        coordinator: TrainDeparturesCoordinator,
        entry: ConfigEntry,
        station_crs: str,
        scheduled_time: str,
        destination_filter: str,
        train_number: int,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._station_crs = station_crs
        self._scheduled_time = scheduled_time
        self._destination_filter = destination_filter
        self._train_number = train_number
        self._entry = entry

        time_slug = scheduled_time.replace(":", "")
        self._attr_unique_id = f"{entry.entry_id}_watched_{time_slug}_cancelled"
        self._attr_name = f"{scheduled_time} Train Cancelled"
        self._attr_icon = "mdi:train-car"

    def _get_watched_train(self):
        """Get the watched train service from coordinator data."""
        return self.coordinator.watched_train_data.get(self._scheduled_time)

    @property
    def is_on(self) -> bool:
        """Return true if the train is cancelled."""
        service = self._get_watched_train()
        if not service:
            return False
        return service.is_cancelled

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        service = self._get_watched_train()
        if not service:
            return {
                "scheduled_time": self._scheduled_time,
                "found": False,
            }

        return {
            "scheduled_time": self._scheduled_time,
            "cancel_reason": service.cancel_reason,
            "destination": service.destination,
            "found": True,
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success
