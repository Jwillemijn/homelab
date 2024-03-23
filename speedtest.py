import subprocess
import json
import time
import logging
from logging.handlers import RotatingFileHandler
from prometheus_client import start_http_server, Gauge
from http.server import BaseHTTPRequestHandler, HTTPServer

PROMETHEUS_PORT = 8000

ping_metric = Gauge('ping_latency_ms', 'Ping latency in milliseconds')
download_metric = Gauge('download_speed_mbps', 'Download speed in Mbps')
upload_metric = Gauge('upload_speed_mbps', 'Upload speed in Mbps')

def configure_logging():
    logger = logging.getLogger("speedtest_logger")
    logger.setLevel(logging.INFO)

    log_file = "/var/log/speedtest_runtime.log"
    handler = RotatingFileHandler(log_file, maxBytes=200*1024*1024, backupCount=2)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger

def run_speed_test():
    # Run speedtest-cli command and capture the output
    output = subprocess.check_output(["speedtest", "--secure","--json"]).decode("utf-8")

    # Parse the JSON output to get the speed test results
    results = json.loads(output)

    ping = results["ping"]
    download = round(results["download"] / 1_000_000, 2)  # Convert to Mbps and round to 2 decimals
    upload = round(results["upload"] / 1_000_000, 2)  # Convert to Mbps and round to 2 decimals
    
    # Set Prometheus metrics
    ping_metric.set(ping)
    download_metric.set(download)
    upload_metric.set(upload)

    return ping, download, upload

def main():
    logger = configure_logging()

    # Start Prometheus HTTP server
    start_http_server(PROMETHEUS_PORT)

    try:
        while True:
            start_time = time.time()
            ping, download, upload = run_speed_test()
            end_time = time.time()
            total_time = end_time - start_time
            logger.info(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}, Script runtime: {total_time:.2f} seconds")
            time.sleep(300)  # Run speed test every 5 minutes

    except Exception as e:
        logger.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
