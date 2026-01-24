# Home Assistant Integration Guide

This guide explains how to install and configure the UK Train Departures integration for Home Assistant.

## Prerequisites

- Home Assistant 2023.1 or later
- A National Rail Darwin API token (free) - see [Getting an API Token](#getting-an-api-token)

## Installation

### Method 1: Manual Installation

1. **Download the integration**

   Download or clone this repository:
   ```bash
   git clone https://github.com/patpending/traintimes.git
   ```

2. **Copy to Home Assistant**

   Copy the `custom_components/uk_train_departures` folder to your Home Assistant configuration directory:
   ```
   /config/custom_components/uk_train_departures/
   ```

   Your directory structure should look like:
   ```
   config/
   ├── configuration.yaml
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

3. **Restart Home Assistant**

   Restart Home Assistant to load the new integration.

### Method 2: HACS (Coming Soon)

HACS installation will be available in a future release.

## Configuration

### Adding the Integration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "UK Train Departures"
4. Enter your configuration:

   | Field | Description | Example |
   |-------|-------------|---------|
   | API Token | Your National Rail Darwin API token | `453f5f0a-9e29-...` |
   | Station CRS | 3-letter station code | `SVG` (Stevenage) |
   | Destination Filter | Optional: only show trains calling at this station | `KGX` (King's Cross) |
   | Number of Departures | How many trains to show (1-10) | `3` |

5. Click **Submit**

### Finding Your Station Code

Station codes (CRS codes) can be found at:
- https://www.nationalrail.co.uk/stations_destinations/

Common codes:
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

## Entities Created

The integration creates the following entities:

### Individual Departure Sensors

For each departure slot (e.g., 3 departures = 3 sensors):

- `sensor.departures_from_[station]_departure_1`
- `sensor.departures_from_[station]_departure_2`
- `sensor.departures_from_[station]_departure_3`

**State:** Destination name (e.g., "London Kings Cross")

**Attributes:**
| Attribute | Description | Example |
|-----------|-------------|---------|
| `scheduled_time` | Timetabled departure | `08:45` |
| `expected_time` | Predicted time or status | `On time` / `08:52` / `Cancelled` |
| `platform` | Platform number | `1` |
| `operator` | Train company | `Thameslink` |
| `status` | Status code | `on_time` / `delayed` / `cancelled` |
| `calling_points` | List of stops | See below |

**Calling Points Format:**
```yaml
calling_points:
  - station: "Finsbury Park"
    crs: "FPK"
    scheduled: "09:02"
    expected: "On time"
  - station: "London Kings Cross"
    crs: "KGX"
    scheduled: "09:10"
    expected: "On time"
```

### Summary Sensor

- `sensor.departures_from_[station]_departures`

**State:** Number of departures (e.g., `3`)

**Attributes:**
| Attribute | Description |
|-----------|-------------|
| `departures` | Full list of all departure data |
| `station_crs` | Station code |
| `station_name` | Full station name |
| `on_time_count` | Number of on-time trains |
| `delayed_count` | Number of delayed trains |
| `cancelled_count` | Number of cancelled trains |

## Custom Lovelace Card

For an authentic departure board display, install the custom card:

### Installation

1. Copy `lovelace/uk-departures-card.js` to your `www` folder:
   ```
   config/www/uk-departures-card.js
   ```

2. Add the resource in Home Assistant:
   - Go to **Settings** → **Dashboards**
   - Click the three dots menu → **Resources**
   - Click **+ Add Resource**
   - URL: `/local/uk-departures-card.js`
   - Type: **JavaScript Module**

3. Add the card to your dashboard:
   ```yaml
   type: custom:uk-departures-card
   entity: sensor.departures_from_stevenage_departures
   title: Stevenage
   show_calling_points: true
   show_clock: true
   show_platform: true
   num_departures: 6
   ```

### Card Configuration

| Option | Default | Description |
|--------|---------|-------------|
| `entity` | Required | The summary sensor entity |
| `title` | Station name | Header title |
| `show_calling_points` | `true` | Show scrolling calling points |
| `show_clock` | `true` | Show current time |
| `show_platform` | `true` | Show platform column |
| `num_departures` | `3` | Number of rows to display |

## Example Automations

### Notification When Train is Delayed

```yaml
automation:
  - alias: "Train Delay Alert"
    trigger:
      - platform: state
        entity_id: sensor.departures_from_stevenage_departure_1
    condition:
      - condition: template
        value_template: "{{ state_attr('sensor.departures_from_stevenage_departure_1', 'status') == 'delayed' }}"
    action:
      - service: notify.mobile_app
        data:
          title: "Train Delayed"
          message: >
            The {{ state_attr('sensor.departures_from_stevenage_departure_1', 'scheduled_time') }}
            to {{ states('sensor.departures_from_stevenage_departure_1') }}
            is now expected at {{ state_attr('sensor.departures_from_stevenage_departure_1', 'expected_time') }}
```

### Morning Commute Summary

```yaml
automation:
  - alias: "Morning Train Summary"
    trigger:
      - platform: time
        at: "07:00:00"
    condition:
      - condition: time
        weekday:
          - mon
          - tue
          - wed
          - thu
          - fri
    action:
      - service: notify.mobile_app
        data:
          title: "Morning Trains"
          message: >
            Next train: {{ state_attr('sensor.departures_from_stevenage_departure_1', 'scheduled_time') }}
            to {{ states('sensor.departures_from_stevenage_departure_1') }}
            ({{ state_attr('sensor.departures_from_stevenage_departure_1', 'expected_time') }})
```

## Getting an API Token

1. Visit https://opendata.nationalrail.co.uk/
2. Click **Register** and create an account
3. Verify your email address
4. Log in and go to **My Feeds**
5. Subscribe to **Live Departure Boards (OpenLDBWS)**
6. Accept the terms and conditions
7. Your API token will be displayed (UUID format)

The API is free for up to 5 million requests per month.

## Troubleshooting

### "Invalid API token" Error

- Ensure the token is copied correctly without extra spaces
- Verify you've subscribed to the OpenLDBWS feed specifically
- Try regenerating your token in the portal

### No Departures Showing

- Check the station CRS code is correct
- Some stations have limited services at certain times
- If using a destination filter, ensure trains actually call there

### Integration Not Appearing

- Check the `custom_components` folder structure is correct
- Look at Home Assistant logs for errors
- Ensure you've restarted Home Assistant after installation

### Entities Not Updating

- The integration polls every 30 seconds
- Check your internet connection
- Verify the API token is still valid

## Support

- GitHub Issues: https://github.com/patpending/traintimes/issues
- National Rail API Forum: https://groups.google.com/g/openraildata-talk
