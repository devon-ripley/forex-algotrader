import sys
from packages import forex
from packages.misc import arguments
from packages.misc import helpers
# set up logger
helpers.set_logger()
# check run arguments
arguments.controller(sys.argv)
# start program
while True:
    profile = forex.setup()
    forex.trading_loop(profile)
    forex.end_week(profile)