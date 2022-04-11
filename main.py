import logging
import sys
from packages import forex
from packages.misc import arguments
from packages.output import notification
import logging
# check run arguments
arguments.controller(sys.argv)
# start program
profile = forex.setup()
logger = logging.getLogger('forexlogger')

forex.trading_loop(profile)

forex.end_week()
