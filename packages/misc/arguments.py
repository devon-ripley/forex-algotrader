import os
import sys
import datetime
import json
from packages.misc import helpers
from packages.output import trade_sql
from packages.backtest import backtest
from packages.tech import ai_neat


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
        print('(ms) To reset mysql tables')
        print('(con) To setup general config.json file')
        print('(neatraw) To start neat raw indicator data training')
        print('(neatrawio) To return number of inputs and outputs for neat raw indicator')
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

    elif arg == 'neatraw':
        config_path = '/data/neat_raw_config.txt'
        cur_path = str(os.getcwd())
        config_path = cur_path + config_path
        ai_neat.main()

    elif arg == 'neatrawio':
        try:
            f = open('data/config.json', 'r')
            profile = json.load(f)
            f.close()
        except FileNotFoundError:
            print('config file not found')
            exit()
        pairs = profile['currencypairs']
        grans = profile['gran']
        print(helpers.num_nodes_rawneat(pairs, grans, 5))

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

    elif arg == 'con':
        name = input('Enter name of config file you would like to setup'
                     ' (Hit enter with no input to save as general config,'
                     ' this is the config file the program will run off of): ')
        if name == '':
            helpers.setup_config()
        else:
            helpers.setup_config(name)
