"""UK Train Departures integration for Home Assistant."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import DarwinApi
from .const import (
    CONF_API_TOKEN,
    CONF_DESTINATION_CRS,
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
)
from .coordinator import TrainDeparturesCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up UK Train Departures from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Create API client with HA's shared session
    session = async_get_clientsession(hass)
    api = DarwinApi(entry.data[CONF_API_TOKEN], session=session)

    # Build watched trains list
    watched_trains = []
    for i, (time_key, dest_key) in enumerate([
        (CONF_WATCHED_TRAIN_1_TIME, CONF_WATCHED_TRAIN_1_DEST),
        (CONF_WATCHED_TRAIN_2_TIME, CONF_WATCHED_TRAIN_2_DEST),
        (CONF_WATCHED_TRAIN_3_TIME, CONF_WATCHED_TRAIN_3_DEST),
    ], 1):
        time_val = entry.data.get(time_key, "")
        dest_val = entry.data.get(dest_key, "")
        if time_val:
            watched_trains.append({
                "name": f"Watched Train {i}",
                "scheduled_time": time_val,
                "destination": dest_val or None,
            })

    # Get destination filter
    destination_crs = entry.data.get(CONF_DESTINATION_CRS) or None
    _LOGGER.debug(
        "Setting up integration: station=%s, destination=%s, data=%s",
        entry.data[CONF_STATION_CRS], destination_crs, dict(entry.data)
    )

    # Create coordinator
    coordinator = TrainDeparturesCoordinator(
        hass=hass,
        api=api,
        station_crs=entry.data[CONF_STATION_CRS],
        num_departures=entry.data.get(CONF_NUM_DEPARTURES, DEFAULT_NUM_DEPARTURES),
        destination_crs=destination_crs,
        watched_trains=watched_trains,
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
