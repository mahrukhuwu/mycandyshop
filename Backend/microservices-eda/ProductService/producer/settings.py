from starlette.config import Config
from starlette.datastructures import Secret

try:
    config = Config(".env")
except FileNotFoundError:
    config = Config()

BOOTSTRAP_SERVER = config("KAFKA_SERVER", cast=str)
KAFKA_ORDER_TOPIC = config("KAFKA_ORDER_TOPIC", cast=str)