# UK Train Departures Add-on

Display live UK train departures with authentic station departure board styling.

## Configuration

### API Token (Required)

You need a National Rail Darwin API token to fetch live departure data.

1. Visit https://opendata.nationalrail.co.uk/
2. Click **Register** and create an account
3. Verify your email address
4. Log in and go to **My Feeds**
5. Subscribe to **Live Departure Boards (OpenLDBWS)**
6. Accept the terms and conditions
7. Your API token will be displayed (UUID format)

The API is free for up to 5 million requests per month.

### Station CRS Code

The 3-letter CRS code for your station. Common codes:

| Code | Station |
|------|---------|
| KGX | London King's Cross |
| STP | London St Pancras |
| EUS | London Euston |
| PAD | London Paddington |
| VIC | London Victoria |
| WAT | London Waterloo |
| BHM | Birmingham New Street |
| MAN | Manchester Piccadilly |
| SVG | Stevenage |
| CTK | City Thameslink |

Find more codes at: https://www.nationalrail.co.uk/stations_destinations/

### Destination Filter (Optional)

Filter to only show trains calling at specific stations. Use comma-separated CRS codes.

Examples:
- `KGX` - Only trains to King's Cross
- `KGX,STP` - Trains to King's Cross OR St Pancras
- `KGX,STP,CTK` - Trains calling at any of these London stations

Leave empty to show all departures.

### Number of Departures

How many trains to display (1-10). Default is 6.

### Log Level

Set the logging verbosity:
- `debug` - Verbose logging for troubleshooting
- `info` - Normal operation messages
- `warning` - Only warnings and errors
- `error` - Only errors

## Usage

After configuring the add-on:

1. Start the add-on
2. Click "Open Web UI" to view the departure board
3. The board updates automatically every 30 seconds

## Troubleshooting

### "No departures" showing

- Check your station CRS code is correct
- If using destination filter, ensure trains actually call at those stations
- Some stations have limited services at certain times

### API errors

- Verify your API token is correct
- Ensure you've subscribed to the OpenLDBWS feed specifically
- Check the add-on logs for detailed error messages
