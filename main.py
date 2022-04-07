import logging
import sys
from packages import forex
from packages.misc import arguments, helpers
from packages.output import notification
helpers.set_logger()
logger = logging.getLogger('forexlogger')
# check run arguments
arguments.controller(sys.argv)
# start program
profile = forex.setup()

try:
    forex.trading_loop(profile)

except:
    notification.send('Crash during trading loop, restarting')
    logger.info('Crash during trading loop, restarting')
    profile = forex.setup()
    forex.trading_loop(profile)

forex.end_week()
