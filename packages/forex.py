# forex trading bot
# By Devon Ripley
# v0.5
# make a function to do all score and advanced math for all single candles!!!!!
# add in long term trades, change system shut down to always running
# add in saving of trade decision making data???
# trend daily adjustment features
# margin limit watch
# trend and daily amount of account limits based of margin limits. safly within amounts, get from account info
# add in report generation???
# system time must be UTC
# imports
from datetime import datetime as now
import datetime

import json
import logging
import time
from packages.oanda_api import oanda_api as oanda_api
from packages.tech import trading
from packages.output import trade_sql, notification, market_csv, reports
from packages.misc import helpers


def setup():
    # logging format
    logging.basicConfig(filename='log/test.log', format='%(asctime)s %(levelname)s:%(message)s', level=logging.INFO)
    # Initial start
    print('FTBv0.5')
    logging.info('New System Start')
    utc_time = datetime.datetime.utcnow()
    system_time = now.now()
    print(utc_time, 'Current UTC Date/Time')
    print(system_time, ' Current System Date/Time')
    print(now.now(), 'Current UNIX: ', time.time())
    # check if system time is UTC
    if True:
        print(now.now(), 'System is set to UTC time')
        logging.info('System is set to UTC time')
    # else:
    #    print(now.now(), '!!!ERROR System is NOT set to UCT time!!!')
    #    logging.critical('System is NOT set to UCT time')
    #    exit()
    # system profile load
    f = open('data/config.json', )
    profile = json.load(f)
    f.close()
    print(now.now(), profile)
    # load variables
    apikey = profile['apikey']
    currency_pairs = profile['currencypairs']
    currency_pairs = list(currency_pairs.split(','))
    gran = profile['gran']
    gran = list(gran.split(','))
    daily_chart = profile['dailychart']
    daily_chart = bool(daily_chart)
    csv_start = int(profile['csvstart'])
    # set up folders if needed
    helpers.folder_setup(currency_pairs, gran)
    # API connection test
    # MAX LENGTH OF API CALL 500
    account_id = oanda_api.account_get_init(apikey)
    ###### MARKET DATA CSV FILE SET UP

    # Daily chart setup
    if daily_chart:
        for num_cur in range(len(currency_pairs)):
            result = market_csv.daily_check(currency_pairs[num_cur])
            if not result:
                print(now.now(), 'Creating csv file for D1', currency_pairs[num_cur])
                market_csv.daily_setup(apikey, currency_pairs[num_cur])
            if result:
                market_csv.daily_current(apikey, currency_pairs[num_cur])

    # set up csv files starting at csv start year

    for num_cur in range(len(currency_pairs)):
        for x in range(len(gran)):
            result = market_csv.past_years_check(apikey, currency_pairs[num_cur], gran[x], csv_start)

    # check if current year data csv file exists
    for x in range(len(currency_pairs)):
        for x_gran in range(len(gran)):
            result = market_csv.current_year_check(currency_pairs[x], gran[x_gran])
            if not result:
                print(now.now(), 'Current year csv file does not exist', currency_pairs[x], gran[x_gran])
                print(now.now(), 'Creating current year csv file for', currency_pairs[x], gran[x_gran])
                logging.debug('Creating current year csv file for ' + currency_pairs[x] + gran[x_gran])
                # ERROR when running on sunday, monday at 00:00 works
                market_csv.current_year_setup(apikey, currency_pairs[x], gran[x_gran])
    # check existing current year csv files if complete, complete them if not
    for x in range(len(currency_pairs)):
        for x_gran in range(len(gran)):
            market_csv.current_year_complete(apikey, currency_pairs[x], gran[x_gran])

    # check and setup trade sql
    trade_sql.setup()
    notification.send('System start complete')
    return profile


def trading_loop(profile):
    # get current day
    run = True
    system_time = now.now()
    current_unix = time.time()
    today_struct = time.localtime(current_unix)
    day = int(time.strftime('%w', today_struct))
    # current hr
    current_hr = int(system_time.strftime("%H"))
    # check if trading open, after sunday 21, before Friday 21
    if day == 6:
        run = False
    if day == 5 and current_hr >= 21:
        run = False
    if day == 0 and current_hr < 21:
        run = False
    # load variables
    apikey = profile['apikey']
    max_risk = profile['maxrisk']
    max_use_day = profile['maxuseday']
    wknd_shut = profile['wkndshut']
    currency_pairs = profile['currencypairs']
    currency_pairs = list(currency_pairs.split(','))
    gran = profile['gran']
    gran = list(gran.split(','))
    max_use_trend = profile['maxusetrend']
    margin_rate = profile['marginrate']
    account_id = oanda_api.account_get_init(apikey)
    while run:
        # check hr and day
        system_time = now.now()
        current_hr = int(system_time.strftime("%H"))
        current_day = int(system_time.strftime("%w"))
        # logging.info('Running trend trade check')
        # print(now.now(), 'Running trend trade check')
        # trading.trend(apikey, account_id, currency_pairs, max_risk, max_use_trend, margin_rate)
        logging.info('Running regular hours trading')
        res = trading.regular(apikey, account_id, currency_pairs, gran, max_risk, max_use_day, margin_rate)
        if res:
            print(now.now(), 'Regular hours trading complete, trades closed')
            logging.info('Regular hours trading complete, trades closed')
            system_time = now.now()
            current_hr = int(system_time.strftime("%H"))
        if not res:
            print(now.now(), '!!!Error in regular hours trading!!!')
            logging.critical('error in regular hours trading')
            system_time = now.now()
            current_hr = int(system_time.strftime("%H"))
        # check if week is over
        if current_day == 5 and current_hr == 20:
            run = False
            trade_sql.close_all_short_term(apikey, account_id)
            print(now.now(), 'All short term trades closed, end of week')
            logging.info('All short term trades closed, end of week')


def end_week():
    # generate reports
    reports.end_of_week()
    notification.send_att('End of week report', 'data/reports/' + str(datetime.datetime.now().date()) + '.csv')
    # safly sleep program
    print(now.now(), 'End of week system sleeping')
    logging.info('End of week, system sleeping')
    notification.send(message='End of week, system sleep', subject='End of week')
    weeknd = True
    while weeknd:
        system_time = now.now()
        current_hr = int(system_time.strftime("%H"))
        current_day = int(system_time.strftime("%w"))
        if current_day == 0 and current_hr == 20:
            weeknd = False
