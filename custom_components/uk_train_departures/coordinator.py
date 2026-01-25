"""Data update coordinator for UK Train Departures."""

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import DarwinApi, DarwinApiError, TrainService
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class TrainDeparturesCoordinator(DataUpdateCoordinator[list[TrainService]]):
    """Coordinator to manage fetching train departure data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: DarwinApi,
        station_crs: str,
        num_departures: int = 3,
        destination_crs: str | None = None,
        watched_trains: list[dict] | None = None,
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance
            api: Darwin API client
            station_crs: Station CRS code
            num_departures: Number of departures to fetch
            destination_crs: Optional destination filter
            watched_trains: List of watched train configs
        """
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{station_crs}",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.api = api
        self.station_crs = station_crs
        self.num_departures = num_departures
        self.destination_crs = destination_crs
        self.watched_trains = watched_trains or []
        self.watched_train_data: dict[str, TrainService | None] = {}

    async def _async_update_data(self) -> list[TrainService]:
        """Fetch data from the Darwin API."""
        try:
            # Fetch more rows if we have watched trains to find
            rows_to_fetch = max(self.num_departures, 20) if self.watched_trains else self.num_departures

            services = await self.api.async_get_departure_board(
                station_crs=self.station_crs,
                num_rows=rows_to_fetch,
                destination_crs=self.destination_crs,
            )

            # Find watched trains
            self.watched_train_data = {}
            for watched in self.watched_trains:
                scheduled_time = watched.get("scheduled_time", "")
                dest_filter = watched.get("destination", "")

                found_train = None
                for service in services:
                    if service.scheduled_time == scheduled_time:
                        # Check destination filter if specified
                        if dest_filter:
                            dest_match = (
                                dest_filter.upper() in service.destination.upper() or
                                service.destination_crs.upper() == dest_filter.upper()
                            )
                            if not dest_match:
                                continue
                        found_train = service
                        break

                self.watched_train_data[scheduled_time] = found_train

            _LOGGER.debug(
                "Fetched %d departures from %s, found %d watched trains",
                len(services),
                self.station_crs,
                sum(1 for v in self.watched_train_data.values() if v is not None)
            )

            # Return only the requested number of departures
            return services[:self.num_departures]
        except DarwinApiError as err:
            _LOGGER.error("Error fetching departure data: %s", err)
            raise UpdateFailed(f"Error communicating with Darwin API: {err}") from err
        except Exception as err:
            _LOGGER.exception("Unexpected error fetching departure data")
            raise UpdateFailed(f"Unexpected error: {err}") from err
