from settings import logger_level
import logging
import sys

logger = logging.getLogger()
logger.setLevel(logger_level)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logger_level)
logger.addHandler(handler)
