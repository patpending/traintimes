ARG BUILD_FROM=ghcr.io/hassio-addons/base:15.0.8
FROM $BUILD_FROM

# Install Python and dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    py3-flask \
    py3-requests

# Copy application files
COPY app.py /app/
COPY darwin_api.py /app/
COPY static /app/static/
COPY templates /app/templates/

# Copy s6-overlay service
COPY rootfs /
