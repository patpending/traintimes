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
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance
            api: Darwin API client
            station_crs: Station CRS code
            num_departures: Number of departures to fetch
            destination_crs: Optional destination filter
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

    async def _async_update_data(self) -> list[TrainService]:
        """Fetch data from the Darwin API."""
        try:
            services = await self.api.async_get_departure_board(
                station_crs=self.station_crs,
                num_rows=self.num_departures,
                destination_crs=self.destination_crs,
            )
            _LOGGER.debug(
                "Fetched %d departures from %s",
                len(services),
                self.station_crs
            )
            return services
        except DarwinApiError as err:
            _LOGGER.error("Error fetching departure data: %s", err)
            raise UpdateFailed(f"Error communicating with Darwin API: {err}") from err
        except Exception as err:
            _LOGGER.exception("Unexpected error fetching departure data")
            raise UpdateFailed(f"Unexpected error: {err}") from err
