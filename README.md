# UK Train Departures

A Home Assistant integration and standalone web application that displays live train departures from UK stations in authentic station departure board style.

![Departure Board Example](https://ukdepartureboards.co.uk/wp-content/uploads/2023/departure-board-preview.jpg)

## Features

- **Real-time departure data** from National Rail's Darwin system
- **Authentic UK station board styling** with amber LED text and dot matrix fonts
- **Calling points display** showing all stops for each train
- **Status indicators** for on-time, delayed, and cancelled services
- **Platform information** where available
- **Home Assistant integration** with sensor entities and custom Lovelace card
- **Standalone web mode** runnable without Home Assistant

## Getting Your API Token

To use this integration, you need a free API token from National Rail Enquiries.

### Step-by-Step Registration Guide

1. **Visit the National Rail Data Portal**

   Go to: https://opendata.nationalrail.co.uk/

2. **Create an Account**

   - Click "Register" in the top right corner
   - Fill in the registration form:
     - Email address (you'll need to verify this)
     - Password
     - Your name
     - Organisation (can be "Personal Use")
   - Accept the terms and conditions
   - Click "Register"

3. **Verify Your Email**

   - Check your inbox for a verification email from National Rail
   - Click the verification link
   - Log in with your new credentials

4. **Subscribe to the Darwin API**

   - Once logged in, navigate to "My Feeds" or "My Account"
   - Look for "Live Departure Boards" or "OpenLDBWS"
   - Click "Subscribe" or "Add Feed"
   - Accept the specific terms for this feed (based on Open Government Licence 2.0)

5. **Get Your API Token**

   - After subscribing, your API token will be displayed
   - It's a UUID format like: `12345678-1234-1234-1234-123456789abc`
   - **Copy this token and keep it safe!**

### Alternative Registration Link

If the above doesn't work, try the direct registration link:
https://realtime.nationalrail.co.uk/OpenLDBWSRegistration/

### Usage Limits

- **Free tier**: Up to 5 million requests per 4-week railway period
- This is more than enough for personal use (1 request every 30 seconds = ~100k/month)
- Commercial high-volume users may need to pay for additional capacity

### Need Help?

- Official documentation: https://wiki.openraildata.com/
- Community forum: https://groups.google.com/g/openraildata-talk

## Installation

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Quick Start

```bash
# Clone or download this repository
cd traintimes

# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and edit the config file
cp config.yaml.example config.yaml
# Edit config.yaml with your API token and station code
```

## Standalone Mode

Run the departure board as a standalone web application without Home Assistant.

### Configuration

Edit `config.yaml`:

```yaml
api_token: "your-api-token-here"
station_crs: "PAD"  # Your station's 3-letter code
num_departures: 6
```

### Starting the Server

```bash
./startup.sh
```

Or with a custom port:

```bash
./startup.sh 8080
```

The departure board will be available at: http://localhost:5000

### Stopping the Server

```bash
./shutdown.sh
```

### Environment Variables

You can also configure via environment variables:

```bash
export DARWIN_API_TOKEN="your-token"
export STATION_CRS="PAD"
export NUM_DEPARTURES=6
export PORT=5000
./startup.sh
```

## Home Assistant Integration

### Installation

1. Copy the `custom_components/uk_train_departures` folder to your Home Assistant's `custom_components` directory:

   ```
   config/
   └── custom_components/
       └── uk_train_departures/
           ├── __init__.py
           ├── api.py
           ├── config_flow.py
           ├── const.py
           ├── coordinator.py
           ├── manifest.json
           ├── sensor.py
           └── strings.json
   ```

2. Restart Home Assistant

3. Go to **Settings > Devices & Services > Add Integration**

4. Search for "UK Train Departures"

5. Enter your:
   - API token
   - Station CRS code (e.g., "PAD" for Paddington)
   - Number of departures to show
   - Optional destination filter

### Entities Created

The integration creates the following entities:

- `sensor.departures_from_[station]_departure_1` - First departure
- `sensor.departures_from_[station]_departure_2` - Second departure
- `sensor.departures_from_[station]_departure_3` - Third departure
- `sensor.departures_from_[station]_departures` - Summary sensor with all departures

Each departure sensor has attributes:
- `destination` - Final destination
- `scheduled_time` - Timetabled departure time
- `expected_time` - Predicted time (or "On time"/"Cancelled")
- `platform` - Platform number
- `operator` - Train operating company
- `status` - on_time, delayed, or cancelled
- `calling_points` - List of stations the train stops at

### Custom Lovelace Card

For the authentic departure board look in Home Assistant:

1. Copy `lovelace/uk-departures-card.js` to your `www` folder:

   ```
   config/
   └── www/
       └── uk-departures-card.js
   ```

2. Add the card as a resource in your Lovelace dashboard:

   - Go to **Settings > Dashboards**
   - Click the three dots menu > **Resources**
   - Add `/local/uk-departures-card.js` as JavaScript Module

3. Add the card to your dashboard:

   ```yaml
   type: custom:uk-departures-card
   entity: sensor.departures_from_paddington_departures
   title: Paddington Departures
   show_calling_points: true
   show_clock: true
   num_departures: 3
   ```

## Station CRS Codes

Find your station's 3-letter CRS code at:
https://www.nationalrail.co.uk/stations_destinations/

### Common Station Codes

| Code | Station |
|------|---------|
| PAD | London Paddington |
| EUS | London Euston |
| KGX | London King's Cross |
| STP | London St Pancras International |
| VIC | London Victoria |
| WAT | London Waterloo |
| CHX | London Charing Cross |
| LST | London Liverpool Street |
| BHM | Birmingham New Street |
| MAN | Manchester Piccadilly |
| LDS | Leeds |
| EDB | Edinburgh Waverley |
| GLC | Glasgow Central |
| BRI | Bristol Temple Meads |
| RDG | Reading |
| OXF | Oxford |
| CBG | Cambridge |
| NCL | Newcastle |
| LIV | Liverpool Lime Street |
| SHF | Sheffield |

## Troubleshooting

### "Invalid API token" Error

- Double-check your token is copied correctly (no extra spaces)
- Ensure you've subscribed to the "Live Departure Boards" feed
- Try regenerating your token in the portal

### "No departures" Showing

- Some stations may have no scheduled departures at certain times
- Check the station CRS code is correct
- Try a major station like PAD to test

### Connection Errors

- Check your internet connection
- The National Rail API may occasionally be down for maintenance
- Check https://groups.google.com/g/openraildata-talk for status updates

### Fonts Not Displaying Correctly

The Dot Matrix font is loaded from a CDN. If it doesn't load:
- Check your internet connection
- Try refreshing the page
- The board will fall back to Courier New

## API Rate Limits

The integration polls every 30 seconds by default. This means:
- ~2,880 requests per day
- ~86,400 requests per month
- Well within the free 5 million request limit

## Credits

- Train data provided by [National Rail Enquiries](https://www.nationalrail.co.uk/)
- Dot Matrix font by [DanielHartUK](https://github.com/DanielHartUK/Dot-Matrix-Typeface)
- Inspired by [UK Departure Boards](https://ukdepartureboards.co.uk/)

## License

MIT License - See LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.
