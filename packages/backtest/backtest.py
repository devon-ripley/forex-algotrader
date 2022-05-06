import datetime
import itertools
import logging
import os
import sys
import time
import copy
from packages.output import market_csv
from packages.tech import trading
from packages.backtest import backtest_csv
from packages.misc import helpers
import json


def minstr(min_step):
    days = min_step.days
    if days != 0:
        return 'D'
    else:
        hour = min_step.seconds / 3600
        if hour >= 1:
            return 'H' + str(int(hour))
        else:
            minutes = min_step.seconds / 60
            return 'M' + str(int(minutes))


def get_last_date(pairs, grans):
    current_year = datetime.datetime.now().year
    data = market_csv.csv_read_recent(pairs[0], grans[0], current_year)
    last_date = data['date'][-1]
    end = last_date - datetime.timedelta(days=1)
    return end


def runner(track_datetime, track_year, currency_pairs, gran,
           market_reader_obs, trader, min_step, min_step_str, end_date):
    logger = logging.getLogger('backtest')
    starting_balance = trader.active_data['balance']

    logger.info(f'Running backtest, start: {track_datetime}, end: {end_date}...')
    running = True
    iteration = 0
    while running:
        iteration += 1
        new_year_once = True
        # market reader index check
        for p in currency_pairs:
            for g in gran:
                m_ob = market_reader_obs[track_year][p][g]
                if m_ob.start_index > m_ob.total_length:
                    if new_year_once:
                        track_year += 1
                        new_year_once = False
                    m_ob = market_reader_obs[track_year][p][g]
                m_ob.go_check(track_datetime)
        if market_reader_obs[track_year][currency_pairs[0]][min_step_str].go:
            trader.trade_past(track_year, track_datetime)
        # next step
        track_datetime = track_datetime + min_step
        if trader.active_data['balance'] <= 0.05 * starting_balance:
            logger.warning('Backtest ended early!')
            logger.warning('Balance at or under 5% of start amount')
            running = False
        if track_datetime >= end_date:
            logger.info('Backtest complete!')
            running = False
            logger.info(f'Balance: {trader.active_data["balance"]}')
            logger.info(f'Total profit: {trader.active_data["balance"] - starting_balance}')
            logger.info(f'Total number of trades: {trader.active_data["total_trades"]}')
            # end of run


def setup(start_date_str='2018-05-15', start_balance=10000, neat_training_run=False, number_traders=1):
    # setup backtest logger
    helpers.set_logger_backtest()
    logger = logging.getLogger('backtest')
    # system profile load
    f = open('data/config.json', 'r')
    profile = json.load(f)
    f.close()
    # weights?
    weights = 0
    # load variables
    max_risk = profile['maxrisk']
    max_use_day = profile['maxuseday']
    currency_pairs = profile['currencypairs']
    currency_pairs = list(currency_pairs.split(','))
    gran = profile['gran']
    gran = list(gran.split(','))
    max_use_trend = profile['maxusetrend']
    margin_rate = profile['marginrate']
    periods = profile['periods']

    start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d')
    year = start_date.year - 1
    start_year = year + 1
    market_reader_obs = {}
    year_lst = []
    current_year = datetime.datetime.now().year
    while year <= current_year:
        year_lst.append(year)
        year += 1
    for x in year_lst:
        market_reader_obs[x] = {}
        for pair in currency_pairs:
            market_reader_obs[x][pair] = {}
            for g in gran:
                logger.info(f'Loading market data for {x}, {pair}, {g}...')
                market_reader_obs[x][pair][g] = (backtest_csv.BacktestMarketReader(x, pair, g, start_date, False))
                if x == start_date.year:
                    market_reader_obs[x][pair][g] = (backtest_csv.BacktestMarketReader(x, pair, g, start_date, True))

    end_date = get_last_date(currency_pairs, gran)

    min_step_lst = []
    for x in gran:
        if x[0] == 'M':
            temp_g = int(x.strip('M'))
            min_step_lst.append(datetime.timedelta(minutes=temp_g))
        elif x[0] == 'H':
            temp_g = int(x.strip('H'))
            min_step_lst.append(datetime.timedelta(hours=temp_g))
    min_step = min(min_step_lst)
    min_step_str = minstr(min_step)
    if neat_training_run:
        traders = []
        for x in range(number_traders):
            trader = trading.NeatRawPastTrader(False, currency_pairs, gran, max_risk, max_use_day,
                                           margin_rate, periods, step_str=min_step_str)
            trader.active_data['balance'] = start_balance
            trader.add_market_readers(market_reader_obs)
            traders.append(trader)
    else:
        trader = trading.PastTrader(False, currency_pairs, gran, max_risk, max_use_day,
                                    margin_rate, periods, step_str=min_step_str)
        trader.active_data['balance'] = start_balance
        trader.add_market_readers(market_reader_obs)
    track_datetime = start_date
    track_year = track_datetime.year
    if neat_training_run:
        return [track_datetime, track_year, currency_pairs, gran, market_reader_obs,
           traders, min_step, min_step_str, end_date, year_lst]
    else:
        runner(track_datetime, track_year, currency_pairs, gran, market_reader_obs,
           trader, min_step, min_step_str, end_date)


if __name__ == '__main__':
    # change path out one
    path_parent = os.path.dirname(os.getcwd())
    os.chdir(path_parent)
    path_parent = os.path.dirname(os.getcwd())
    os.chdir(path_parent)
    # system profile load
    f = open('data/config.json', 'r')
    profile = json.load(f)
    f.close()
    earliest_year = int(profile['csvstart'])
    earliest_year += 1
    print(f'Earliest year allowed: {earliest_year}')
    start_date = input('Enter start date for back test (YYYY-MM-DD): ')
    start_balance = int(input('Enter starting balance, no decimals: '))
    setup(start_date, start_balance)
