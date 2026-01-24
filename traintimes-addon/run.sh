#!/bin/sh
# Read configuration from Home Assistant Add-on options

CONFIG_PATH=/data/options.json

# Parse options using Python (jq not available)
export DARWIN_API_TOKEN=$(python3 -c "import json; print(json.load(open('$CONFIG_PATH'))['api_token'])")
export STATION_CRS=$(python3 -c "import json; print(json.load(open('$CONFIG_PATH'))['station_crs'])")
export DESTINATION_CRS=$(python3 -c "import json; print(json.load(open('$CONFIG_PATH')).get('destination_filter', ''))")
export NUM_DEPARTURES=$(python3 -c "import json; print(json.load(open('$CONFIG_PATH'))['num_departures'])")
export LOG_LEVEL=$(python3 -c "import json; print(json.load(open('$CONFIG_PATH'))['log_level'])")

# Set Flask to run on the ingress port
export PORT=5050

echo "Starting UK Train Departures Add-on"
echo "Station: ${STATION_CRS}"
echo "Destination Filter: ${DESTINATION_CRS:-none}"
echo "Number of Departures: ${NUM_DEPARTURES}"

# Start the Flask application
cd /app
exec python3 app.py
