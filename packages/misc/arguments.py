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
        print('(neat) To start neat training')
        print('(neatio) To return number of inputs and outputs for neat')
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

    elif arg == 'neat':
        config_path = '/data/neat_raw_config.txt'
        cur_path = str(os.getcwd())
        config_path = cur_path + config_path
        ai_neat.main()
        exit()
    elif arg == 'neatio':
        try:
            f = open('data/config.json', 'r')
            profile = json.load(f)
            f.close()
        except FileNotFoundError:
            print('config file not found')
            exit()
        pairs = profile['currencypairs']
        pairs = list(pairs.split(','))
        grans = profile['gran']
        grans = list(grans.split(','))
        ur_in = int(input('Enter (0) for raw indicator neat, (1) for strategy neat'))
        if ur_in == 0:
            print(helpers.num_nodes_rawneat(pairs, grans, 5))
        if ur_in == 1:
            print(helpers.num_nodes_stratneat(pairs, grans))
        exit()
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
        backtest.main()
        exit()

    elif arg == 'con':
        name = input('Enter name of config file you would like to setup'
                     ' (Hit enter with no input to save as general config,'
                     ' this is the config file the program will run off of): ')
        if name == '':
            helpers.setup_config()
        else:
            helpers.setup_config(name)
