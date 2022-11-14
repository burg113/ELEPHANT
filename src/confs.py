from typing import Final
import logging

APP_NAME:Final = "Elephant"
APP_VERSION:Final = "0.0.1"
APP_URL:Final = "https://github.com/burg113/ELEPHANT"
APP_DEBUG:Final = True
LOG_FILE:Final = "logs.log"
LOG_FORMAT:Final = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL:Final = logging.DEBUG
APP_BASEPATH:Final = ""

CONFIG_ORIGIN_WHITELIST = {
    "campus.kit.edu": {
        "scheme": ["http", "https"],
        "path": ["/sp/webcal/"],
    }
}