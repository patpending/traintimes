"""Config flow for UK Train Departures integration."""

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .api import DarwinApi, DarwinApiError
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
    STATION_CODES,
)

_LOGGER = logging.getLogger(__name__)


class UKTrainDeparturesConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for UK Train Departures."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._user_input: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate the API token
            api = DarwinApi(user_input[CONF_API_TOKEN])

            try:
                # Test the connection with the specified station (use async method directly)
                await api.async_get_departure_board(
                    station_crs=user_input[CONF_STATION_CRS].upper(),
                    num_rows=1,
                )
            except DarwinApiError as err:
                _LOGGER.error("Failed to connect to Darwin API: %s", err)
                if "Invalid token" in str(err) or "401" in str(err) or "authentication" in str(err).lower():
                    errors["base"] = "invalid_auth"
                else:
                    errors["base"] = "cannot_connect"
            except Exception as err:
                _LOGGER.exception("Unexpected error during config flow: %s", err)
                errors["base"] = "unknown"
            else:
                station_crs = user_input[CONF_STATION_CRS].upper()

                # Check if already configured for this station
                await self.async_set_unique_id(f"{station_crs}")
                self._abort_if_unique_id_configured()

                # Store data and proceed to watched trains step
                self._user_input = user_input
                return await self.async_step_watched_trains()

        # Build the schema
        data_schema = vol.Schema(
            {
                vol.Required(CONF_API_TOKEN): str,
                vol.Required(CONF_STATION_CRS): str,
                vol.Optional(CONF_DESTINATION_CRS, default=""): str,
                vol.Optional(
                    CONF_NUM_DEPARTURES, default=DEFAULT_NUM_DEPARTURES
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=10)),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "station_codes_url": "https://www.nationalrail.co.uk/stations_destinations/48702.aspx"
            },
        )

    async def async_step_watched_trains(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the watched trains configuration step."""
        if user_input is not None:
            # Merge with previous input
            self._user_input.update(user_input)

            station_crs = self._user_input[CONF_STATION_CRS].upper()
            station_name = STATION_CODES.get(station_crs, station_crs)

            return self.async_create_entry(
                title=f"Departures from {station_name}",
                data=self._user_input,
            )

        # Build schema for watched trains
        data_schema = vol.Schema(
            {
                vol.Optional(CONF_WATCHED_TRAIN_1_TIME, default=""): str,
                vol.Optional(CONF_WATCHED_TRAIN_1_DEST, default=""): str,
                vol.Optional(CONF_WATCHED_TRAIN_2_TIME, default=""): str,
                vol.Optional(CONF_WATCHED_TRAIN_2_DEST, default=""): str,
                vol.Optional(CONF_WATCHED_TRAIN_3_TIME, default=""): str,
                vol.Optional(CONF_WATCHED_TRAIN_3_DEST, default=""): str,
            }
        )

        return self.async_show_form(
            step_id="watched_trains",
            data_schema=data_schema,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return UKTrainDeparturesOptionsFlow(config_entry)


class UKTrainDeparturesOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for UK Train Departures."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_DESTINATION_CRS,
                        default=self.config_entry.data.get(CONF_DESTINATION_CRS, ""),
                    ): str,
                    vol.Optional(
                        CONF_NUM_DEPARTURES,
                        default=self.config_entry.data.get(
                            CONF_NUM_DEPARTURES, DEFAULT_NUM_DEPARTURES
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=10)),
                }
            ),
        )
