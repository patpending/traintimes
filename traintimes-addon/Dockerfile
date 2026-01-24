ARG BUILD_FROM
FROM $BUILD_FROM

# Install Python dependencies
RUN pip3 install --no-cache-dir flask requests

# Copy application files
WORKDIR /app
COPY app.py /app/
COPY darwin_api.py /app/
COPY static /app/static/
COPY templates /app/templates/
COPY run.sh /app/

RUN chmod +x /app/run.sh

CMD ["/app/run.sh"]
