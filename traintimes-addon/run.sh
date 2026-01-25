#!/bin/sh
# UK Train Departures Add-on startup script

CONFIG_PATH=/data/options.json

echo "=============================================="
echo "   UK Train Departures Add-on Starting"
echo "=============================================="

# Install custom integration to Home Assistant
echo "Installing UK Train Departures integration..."
if [ -d "/config" ]; then
    mkdir -p /config/custom_components
    cp -r /app/custom_components/uk_train_departures /config/custom_components/
    echo "Integration installed to /config/custom_components/uk_train_departures"
    echo "NOTE: Restart Home Assistant to load the integration, then add it via Settings > Integrations"
else
    echo "WARNING: /config not mounted, integration not installed"
fi

# Parse options using Python (jq not available)
export DARWIN_API_TOKEN=$(python3 -c "import json; print(json.load(open('$CONFIG_PATH'))['api_token'])")
export STATION_CRS=$(python3 -c "import json; print(json.load(open('$CONFIG_PATH'))['station_crs'])")
export DESTINATION_CRS=$(python3 -c "import json; print(json.load(open('$CONFIG_PATH')).get('destination_filter', ''))")
export NUM_DEPARTURES=$(python3 -c "import json; print(json.load(open('$CONFIG_PATH'))['num_departures'])")
export LOG_LEVEL=$(python3 -c "import json; print(json.load(open('$CONFIG_PATH'))['log_level'])")

# Set Flask to run on the ingress port
export PORT=5050

echo "=============================================="
echo "Web UI Configuration:"
echo "  Station: ${STATION_CRS}"
echo "  Destination Filter: ${DESTINATION_CRS:-none}"
echo "  Number of Departures: ${NUM_DEPARTURES}"
echo "=============================================="

# Start the Flask application
cd /app
exec python3 app.py
