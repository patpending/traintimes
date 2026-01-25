#!/usr/bin/env python3
"""
Standalone UK Train Departure Board Web Application

A Flask application that displays live train departures in authentic
UK station departure board style.
"""

import os
from datetime import datetime

from flask import Flask, render_template, jsonify, request

from darwin_api import DarwinApi, DarwinApiError

app = Flask(__name__)

# Support running behind Home Assistant ingress proxy
app.config['APPLICATION_ROOT'] = '/'

# Configuration
API_TOKEN = os.environ.get('DARWIN_API_TOKEN', '')
STATION_CRS = os.environ.get('STATION_CRS', 'PAD')
NUM_DEPARTURES = int(os.environ.get('NUM_DEPARTURES', '6'))
# Support multiple destinations separated by comma
DESTINATION_CRS = os.environ.get('DESTINATION_CRS', '')
DESTINATION_LIST = [d.strip().upper() for d in DESTINATION_CRS.split(',') if d.strip()]

# Station names lookup
STATION_NAMES = {
    "PAD": "London Paddington",
    "EUS": "London Euston",
    "KGX": "London King's Cross",
    "STP": "London St Pancras International",
    "VIC": "London Victoria",
    "WAT": "London Waterloo",
    "CHX": "London Charing Cross",
    "LST": "London Liverpool Street",
    "BHM": "Birmingham New Street",
    "MAN": "Manchester Piccadilly",
    "LDS": "Leeds",
    "EDB": "Edinburgh Waverley",
    "GLC": "Glasgow Central",
    "BRI": "Bristol Temple Meads",
    "RDG": "Reading",
    "OXF": "Oxford",
    "CBG": "Cambridge",
    "NCL": "Newcastle",
    "LIV": "Liverpool Lime Street",
    "SHF": "Sheffield",
    "SVG": "Stevenage",
    "HIT": "Hitchin",
    "LET": "Letchworth Garden City",
    "BDK": "Baldock",
    "RYS": "Royston",
}


def get_station_name(crs: str) -> str:
    """Get the full station name from CRS code."""
    return STATION_NAMES.get(crs.upper(), crs.upper())


@app.route('/')
def index():
    """Render the departure board page."""
    station = request.args.get('station', STATION_CRS).upper()
    station_name = get_station_name(station)
    return render_template('board.html',
                         station_crs=station,
                         station_name=station_name)


def get_demo_departures(station_crs):
    """Return demo departure data for testing the UI."""
    now = datetime.now()

    demo_data = [
        {
            'destination': 'Bristol Temple Meads',
            'scheduled_time': (now.replace(minute=(now.minute + 5) % 60)).strftime('%H:%M'),
            'expected_time': 'On time',
            'platform': '1',
            'operator': 'Great Western Railway',
            'status': 'on_time',
            'is_cancelled': False,
            'cancel_reason': None,
            'delay_reason': None,
            'calling_points': [
                {'station': 'Reading', 'scheduled': (now.replace(minute=(now.minute + 25) % 60)).strftime('%H:%M'), 'expected': 'On time'},
                {'station': 'Didcot Parkway', 'scheduled': (now.replace(minute=(now.minute + 40) % 60)).strftime('%H:%M'), 'expected': 'On time'},
                {'station': 'Swindon', 'scheduled': (now.replace(minute=(now.minute + 55) % 60)).strftime('%H:%M'), 'expected': 'On time'},
                {'station': 'Bath Spa', 'scheduled': (now.replace(hour=(now.hour + 1) % 24, minute=(now.minute + 20) % 60)).strftime('%H:%M'), 'expected': 'On time'},
                {'station': 'Bristol Temple Meads', 'scheduled': (now.replace(hour=(now.hour + 1) % 24, minute=(now.minute + 35) % 60)).strftime('%H:%M'), 'expected': 'On time'},
            ]
        },
        {
            'destination': 'Oxford',
            'scheduled_time': (now.replace(minute=(now.minute + 12) % 60)).strftime('%H:%M'),
            'expected_time': (now.replace(minute=(now.minute + 17) % 60)).strftime('%H:%M'),
            'platform': '4',
            'operator': 'Great Western Railway',
            'status': 'delayed',
            'is_cancelled': False,
            'cancel_reason': None,
            'delay_reason': 'Awaiting train crew',
            'calling_points': [
                {'station': 'Slough', 'scheduled': (now.replace(minute=(now.minute + 25) % 60)).strftime('%H:%M'), 'expected': 'On time'},
                {'station': 'Reading', 'scheduled': (now.replace(minute=(now.minute + 40) % 60)).strftime('%H:%M'), 'expected': 'On time'},
                {'station': 'Didcot Parkway', 'scheduled': (now.replace(minute=(now.minute + 55) % 60)).strftime('%H:%M'), 'expected': 'On time'},
                {'station': 'Oxford', 'scheduled': (now.replace(hour=(now.hour + 1) % 24, minute=(now.minute + 10) % 60)).strftime('%H:%M'), 'expected': 'On time'},
            ]
        },
        {
            'destination': 'Penzance',
            'scheduled_time': (now.replace(minute=(now.minute + 20) % 60)).strftime('%H:%M'),
            'expected_time': 'On time',
            'platform': '3',
            'operator': 'Great Western Railway',
            'status': 'on_time',
            'is_cancelled': False,
            'cancel_reason': None,
            'delay_reason': None,
            'calling_points': [
                {'station': 'Reading', 'scheduled': (now.replace(minute=(now.minute + 35) % 60)).strftime('%H:%M'), 'expected': 'On time'},
                {'station': 'Taunton', 'scheduled': (now.replace(hour=(now.hour + 1) % 24, minute=(now.minute + 30) % 60)).strftime('%H:%M'), 'expected': 'On time'},
                {'station': 'Exeter St Davids', 'scheduled': (now.replace(hour=(now.hour + 2) % 24, minute=now.minute)).strftime('%H:%M'), 'expected': 'On time'},
                {'station': 'Plymouth', 'scheduled': (now.replace(hour=(now.hour + 3) % 24, minute=now.minute)).strftime('%H:%M'), 'expected': 'On time'},
                {'station': 'Penzance', 'scheduled': (now.replace(hour=(now.hour + 5) % 24, minute=now.minute)).strftime('%H:%M'), 'expected': 'On time'},
            ]
        },
        {
            'destination': 'Cardiff Central',
            'scheduled_time': (now.replace(minute=(now.minute + 28) % 60)).strftime('%H:%M'),
            'expected_time': 'Cancelled',
            'platform': '-',
            'operator': 'Great Western Railway',
            'status': 'cancelled',
            'is_cancelled': True,
            'cancel_reason': 'A points failure',
            'delay_reason': None,
            'calling_points': []
        },
        {
            'destination': 'Swansea',
            'scheduled_time': (now.replace(minute=(now.minute + 35) % 60)).strftime('%H:%M'),
            'expected_time': 'On time',
            'platform': '6',
            'operator': 'Great Western Railway',
            'status': 'on_time',
            'is_cancelled': False,
            'cancel_reason': None,
            'delay_reason': None,
            'calling_points': [
                {'station': 'Reading', 'scheduled': (now.replace(minute=(now.minute + 50) % 60)).strftime('%H:%M'), 'expected': 'On time'},
                {'station': 'Swindon', 'scheduled': (now.replace(hour=(now.hour + 1) % 24, minute=(now.minute + 10) % 60)).strftime('%H:%M'), 'expected': 'On time'},
                {'station': 'Bristol Parkway', 'scheduled': (now.replace(hour=(now.hour + 1) % 24, minute=(now.minute + 35) % 60)).strftime('%H:%M'), 'expected': 'On time'},
                {'station': 'Newport', 'scheduled': (now.replace(hour=(now.hour + 2) % 24, minute=now.minute)).strftime('%H:%M'), 'expected': 'On time'},
                {'station': 'Cardiff Central', 'scheduled': (now.replace(hour=(now.hour + 2) % 24, minute=(now.minute + 15) % 60)).strftime('%H:%M'), 'expected': 'On time'},
                {'station': 'Swansea', 'scheduled': (now.replace(hour=(now.hour + 3) % 24, minute=now.minute)).strftime('%H:%M'), 'expected': 'On time'},
            ]
        },
        {
            'destination': 'Cheltenham Spa',
            'scheduled_time': (now.replace(minute=(now.minute + 42) % 60)).strftime('%H:%M'),
            'expected_time': 'On time',
            'platform': '2',
            'operator': 'Great Western Railway',
            'status': 'on_time',
            'is_cancelled': False,
            'cancel_reason': None,
            'delay_reason': None,
            'calling_points': [
                {'station': 'Reading', 'scheduled': (now.replace(minute=(now.minute + 55) % 60)).strftime('%H:%M'), 'expected': 'On time'},
                {'station': 'Swindon', 'scheduled': (now.replace(hour=(now.hour + 1) % 24, minute=(now.minute + 20) % 60)).strftime('%H:%M'), 'expected': 'On time'},
                {'station': 'Gloucester', 'scheduled': (now.replace(hour=(now.hour + 1) % 24, minute=(now.minute + 50) % 60)).strftime('%H:%M'), 'expected': 'On time'},
                {'station': 'Cheltenham Spa', 'scheduled': (now.replace(hour=(now.hour + 2) % 24, minute=(now.minute + 5) % 60)).strftime('%H:%M'), 'expected': 'On time'},
            ]
        },
    ]

    return demo_data


@app.route('/api/departures')
def get_departures():
    """API endpoint to get live departure data."""
    station = request.args.get('station', STATION_CRS).upper()
    destination_param = request.args.get('destination', DESTINATION_CRS).upper()
    num = int(request.args.get('num', NUM_DEPARTURES))
    demo = request.args.get('demo', 'false').lower() == 'true'

    # Parse destination list (comma-separated)
    # Empty string means no filter (show all), use config default otherwise
    if destination_param == '':
        destinations = []  # No filter - show all departures
    elif destination_param:
        destinations = [d.strip() for d in destination_param.split(',') if d.strip()]
    else:
        destinations = DESTINATION_LIST

    # Use demo mode if requested or if no valid API token
    if demo or not API_TOKEN or API_TOKEN == "YOUR_API_TOKEN_HERE":
        return jsonify({
            'departures': get_demo_departures(station)[:num],
            'station_name': get_station_name(station),
            'station_crs': station,
            'time': datetime.now().strftime('%H:%M'),
            'last_updated': datetime.now().isoformat(),
            'demo_mode': True
        })

    try:
        api = DarwinApi(API_TOKEN)

        # Always fetch without API filter - we'll filter client-side by calling points
        # This ensures we get the correct final destination, not the filter station
        all_services = api.get_departure_board(
            station_crs=station,
            num_rows=20,  # Fetch more to allow for filtering
            destination_crs=None
        )

        # Filter by calling points if destinations specified
        if destinations:
            filtered_services = []
            for service in all_services:
                # Check if final destination matches
                if service.destination_crs in destinations:
                    filtered_services.append(service)
                    continue
                # Check if any calling point matches
                for cp in service.calling_points:
                    if cp.crs in destinations:
                        filtered_services.append(service)
                        break
            services = filtered_services[:num]
        else:
            services = all_services[:num]

        departures = []
        for service in services:
            calling_points = [
                {
                    'station': cp.station_name,
                    'crs': cp.crs,
                    'scheduled': cp.scheduled_time,
                    'expected': cp.expected_time
                }
                for cp in service.calling_points
            ]

            departures.append({
                'destination': service.destination,
                'scheduled_time': service.scheduled_time,
                'expected_time': service.expected_time,
                'platform': service.platform or '-',
                'operator': service.operator,
                'status': service.status,
                'is_cancelled': service.is_cancelled,
                'cancel_reason': service.cancel_reason,
                'delay_reason': service.delay_reason,
                'calling_points': calling_points
            })

        return jsonify({
            'departures': departures,
            'station_name': get_station_name(station),
            'station_crs': station,
            'time': datetime.now().strftime('%H:%M'),
            'last_updated': datetime.now().isoformat(),
            'demo_mode': False
        })

    except DarwinApiError as e:
        # Fall back to demo mode on API error
        return jsonify({
            'departures': get_demo_departures(station)[:num],
            'station_name': get_station_name(station),
            'station_crs': station,
            'time': datetime.now().strftime('%H:%M'),
            'last_updated': datetime.now().isoformat(),
            'demo_mode': True,
            'api_error': str(e)
        })


@app.route('/api/stations')
def get_stations():
    """API endpoint to get list of common stations."""
    return jsonify({
        'stations': [
            {'crs': crs, 'name': name}
            for crs, name in sorted(STATION_NAMES.items(), key=lambda x: x[1])
        ]
    })


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'time': datetime.now().isoformat()})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'

    print(f"""
╔════════════════════════════════════════════════════════════════╗
║                   UK Train Departure Board                      ║
╠════════════════════════════════════════════════════════════════╣
║  Server starting on http://localhost:{port:<5}                     ║
║  Station: {STATION_CRS:3} ({get_station_name(STATION_CRS)[:30]:<30})    ║
║  Departures: {NUM_DEPARTURES}                                              ║
╚════════════════════════════════════════════════════════════════╝
    """)

    if not API_TOKEN:
        print("WARNING: No DARWIN_API_TOKEN set. Set this environment variable.")
        print("   Get your token from: https://opendata.nationalrail.co.uk/")

    app.run(host='0.0.0.0', port=port, debug=debug)
