#!/bin/bash
#
# UK Train Departure Board - Shutdown Script
#
# Gracefully stops the standalone Flask web server.
# Usage: ./shutdown.sh
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/.departure-board.pid"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║          UK Train Departure Board - Shutdown Script            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if PID file exists
if [ ! -f "$PID_FILE" ]; then
    echo -e "${YELLOW}⚠️  No PID file found. Server may not be running.${NC}"

    # Try to find any running instance
    RUNNING_PID=$(pgrep -f "standalone/app.py" 2>/dev/null)
    if [ -n "$RUNNING_PID" ]; then
        echo -e "${YELLOW}Found running process with PID: $RUNNING_PID${NC}"
        read -p "Kill this process? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            kill "$RUNNING_PID" 2>/dev/null
            echo -e "${GREEN}✓ Process killed${NC}"
        fi
    else
        echo "No departure board server process found."
    fi
    exit 0
fi

# Read PID
PID=$(cat "$PID_FILE")

# Check if process is running
if ! ps -p "$PID" > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Process $PID is not running. Cleaning up PID file.${NC}"
    rm -f "$PID_FILE"
    exit 0
fi

# Gracefully stop the server
echo "Stopping server (PID: $PID)..."

# Send SIGTERM first
kill "$PID" 2>/dev/null

# Wait for graceful shutdown (up to 10 seconds)
COUNTER=0
while ps -p "$PID" > /dev/null 2>&1 && [ $COUNTER -lt 10 ]; do
    sleep 1
    COUNTER=$((COUNTER + 1))
    echo -n "."
done
echo ""

# Check if still running
if ps -p "$PID" > /dev/null 2>&1; then
    echo -e "${YELLOW}Process still running. Sending SIGKILL...${NC}"
    kill -9 "$PID" 2>/dev/null
    sleep 1
fi

# Clean up PID file
rm -f "$PID_FILE"

# Final check
if ps -p "$PID" > /dev/null 2>&1; then
    echo -e "${RED}✗ Failed to stop server${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Server stopped successfully${NC}"
    echo ""
fi
