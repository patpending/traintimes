ARG BUILD_FROM
FROM $BUILD_FROM

# Install Python dependencies
RUN pip3 install --no-cache-dir flask requests aiohttp

# Copy application files
WORKDIR /app
COPY app.py /app/
COPY darwin_api.py /app/
COPY static /app/static/
COPY templates /app/templates/
COPY run.sh /app/

# Copy custom integration for auto-install
COPY custom_components /app/custom_components/

RUN chmod +x /app/run.sh

CMD ["/app/run.sh"]
