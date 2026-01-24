#!/bin/bash
#
# UK Train Departure Board - Startup Script
#
# Starts the standalone Flask web server for the departure board.
# Usage: ./startup.sh [port]
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/.departure-board.pid"
LOG_FILE="$SCRIPT_DIR/departure-board.log"
CONFIG_FILE="$SCRIPT_DIR/config.yaml"
DEFAULT_PORT=5000

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║           UK Train Departure Board - Startup Script            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if already running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Server already running with PID $OLD_PID${NC}"
        echo "   Use ./shutdown.sh to stop it first."
        exit 1
    else
        echo -e "${YELLOW}Cleaning up stale PID file...${NC}"
        rm -f "$PID_FILE"
    fi
fi

# Load configuration from config.yaml if it exists
if [ -f "$CONFIG_FILE" ]; then
    echo -e "${GREEN}✓ Found config.yaml${NC}"
    # Parse YAML (simple grep-based for basic values)
    if command -v python3 &> /dev/null; then
        export DARWIN_API_TOKEN=$(python3 -c "import yaml; print(yaml.safe_load(open('$CONFIG_FILE'))['api_token'])" 2>/dev/null || echo "")
        export STATION_CRS=$(python3 -c "import yaml; print(yaml.safe_load(open('$CONFIG_FILE'))['station_crs'])" 2>/dev/null || echo "PAD")
        export NUM_DEPARTURES=$(python3 -c "import yaml; print(yaml.safe_load(open('$CONFIG_FILE')).get('num_departures', 6))" 2>/dev/null || echo "6")
        export DESTINATION_CRS=$(python3 -c "import yaml; print(yaml.safe_load(open('$CONFIG_FILE')).get('destination_crs', ''))" 2>/dev/null || echo "")
    fi
else
    echo -e "${YELLOW}⚠️  No config.yaml found. Using environment variables.${NC}"
    echo "   Create config.yaml from config.yaml.example"
fi

# Check for API token
if [ -z "$DARWIN_API_TOKEN" ]; then
    echo ""
    echo -e "${RED}✗ ERROR: No API token configured!${NC}"
    echo ""
    echo "  Set DARWIN_API_TOKEN environment variable or create config.yaml"
    echo "  Get your free API token from: https://opendata.nationalrail.co.uk/"
    echo ""
    exit 1
fi

# Get port from argument or default
PORT="${1:-$DEFAULT_PORT}"
export PORT

# Check if port is available
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${RED}✗ ERROR: Port $PORT is already in use${NC}"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "$SCRIPT_DIR/venv" ]; then
    echo -e "${GREEN}✓ Activating virtual environment${NC}"
    source "$SCRIPT_DIR/venv/bin/activate"
elif [ -d "$SCRIPT_DIR/.venv" ]; then
    echo -e "${GREEN}✓ Activating virtual environment${NC}"
    source "$SCRIPT_DIR/.venv/bin/activate"
fi

# Check dependencies
echo "Checking dependencies..."
python3 -c "import flask" 2>/dev/null || {
    echo -e "${RED}✗ Flask not installed. Run: pip install -r requirements.txt${NC}"
    exit 1
}
python3 -c "import zeep" 2>/dev/null || {
    echo -e "${RED}✗ zeep not installed. Run: pip install -r requirements.txt${NC}"
    exit 1
}
echo -e "${GREEN}✓ Dependencies OK${NC}"

# Start the server
echo ""
echo "Starting server on port $PORT..."
cd "$SCRIPT_DIR/standalone"
python3 app.py > "$LOG_FILE" 2>&1 &
SERVER_PID=$!
echo $SERVER_PID > "$PID_FILE"

# Wait a moment and check if it started
sleep 2
if ps -p $SERVER_PID > /dev/null 2>&1; then
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                     Server Started Successfully                 ║${NC}"
    echo -e "${GREEN}╠════════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${GREEN}║  URL:      http://localhost:$PORT                              ${NC}"
    echo -e "${GREEN}║  PID:      $SERVER_PID                                             ${NC}"
    echo -e "${GREEN}║  Log:      $LOG_FILE${NC}"
    echo -e "${GREEN}║  Station:  ${STATION_CRS:-PAD}                                           ${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "To stop the server, run: ./shutdown.sh"
    echo ""
else
    echo -e "${RED}✗ Failed to start server. Check $LOG_FILE for details.${NC}"
    rm -f "$PID_FILE"
    cat "$LOG_FILE"
    exit 1
fi
