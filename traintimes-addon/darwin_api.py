"""National Rail Darwin SOAP API client - Standalone version using raw requests."""

import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Optional

import requests

_LOGGER = logging.getLogger(__name__)

# Darwin API endpoint
DARWIN_ENDPOINT = "https://lite.realtime.nationalrail.co.uk/OpenLDBWS/ldb12.asmx"

# Status constants
STATUS_ON_TIME = "on_time"
STATUS_DELAYED = "delayed"
STATUS_CANCELLED = "cancelled"

# Namespaces used in responses
NS = {
    'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
    'ldb': 'http://thalesgroup.com/RTTI/2021-11-01/ldb/',
    'lt': 'http://thalesgroup.com/RTTI/2012-01-13/ldb/types',
    'lt2': 'http://thalesgroup.com/RTTI/2014-02-20/ldb/types',
    'lt3': 'http://thalesgroup.com/RTTI/2015-05-14/ldb/types',
    'lt4': 'http://thalesgroup.com/RTTI/2015-11-27/ldb/types',
    'lt5': 'http://thalesgroup.com/RTTI/2016-02-16/ldb/types',
    'lt6': 'http://thalesgroup.com/RTTI/2017-02-02/ldb/types',
    'lt7': 'http://thalesgroup.com/RTTI/2017-10-01/ldb/types',
    'lt8': 'http://thalesgroup.com/RTTI/2021-11-01/ldb/types',
}


@dataclass
class CallingPoint:
    """Represents a calling point (station stop) on a service."""

    station_name: str
    crs: str
    scheduled_time: str
    expected_time: str
    is_cancelled: bool = False

    @property
    def status(self) -> str:
        """Get the status of this calling point."""
        if self.is_cancelled:
            return STATUS_CANCELLED
        if self.expected_time == "On time":
            return STATUS_ON_TIME
        if self.expected_time == "Delayed":
            return STATUS_DELAYED
        return STATUS_ON_TIME


@dataclass
class TrainService:
    """Represents a train departure service."""

    service_id: str
    destination: str
    destination_crs: str
    scheduled_time: str
    expected_time: str
    platform: Optional[str] = None
    operator: str = ""
    operator_code: str = ""
    is_cancelled: bool = False
    cancel_reason: Optional[str] = None
    delay_reason: Optional[str] = None
    calling_points: list[CallingPoint] = field(default_factory=list)

    @property
    def status(self) -> str:
        """Get the status of this service."""
        if self.is_cancelled:
            return STATUS_CANCELLED
        if self.expected_time == "On time":
            return STATUS_ON_TIME
        if self.expected_time in ("Delayed", "Cancelled"):
            return STATUS_DELAYED if self.expected_time == "Delayed" else STATUS_CANCELLED
        try:
            if self.expected_time != self.scheduled_time:
                return STATUS_DELAYED
        except Exception:
            pass
        return STATUS_ON_TIME


class DarwinApiError(Exception):
    """Exception for Darwin API errors."""
    pass


class DarwinApi:
    """Client for the National Rail Darwin SOAP API."""

    def __init__(self, api_token: str):
        """Initialize the Darwin API client."""
        self._api_token = api_token

    def _build_request(self, station_crs: str, num_rows: int,
                       destination_crs: Optional[str] = None,
                       time_offset: int = 0, time_window: int = 120) -> str:
        """Build the SOAP request XML."""
        filter_section = ""
        if destination_crs:
            filter_section = f"""
            <ldb:filterCrs>{destination_crs.upper()}</ldb:filterCrs>
            <ldb:filterType>to</ldb:filterType>"""

        return f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:typ="http://thalesgroup.com/RTTI/2013-11-28/Token/types"
               xmlns:ldb="http://thalesgroup.com/RTTI/2021-11-01/ldb/">
    <soap:Header>
        <typ:AccessToken>
            <typ:TokenValue>{self._api_token}</typ:TokenValue>
        </typ:AccessToken>
    </soap:Header>
    <soap:Body>
        <ldb:GetDepBoardWithDetailsRequest>
            <ldb:numRows>{num_rows}</ldb:numRows>
            <ldb:crs>{station_crs.upper()}</ldb:crs>{filter_section}
            <ldb:timeOffset>{time_offset}</ldb:timeOffset>
            <ldb:timeWindow>{time_window}</ldb:timeWindow>
        </ldb:GetDepBoardWithDetailsRequest>
    </soap:Body>
</soap:Envelope>"""

    def get_departure_board(
        self,
        station_crs: str,
        num_rows: int = 3,
        destination_crs: Optional[str] = None,
        time_offset: int = 0,
        time_window: int = 120,
    ) -> list[TrainService]:
        """Get the departure board for a station."""
        try:
            soap_request = self._build_request(
                station_crs, num_rows, destination_crs, time_offset, time_window
            )

            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': 'http://thalesgroup.com/RTTI/2015-05-14/ldb/GetDepBoardWithDetails'
            }

            response = requests.post(
                DARWIN_ENDPOINT,
                data=soap_request,
                headers=headers,
                timeout=30
            )

            if response.status_code == 401:
                raise DarwinApiError("Invalid API token - authentication failed")

            if response.status_code != 200:
                raise DarwinApiError(f"API returned status {response.status_code}")

            return self._parse_response(response.text)

        except requests.RequestException as e:
            _LOGGER.error("Request error: %s", str(e))
            raise DarwinApiError(f"Connection error: {str(e)}") from e
        except ET.ParseError as e:
            _LOGGER.error("XML parse error: %s", str(e))
            raise DarwinApiError(f"Failed to parse response: {str(e)}") from e
        except Exception as e:
            _LOGGER.error("Unexpected error: %s", str(e))
            raise DarwinApiError(f"Unexpected error: {str(e)}") from e

    def _parse_response(self, xml_text: str) -> list[TrainService]:
        """Parse the SOAP response XML into TrainService objects."""
        root = ET.fromstring(xml_text)

        # Check for SOAP fault
        fault = root.find('.//soap:Fault', NS)
        if fault is not None:
            fault_string = fault.find('faultstring')
            raise DarwinApiError(fault_string.text if fault_string is not None else "Unknown SOAP fault")

        services = []

        # Find all train services in the response
        for service in root.findall('.//lt8:service', NS):
            train_service = self._parse_service(service)
            if train_service:
                services.append(train_service)

        return services

    def _parse_service(self, service_elem) -> Optional[TrainService]:
        """Parse a service element into a TrainService object."""
        try:
            # Get basic service info
            service_id = self._get_text(service_elem, 'lt4:serviceID')
            if not service_id:
                return None

            # Get destination(s)
            destinations = service_elem.findall('.//lt5:destination/lt4:location', NS)
            if destinations:
                dest_names = [self._get_text(d, 'lt4:locationName') for d in destinations]
                destination = " & ".join(filter(None, dest_names))
                destination_crs = self._get_text(destinations[0], 'lt4:crs') or ""
            else:
                destination = "Unknown"
                destination_crs = ""

            # Get timing info
            scheduled_time = self._get_text(service_elem, 'lt4:std') or ""
            expected_time = self._get_text(service_elem, 'lt4:etd') or "On time"

            # Get platform
            platform = self._get_text(service_elem, 'lt4:platform')

            # Get operator info
            operator = self._get_text(service_elem, 'lt4:operator') or ""
            operator_code = self._get_text(service_elem, 'lt4:operatorCode') or ""

            # Check cancellation status
            is_cancelled = expected_time == "Cancelled"
            cancel_reason = self._get_text(service_elem, 'lt4:cancelReason')
            delay_reason = self._get_text(service_elem, 'lt4:delayReason')

            # Get calling points
            calling_points = []
            for cp in service_elem.findall('.//lt8:callingPoint', NS):
                cp_name = self._get_text(cp, 'lt8:locationName')
                cp_crs = self._get_text(cp, 'lt8:crs') or ""
                cp_st = self._get_text(cp, 'lt8:st') or ""
                cp_et = self._get_text(cp, 'lt8:et') or "On time"

                if cp_name:
                    calling_points.append(CallingPoint(
                        station_name=cp_name,
                        crs=cp_crs,
                        scheduled_time=cp_st,
                        expected_time=cp_et,
                        is_cancelled=cp_et == "Cancelled"
                    ))

            return TrainService(
                service_id=service_id,
                destination=destination,
                destination_crs=destination_crs,
                scheduled_time=scheduled_time,
                expected_time=expected_time,
                platform=platform,
                operator=operator,
                operator_code=operator_code,
                is_cancelled=is_cancelled,
                cancel_reason=cancel_reason,
                delay_reason=delay_reason,
                calling_points=calling_points
            )

        except Exception as e:
            _LOGGER.warning("Failed to parse service: %s", str(e))
            return None

    def _get_text(self, elem, path: str) -> Optional[str]:
        """Get text content from an element by path."""
        # Try with each namespace prefix
        for prefix in ['lt8', 'lt7', 'lt6', 'lt5', 'lt4', 'lt3', 'lt2', 'lt']:
            adjusted_path = path.replace('lt8:', f'{prefix}:').replace('lt4:', f'{prefix}:').replace('lt5:', f'{prefix}:')
            found = elem.find(adjusted_path, NS)
            if found is not None and found.text:
                return found.text.strip()

        # Try direct path
        found = elem.find(path, NS)
        if found is not None and found.text:
            return found.text.strip()

        return None
