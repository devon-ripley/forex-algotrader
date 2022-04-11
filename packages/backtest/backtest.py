import datetime
from packages.tech import trading
from packages.backtest import backtest_csv
import json


def runner(track_datetime, track_year, currency_pairs, gran, market_reader_obs, trader, min_step, end_date):
    running = True
    iteration = 0

    while running:
        iteration += 1
        print(iteration, ': ', track_datetime)
        # market reader index check
        for p in currency_pairs:
            for g in gran:
                m_ob = market_reader_obs[track_year][p][g]
                if m_ob.start_index > m_ob.total_length:
                    track_year = track_year + 1
                    m_ob = market_reader_obs[track_year][p][g]
                m_ob.go_check(track_datetime)
        if market_reader_obs[track_year][currency_pairs[0]]['M1'].go:
            trader.trade_past(track_year, track_datetime)
        # next step
        track_datetime = track_datetime + min_step
        if trader.active_data['balance'] <= 0:
            print('Balance under or at 0')
            print('datetime', track_datetime)
            running = False
        if track_datetime >= end_date:
            print('Balance: ', trader.active_data['balance'])
            running = False
            # end of run


def setup(start_date_str='2018-05-15', start_balance=10000):
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
    account_dict = {'balance': start_balance, 'max_risk': max_risk,
                    'max_use_day': max_use_day, 'margin_rate': margin_rate, 'active_pairs': [], 'active_trades': []}
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
                market_reader_obs[x][pair][g] = (backtest_csv.BacktestMarketReader(x, pair, g, start_date))

    end_date = datetime.datetime(2022, 3, 22)
    trader = trading.PastTrader(False, currency_pairs, gran, max_risk, max_use_day, margin_rate, weights)
    trader.active_data['balance'] = start_balance
    trader.add_market_readers(market_reader_obs)
    track_datetime = start_date
    min_step_lst = []
    for x in gran:
        if x[0] == 'M':
            temp_g = int(x.strip('M'))
            min_step_lst.append(datetime.timedelta(minutes=temp_g))
        elif x[0] == 'H':
            temp_g = int(x.strip('H'))
            min_step_lst.append(datetime.timedelta(hours=temp_g))
    min_step = min(min_step_lst)
    track_year = track_datetime.year
    runner(track_datetime, track_year, currency_pairs, gran, market_reader_obs, trader, min_step, end_date)


if __name__ == '__main__':
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
    setup(start_date, start_balance)
