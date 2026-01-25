# Changelog

## 2.0.6

- Fix: OptionsFlow constructor (don't pass config_entry, HA provides it)

## 2.0.5

- Fix: Force clean integration install (removes old cached files)
- Integration version: 2.2.1

## 2.0.4

- Add integration icon (amber train logo)

## 2.0.3

- Fix: Encode SOAP request as UTF-8 bytes for aiohttp (fixes 500 error)

## 2.0.2

- Fix: Use async API method in config flow (fixes "unknown" error)
- Fix: Add translations/en.json for proper UI labels
- Integration version: 2.2.0

## 2.0.1

- Fix: Add `map: config:rw` to allow add-on to write integration files to /config

## 2.0.0

**Major update: Bundled Home Assistant Integration**

- Auto-installs UK Train Departures integration on add-on startup
- New sensor entities for automations:
  - `sensor.departures_from_xxx_departure_1/2/3` - Next departures
  - `sensor.departures_from_xxx_0645_train` - Watched train by time
  - `binary_sensor.xxx_0645_train_delayed` - Is train delayed?
  - `binary_sensor.xxx_0645_train_cancelled` - Is train cancelled?
- Configure up to 3 watched trains for commute tracking
- All sensors include: `summary`, `is_delayed`, `delay_minutes`, `expected_time`
- After add-on starts, restart HA and add integration via Settings > Integrations

## 1.4.0

- Fix API calls to use correct base URL from ingress path
- Remove problematic base tag from HTML

## 1.3.0

- Fix static files and API paths for Home Assistant ingress
- Use relative URLs for CSS, JS, and API calls

## 1.2.0

- Switch to simpler Python base image without s6-overlay
- Fix container startup issues

## 1.1.0

- Fix s6-overlay service structure for Home Assistant
- Use hassio-addons base image with s6-overlay v3

## 1.0.0

- Initial release
- Live UK train departure board display
- Authentic station board styling with dot matrix font
- Support for destination filtering (show trains calling at specific stations)
- Configuration via Home Assistant Add-on options
- Ingress support for seamless integration
