import datetime
import os
import sys
import logging
import json

# set up folder org if not setup


def folder_setup(currency_pairs, grans):
    for x in currency_pairs:
        try:
            os.makedirs('data/csv/' + x + '/D')
        except FileExistsError:
            pass
        for t in grans:
            try:
                os.makedirs('data/csv/' + x + '/' + t)
            except FileExistsError:
                pass
    try:
        os.makedirs('data/reports')
    except FileExistsError:
        pass
    try:
        os.makedirs('data/neat')
    except FileExistsError:
        pass
    try:
        os.makedirs('data/backtest')
    except FileExistsError:
        pass
    try:
        os.makedirs('data/trade_logic')
    except FileExistsError:
        pass


def set_logger():
    try:
        os.makedirs('log')
    except FileExistsError:
        pass
    logger = logging.getLogger('forexlogger')
    logger.setLevel(logging.INFO)

    logger.propagate = False
    formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
    file_handler = logging.FileHandler('log/main.log')
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    def exception_handle(exc_type, exc_value, exc_traceback):
        logger.exception("Uncaught exception: {0}".format(str(exc_value)))

    # Initiate exception handler
    # uncomment for no terminal output run, error print to file
    #sys.excepthook = exception_handle


def set_logger_backtest():
    try:
        os.makedirs('log')
    except FileExistsError:
        pass
    logger = logging.getLogger('backtest')
    logger.setLevel(logging.INFO)

    logger.propagate = False
    formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
    file_handler = logging.FileHandler('log/backtest.log')
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)


def set_logger_neat():
    try:
        os.makedirs('log')
    except FileExistsError:
        pass
    logger = logging.getLogger('neat')
    logger.setLevel(logging.INFO)

    logger.propagate = False
    formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
    file_handler = logging.FileHandler('log/neat.log')
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)


def get_config():
    # system profile load
    f = open('data/config.json', 'r')
    profile = json.load(f)
    f.close()
    return profile


def setup_config(name='config.json'):
    config_path = 'data/' + name
    res = input(f'Would you like to setup config file, {config_path}, Yes(y)/No(n): ')
    res = res.lower()
    if res == 'y':
        num = 0
        final_num = 17
        config_final = {}
        print('Press enter with no input to pass')
        print(num, '/', final_num)
        config_final['apikey'] = input('Enter oanda apikey: ')
        num += 1
        print(f'{num}/{final_num}')
        config_final['maxrisk'] = input('Enter max risk of total balance in account allowed, '
                                        'example (0.01) for 10%: ')
        num += 1
        print(f'{num}/{final_num}')
        config_final['maxuseday'] = input('Enter max amount of balance to be used in trades, '
                                          'example (0.20) for 20%: ')
        num += 1
        print(f'{num}/{final_num}')
        out = input('Shutdown program on weekend of keep running Yes(y)/No(n) :').lower()
        if out == 'y':
            shut = True
        if out == 'n':
            shut = False
        config_final['wkndshut'] = shut
        num += 1
        print(f'{num}/{final_num}')
        config_final['periods'] = input('Enter candles back to load into temp_test_trade_strategy.py, example (80): ')
        num += 1
        print(f'{num}/{final_num}')
        config_final['currencypairs'] = input('Enter currency pairs to use, '
                                              'example (USD_JPY,EUR_USD) seperated by comma no space: ')
        num += 1
        print(f'{num}/{final_num}')
        config_final['gran'] = input('Enter candle granulation to use, '
                                     'example (M15,H1) separated by comma no space: ')
        num += 1
        print(f'{num}/{final_num}')
        out = input('Use saved neat network with live trading, (y) for yes, (n) for no: ').lower()
        if out == 'y':
            shut = True
        else:
            shut = False
        config_final['neat'] = shut
        num += 1
        print(f'{num}/{final_num}')
        config_final['maxusetrend'] = input('Enter max amount of balance to be used in long term trades, '
                                            'example (0.35) for 35%: ')
        num += 1
        print(f'{num}/{final_num}')
        config_final['marginrate'] = input('Enter margin rate account is set to, example (20) 1:20 rate: ')
        num += 1
        print(f'{num}/{final_num}')
        config_final['csvstart'] = input('Enter start year for market data download, example (2012): ')
        num += 1
        print(f'{num}/{final_num}')
        config_final['mysql'] = {}
        config_final['mysql']['user'] = input('Enter mysql username for program to use: ')
        num += 1
        print(f'{num}/{final_num}')
        config_final['mysql']['password'] = input('Enter password for mysql user: ')
        num += 1
        print(f'{num}/{final_num}')
        config_final['mysql']['database'] = input('Enter mysql database for program to use: ')
        num += 1
        print(f'{num}/{final_num}')
        config_final['notifications'] = {}
        config_final['notifications']['sender_email'] = input('Enter gmail for program to send notifications with: ')
        num += 1
        print(f'{num}/{final_num}')
        config_final['notifications']['sender_email_pass'] = input('Enter password for sending gmail')
        num += 1
        print(f'{num}/{final_num}')
        config_final['notifications']['receive_phone_num'] = input('Enter phone number to send text notifications'
                                                                   ' to with carrier email to sms sufix,'
                                                                   ' example (5551231234@tmomail.net): ')
        num += 1
        print(f'{num}/{final_num}')
        config_final['notifications']['receive_email'] = input('Enter email to have reports sent to: ')
        print('All done! Saving file as ', config_path)
        # save config file
        with open('data/config.json', 'w') as fp:
            json.dump(config_final, fp, indent=4)
    else:
        exit()


def check_config():
    config_path = 'data/config.json'
    file_exists = os.path.exists(config_path)
    if file_exists:
        return
    else:
        setup_config()


def num_nodes_rawneat(pairs, grans, len_ind):
    from packages.tech.trade_check import indicators
    from packages.output import market_csv
    # outputs
    outputs = len(pairs)
    last_year = (datetime.datetime.now() - datetime.timedelta(days=365)).year
    data = market_csv.csv_read_full(pairs[0], grans[0], last_year)
    indicator_dict = indicators(pairs, grans, data)
    indicator_dict = indicator_dict['indicators']
    # inputs
    input_count = 0
    for k in indicator_dict.keys():
        if type(indicator_dict[k]) == dict:
            for under_k in indicator_dict[k].keys():
                input_count += 1
        else:
            input_count += 1

    inputs = input_count * len_ind * len(pairs) * len(grans)

    return {'outputs': outputs, 'inputs': inputs, 'inputs_per_gran': input_count * len_ind}


def num_nodes_stratneat(pairs, grans):
    import trade_strategy
    from packages.output import market_csv
    last_year = (datetime.datetime.now() - datetime.timedelta(days=365)).year
    data = market_csv.csv_read_full(pairs[0], grans[0], last_year)
    one_run_len = len(trade_strategy.trade_strategy(currency_pair=pairs[0], gran=grans[0], data=data))
    overall_len = 0
    for p in pairs:
        for g in grans:
            overall_len += one_run_len
    return {'inputs': overall_len, 'outputs': len(pairs)}



def save_neat_json(s_date, s_balance, mult_p, generations, neat_type):
    path = os.getcwd() + '/data/neat/saved_run.json'
    json_data = {'date': s_date, 'balance': s_balance, 'multi': mult_p,
                 'generations': generations, 'neat_type': neat_type}
    with open(path, 'w') as f:
        json.dump(json_data, f, indent=2)


def load_neat_json():
    path = os.getcwd() + '/data/neat/saved_run.json'
    try:
        with open(path, 'r') as f:
            json_data = json.load(f)
        return json_data
    except FileNotFoundError:
        return False


def save_backtest_json(s_date, s_balance):
    path = os.getcwd() + '/data/backtest/saved_run.json'
    json_data = {'date': s_date, 'balance': s_balance}
    with open(path, 'w') as f:
        json.dump(json_data, f, indent=2)


def load_backtest_json():
    path = os.getcwd() + '/data/backtest/saved_run.json'
    try:
        with open(path, 'r') as f:
            json_data = json.load(f)
        return json_data
    except FileNotFoundError:
        return False
