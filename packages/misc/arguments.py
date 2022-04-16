import sys
import datetime
import json
from packages.misc import weights_json_gen
from packages.output import trade_sql
from packages.backtest import backtest


def controller(arg):
    # argument handling
    if len(arg) > 2:
        print(datetime.datetime.now(), 'ERROR only one argument is allowed')
        exit()
    elif len(arg) == 1:
        return

    arg = str(arg[-1]).lower()
    if arg == 'h':
        print('Help')
        print('(r) or ()To run normally')
        print('(w) To reset weights.json file')
        print('(ms) To reset mysql tables')
        print('(ml) To start manual machine learning program')
        print('(b) To run backtest')
        print('(h), Help menu')
        arg = input('Enter (x) to exit or any other letter to run')
        arg = str(arg).lower()
        if arg == 'x':
            exit()

        elif arg == 'r':
            return
        else:
            pass

    if arg == 'w':
        weights_json_gen.run()
        exit()

    elif arg == 'ml':
        #machine learning
        pass

    elif arg == 'ms':
        a = input('Are you sure you want to delete all trading mysql tables (y/n) ')
        a = str(a).lower()
        if a == 'y':
            trade_sql.drop_all_tables()
            trade_sql.setup()
            exit()
        else:
            exit()

    elif arg == 'b':
        # system profile load
        f = open('data/config.json', 'r')
        profile = json.load(f)
        f.close()
        earliest_year = int(profile['csvstart'])
        earliest_year += 1
        print(f'Earliest year allowed: {earliest_year}')
        start_date = input('Enter start date for back test (YYYY-MM-DD): ')
        start_balance = int(input('Enter starting balance, no decimals: $'))
        backtest.setup(start_date, start_balance)
        exit()
