import sys
from packages import forex
from packages.misc import arguments
from packages.output import notification

arguments.controller(sys.argv)
profile = forex.setup()

try:
    forex.trading_loop(profile)

except:
    notification.send('Crash during trading loop, restarting')
    profile = forex.setup()
    forex.trading_loop(profile)

forex.end_week()
