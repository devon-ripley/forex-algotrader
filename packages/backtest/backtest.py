import datetime
import logging
import os
from packages.output import market_csv
from packages.tech import trading
from packages.backtest import backtest_csv
from packages.misc import helpers
import json
import neat
import pickle
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


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
           market_reader_obs, trader, min_step, min_step_str, end_date, use_neat):
    # set up neat net if needed
    if use_neat == 'raw':
        cur_path = str(os.getcwd())
        config_path = cur_path + '/data/neat_raw_config.txt'
        pickle_load = cur_path + '/data/neat/winner_raw.pkl'
        config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet,
                                    neat.DefaultStagnation, config_path)
        with open(pickle_load, "rb") as f:
            genome = pickle.load(f)
        net = neat.nn.FeedForwardNetwork.create(genome, config)
    elif use_neat == 'strat':
        cur_path = str(os.getcwd())
        config_path = cur_path + '/data/neat_strat_config.txt'
        pickle_load = cur_path + '/data/neat/winner_strat.pkl'
        config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet,
                                    neat.DefaultStagnation, config_path)
        with open(pickle_load, "rb") as f:
            genome = pickle.load(f)
        net = neat.nn.FeedForwardNetwork.create(genome, config)
    else:
        net = False
    logger = logging.getLogger('backtest')
    starting_balance = trader.active_data['balance']

    logger.info(f'Running backtest, start: {track_datetime}, end: {end_date}...')
    running = True
    iteration = 0
    top_balance = starting_balance
    balance_list = []
    dates_list = []
    while running:
        iteration += 1
        # print(track_datetime)
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
            if use_neat == 'raw' or use_neat == 'strat':
                if market_reader_obs[track_year][currency_pairs[0]][min_step_str].go:
                    # trade if times match with market reader and track_datetime
                    inputs = trader.tradeinput(track_year)
                    if inputs is False:
                        pass
                    else:
                        # neat
                        outputs = net.activate(inputs)
                        trader.tradeoutput(track_year, outputs)
            else:
                trader.trade_past(track_year, track_datetime)
        # sell trades end of week
        if market_reader_obs[track_year][currency_pairs[0]][min_step_str].go is False:
            trader.sell_all(track_year)
        # next step
        last_day = track_datetime.day
        track_datetime = track_datetime + min_step
        if last_day < track_datetime.day:
            balance_list.append(trader.active_data['balance'])
            dates_list.append(track_datetime)
        if trader.active_data['balance'] > top_balance:
            top_balance = trader.active_data['balance']
        if trader.active_data['balance'] <= 0.05 * starting_balance:
            logger.warning('Balance at or under 5% of start amount')
            logger.warning(f'Backtest ended early! {track_datetime}')
            logger.info(f'Total number of trades: {trader.active_data["total_trades"]}')
            logger.info(f'Highest balance during backtest: {top_balance}')
            running = False
        if track_datetime >= end_date:
            logger.info('Backtest complete!')
            running = False
            logger.info(f'Balance: {trader.active_data["balance"]}')
            logger.info(f'Total profit: {trader.active_data["balance"] - starting_balance}')
            logger.info(f'Total number of trades: {trader.active_data["total_trades"]}')
            logger.info(f'Highest balance during backtest: {top_balance}')
            # end of run
    return balance_list, dates_list, trader.all_trades_info


def setup(start_date_str, start_balance, use_neat, chart):
    # setup backtest logger
    helpers.set_logger_backtest()
    logger = logging.getLogger('backtest')
    logger.info(f'Start balance: {start_balance}, Use_neat: {use_neat}')
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
    end_date = get_last_date(currency_pairs, gran)
    current_year = end_date.year
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
    if use_neat == 'raw':
        # temp length of indicators to pass to neat as inputs
        ind_len = 5
        num_in_out = helpers.num_nodes_rawneat(currency_pairs, gran, ind_len)
        per_gran_num = num_in_out['inputs_per_gran']
        trader = trading.NeatRawPastTrader(False, currency_pairs, gran, max_risk, max_use_day,
                                           margin_rate, periods, step_str=min_step_str, ind_len=ind_len,
                                           per_gran_num=per_gran_num)
    elif use_neat == 'strat':
        num = helpers.num_nodes_stratneat(currency_pairs, gran)
        per_gran = num['inputs_per_gran']
        trader = trading.NeatStratPastTrader(False, currency_pairs, gran, profile['maxrisk'], profile['maxuseday'],
                                             profile['marginrate'], profile['periods'],
                                             step_str=min_step_str, per_gran_num=per_gran)
    else:
        trader = trading.PastTrader(False, currency_pairs, gran, max_risk, max_use_day,
                                    margin_rate, periods, step_str=min_step_str)
    trader.active_data['balance'] = start_balance
    trader.add_market_readers(market_reader_obs)
    track_datetime = start_date
    track_year = track_datetime.year

    balance_list, dates, all_trades = runner(track_datetime, track_year, currency_pairs, gran, market_reader_obs,
                          trader, min_step, min_step_str, end_date, use_neat)

    backtest_csv.save_trade_data(all_trades)
    logger.info('Saved backtest trade info as backtest_trades.csv')

    if chart:
        inter = round(len(dates) * 0.1)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=inter))
        plt.plot(dates, balance_list)
        plt.gcf().autofmt_xdate()
        logger.info(f'Saved chart as backtest_chart.pdf')
        plt.savefig('backtest_chart.pdf')
        plt.show()


def main():
    # check past run config file
    json_data = helpers.load_backtest_json()
    if json_data is False:
        print('No saved backtest config')
    else:
        use_json = input('Last used backtest settings(y) or use new settings(n): ').lower()
        if use_json == 'n':
            json_data = False
        else:
            start_date = json_data['date']
            start_balance = json_data['balance']
            use_neat = json_data['use_neat']
            chart = json_data['chart']
    if json_data is False:
        # system profile load
        f = open('data/config.json', 'r')
        profile = json.load(f)
        f.close()
        earliest_year = int(profile['csvstart'])
        earliest_year += 1
        print(f'Earliest year allowed: {earliest_year}')
        start_date = input('Enter start date for back test (YYYY-MM-DD): ')
        start_balance = int(input('Enter starting balance, no decimals: '))
        use_neat = input(
            'Run backtest with saved neat winner? (r), Raw indicators. (s), Strategy. (n), No neat: ').lower()
        if use_neat == 'r':
            use_neat = 'raw'
        elif use_neat == 's':
            use_neat = 'strat'
        else:
            use_neat = False
        chart_in = input('Display chart of balance throughout backtest (y) Yes, (n) No: ').lower()
        if chart_in == 'y':
            chart = True
        else:
            chart = False
        helpers.save_backtest_json(start_date, start_balance, use_neat, chart)
    setup(start_date, start_balance, use_neat, chart)


if __name__ == '__main__':
    path_parent = os.path.dirname(os.getcwd())
    os.chdir(path_parent)
    path_parent = os.path.dirname(os.getcwd())
    os.chdir(path_parent)
    main()
