ARG BUILD_FROM
FROM $BUILD_FROM

# Install Python and dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    py3-flask \
    py3-requests

# Copy run script
COPY rootfs /

# Copy application files
COPY app.py /app/
COPY darwin_api.py /app/
COPY static /app/static/
COPY templates /app/templates/

WORKDIR /app

# Make run script executable
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
