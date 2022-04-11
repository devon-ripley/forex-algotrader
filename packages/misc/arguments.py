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
        print('(s) To reset mysql tables')
        print('(m) To start manual machine learning program')
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

    elif arg == 'm':
        #machine learning
        pass

    elif arg == 's':
        trade_sql.drop_all_tables()
        trade_sql.setup()
        exit()

    elif arg == 'b':
        # system profile load
        f = open('data/config.json', 'r')
        profile = json.load(f)
        f.close()
        earliest_year = int(profile['csvstart'])
        earliest_year += 1
        print('Enter start date for back test (YYYY/MM/DD)')
        print(f'Earliest year allowed: {earliest_year}')
        start_date = input()
        start_balance = int(input('Enter starting balance, no decimals '))
        backtest.setup(start_date, start_balance)
        exit()
