#!/usr/bin/with-contenv bashio
# shellcheck shell=bash

# Read configuration from Home Assistant Add-on options
API_TOKEN=$(bashio::config 'api_token')
STATION_CRS=$(bashio::config 'station_crs')
DESTINATION_FILTER=$(bashio::config 'destination_filter')
NUM_DEPARTURES=$(bashio::config 'num_departures')
LOG_LEVEL=$(bashio::config 'log_level')

# Export environment variables for the Flask app
export DARWIN_API_TOKEN="${API_TOKEN}"
export STATION_CRS="${STATION_CRS}"
export DESTINATION_CRS="${DESTINATION_FILTER}"
export NUM_DEPARTURES="${NUM_DEPARTURES}"
export LOG_LEVEL="${LOG_LEVEL}"

# Set Flask to run on the ingress port
export PORT=5050

bashio::log.info "Starting UK Train Departures Add-on"
bashio::log.info "Station: ${STATION_CRS}"
bashio::log.info "Destination Filter: ${DESTINATION_FILTER:-none}"
bashio::log.info "Number of Departures: ${NUM_DEPARTURES}"

# Start the Flask application
cd /app
exec python3 app.py
