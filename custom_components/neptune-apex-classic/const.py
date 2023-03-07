"""Constants for Neptune Apex Classic integration."""
from datetime import timedelta

DOMAIN = "neptune_apex_classic"
DEFAULT_NAME = "Apex Classic"
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "1234"

# Constants used to access cached data from component setup in the individual sensors
DATA_KEY_CONNECTION = "connection"
DATA_KEY_COORDINATOR = "coordinator"

CONFIG_KEY_SERIAL_NUMBER = "serial-number"

TIME_BETWEEN_UPDATES = timedelta(seconds=10)
