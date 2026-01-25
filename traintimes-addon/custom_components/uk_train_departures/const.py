"""Constants for the UK Train Departures integration."""

DOMAIN = "uk_train_departures"
CONF_STATION_CRS = "station_crs"
CONF_API_TOKEN = "api_token"
CONF_DESTINATION_CRS = "destination_crs"
CONF_NUM_DEPARTURES = "num_departures"

# Watched trains configuration
CONF_WATCHED_TRAIN_1_TIME = "watched_train_1_time"
CONF_WATCHED_TRAIN_1_DEST = "watched_train_1_destination"
CONF_WATCHED_TRAIN_2_TIME = "watched_train_2_time"
CONF_WATCHED_TRAIN_2_DEST = "watched_train_2_destination"
CONF_WATCHED_TRAIN_3_TIME = "watched_train_3_time"
CONF_WATCHED_TRAIN_3_DEST = "watched_train_3_destination"

DEFAULT_NUM_DEPARTURES = 3
DEFAULT_SCAN_INTERVAL = 30  # seconds

# Darwin API endpoint
DARWIN_WSDL = "https://lite.realtime.nationalrail.co.uk/OpenLDBWS/wsdl.aspx?ver=2021-11-01"
DARWIN_NAMESPACE = "http://thalesgroup.com/RTTI/2021-11-01/Token/types"

# Status constants
STATUS_ON_TIME = "on_time"
STATUS_DELAYED = "delayed"
STATUS_CANCELLED = "cancelled"
STATUS_NO_REPORT = "no_report"

# Common UK station CRS codes for reference
STATION_CODES = {
    "PAD": "London Paddington",
    "EUS": "London Euston",
    "KGX": "London King's Cross",
    "STP": "London St Pancras",
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
}
