"""UK Train Departures integration for Home Assistant."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .api import DarwinApi
from .const import (
    CONF_API_TOKEN,
    CONF_DESTINATION_CRS,
    CONF_NUM_DEPARTURES,
    CONF_STATION_CRS,
    DEFAULT_NUM_DEPARTURES,
    DOMAIN,
)
from .coordinator import TrainDeparturesCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up UK Train Departures from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Create API client
    api = DarwinApi(entry.data[CONF_API_TOKEN])

    # Create coordinator
    coordinator = TrainDeparturesCoordinator(
        hass=hass,
        api=api,
        station_crs=entry.data[CONF_STATION_CRS],
        num_departures=entry.data.get(CONF_NUM_DEPARTURES, DEFAULT_NUM_DEPARTURES),
        destination_crs=entry.data.get(CONF_DESTINATION_CRS) or None,
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
