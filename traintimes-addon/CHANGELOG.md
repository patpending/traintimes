# Changelog

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
