import sys
from packages import forex
from packages.misc import arguments

# check run arguments
arguments.controller(sys.argv)
# start program
profile = forex.setup()
forex.trading_loop(profile)
forex.end_week()
