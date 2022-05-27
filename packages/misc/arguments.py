import os
import sys
import datetime
import json
from packages.misc import helpers
from packages import forex
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

    if arg in ('-n', '--neat'):
        config_path = '/data/neat_raw_config.txt'
        cur_path = str(os.getcwd())
        config_path = cur_path + config_path
        ai_neat.main()
        exit()
    elif arg in ('-r', '--run'):
        return
    elif arg in ('-i', '--neat_inout'):
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

    elif arg in ('-m', '--reset_ms'):
        a = input('Are you sure you want to delete all trading mysql tables (y/n) ')
        a = str(a).lower()
        if a == 'y':
            trade_sql.drop_all_tables()
            trade_sql.setup()
        exit()

    elif arg in ('-b', '--backtest'):
        backtest.main()
        exit()

    elif arg in ('-c', '--setup_gc'):
        name = input('Enter name of config file you would like to setup'
                     ' (Hit enter with no input to save as general config,'
                     ' this is the config file the program will run off of): ')
        if name == '':
            helpers.setup_config()
        else:
            helpers.setup_config(name)
        exit()

    elif arg in ('-s', '--setup'):
        forex.setup()
        print('Setup complete')
        print('Exiting')
        exit()

    else:
        print('Forex-Algotrader')
        print('Help')
        print('(-r) or (--run) or (): To run normally')
        print('(-s) or (--setup): To only setup folders, download market data, and setup mysql tables')
        print('(-m) or (--reset_ms): To reset mysql tables')
        print('(-c) or (--setup_gc): To setup general config.json file')
        print('(-n) or (--neat): To start neat training')
        print('(-i) or (--neat_inout): To return number of inputs and outputs for neat')
        print('(-b) or (--backtest): To run backtest')
        print('(-h) or (--help): Help menu')
        arg = input('Enter (r) to run normally, any other input to exit')
        arg = str(arg).lower()
        if arg == 'r':
            return
        else:
            exit()

