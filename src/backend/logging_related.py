from clonedigger.settings import cfg
import logging
import sys

logger = logging.getLogger()
logger.setLevel(cfg.logger_level)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(cfg.logger_level)
logger.addHandler(handler)
