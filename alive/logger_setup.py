# setup_logger.py
import logging
# logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('')
logger.setLevel(logging.DEBUG)


# create file handler which logs even debug messages
fh = logging.FileHandler('alive.log')
fh.setLevel(logging.DEBUG)

# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)


# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s %(levelname)-5s %(name)s.%(funcName)s() %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)
