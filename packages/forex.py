# forex-algotrader
# By Devon Ripley
# v0.6
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
    # check if config file exits, setup if not
    helpers.check_config()
    # system profile load
    f = open('data/config.json', 'r')
    profile = json.load(f)
    f.close()

    # load variables
    apikey = profile['apikey']
    currency_pairs = profile['currencypairs']
    currency_pairs = list(currency_pairs.split(','))
    gran = profile['gran']
    gran = list(gran.split(','))
    csv_start = int(profile['csvstart'])

    # set up folders if needed
    helpers.folder_setup(currency_pairs, gran)
    logger = logging.getLogger('forexlogger')
    # Initial start
    logger.info('forex_algotrader v0.6')
    logger.info('New System Start')
    # check if system time is UTC
    if datetime.datetime.now().strftime('%H:%M') == datetime.datetime.utcnow().strftime('%H:%M'):
        logger.info('System is set to UTC time')
    else:
        logger.critical('System is NOT set to UCT time')
        exit()

    # API connection test
    # MAX LENGTH OF API CALL 500
    oanda_api.account_get_init(apikey)
    ###### MARKET DATA CSV FILE SET UP
    now_year = datetime.datetime.now().year
    # Daily chart setup
    if 'D' in gran:
        for num_cur in range(len(currency_pairs)):
            for x in range((now_year + 1) - csv_start):
                result = market_csv.daily_check(currency_pairs[num_cur], csv_start + x)
                if not result:
                    logger.info(f'Creating csv file for D1, {currency_pairs[num_cur]}, {csv_start + x}')
                    market_csv.daily_setup(apikey, currency_pairs[num_cur], csv_start + x)
                if result:
                    market_csv.daily_current(apikey, currency_pairs[num_cur], csv_start + x)

    # set up csv files starting at csv start year

    for num_cur in range(len(currency_pairs)):
        for x in range(len(gran)):
            if gran[x] == 'D':
                continue
            result = market_csv.past_years_check(apikey, currency_pairs[num_cur], gran[x], csv_start)

    # check if current year data csv file exists
    for x in range(len(currency_pairs)):
        for x_gran in range(len(gran)):
            if gran[x_gran] == 'D':
                continue
            result = market_csv.current_year_check(currency_pairs[x], gran[x_gran])
            if not result:
                logger.info(f'Current year csv file does not exist {currency_pairs[x]}_{gran[x_gran]}')
                logger.info(f'Creating current year csv file for {currency_pairs[x]}_{gran[x_gran]}')
                # ERROR when running on sunday, monday at 00:00 works
                market_csv.current_year_setup(apikey, currency_pairs[x], gran[x_gran])
    # check existing current year csv files if complete, complete them if not
    for x in range(len(currency_pairs)):
        for x_gran in range(len(gran)):
            if gran[x_gran] == 'D':
                continue
            market_csv.current_year_complete(apikey, currency_pairs[x], gran[x_gran])

    # check and setup trade sql
    trade_sql.setup()
    # check if last week's report info is in report csv
    # Do it yuh
    notification.send('System start complete')
    return profile


def trading_loop(profile):
    logger = logging.getLogger('forexlogger')
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
    currency_pairs = profile['currencypairs']
    currency_pairs = list(currency_pairs.split(','))
    gran = profile['gran']
    gran = list(gran.split(','))
    max_use_trend = profile['maxusetrend']
    margin_rate = profile['marginrate']
    periods = profile['periods']
    account_id = profile['account_id']
    neat_run = False
    if 'neat' in profile:
        neat_run = bool(profile['neat'])
    # check hr and day
    loop = True
    logger.info('Running trading loop')

    first_run = True
    trade_wait = 300
    # setup trader object
    if neat_run:
        trader = trading.LiveTraderNeatRaw(True, currency_pairs, gran, max_risk, max_use_day,
                                           margin_rate, periods, apikey, account_id, 5)
    else:
        trader = trading.LiveTrader(True, currency_pairs, gran, max_risk, max_use_day,
                                    margin_rate, periods, apikey, account_id)
    count = 0
    if run is False:
        logger.warning('Markets currently closed, exiting program')
        exit()
    while loop:
        count += 1
        # update market csv
        system_time = now.now()
        current_yr = int(system_time.strftime("%Y"))
        current_hr = int(system_time.strftime("%H"))
        current_day = int(system_time.strftime("%D"))
        for x in range(len(currency_pairs)):
            market_csv.daily_current(apikey, currency_pairs[x], current_yr)
            for x_gran in range(len(gran)):
                if gran[x_gran] == 'D':
                    continue
                market_csv.current_year_complete(apikey, currency_pairs[x], gran[x_gran])
        res = trader.trade(first_run)

        first_run = False
        if res:
            logger.info(f'loop #{count} complete')
            system_time = now.now()
            current_hr = int(system_time.strftime("%H"))
        if not res:
            logger.critical('Error trading loop')
            system_time = now.now()
            current_hr = int(system_time.strftime("%H"))
            # loop = False????
        logger.info(f'sleep {trade_wait} seconds')
        time.sleep(trade_wait)
        # check if week is over
        if current_day == 5 and current_hr == 20:
            loop = False
            trade_sql.close_all_short_term(apikey, account_id)
            logger.info('All short term trades closed, end of week')


def end_week(profile):
    # generate reports
    reports.end_of_week(profile['apikey'], profile['account_id'])
    notification.send_att('End of week report',
                          'data/reports/report_' + str(datetime.datetime.now().year) + '.csv')
    # sleep program
    logging.info('End of week, system sleeping')
    notification.send(message='End of week, system sleep', subject='End of week')
    wkndshut = profile['"wkndshut"']
    if wkndshut:
        exit()
    else:
        week_end = True
        while week_end:
            system_time = now.now()
            current_hr = int(system_time.strftime("%H"))
            current_day = int(system_time.strftime("%w"))
            if current_day == 0 and current_hr == 20:
                week_end = False
