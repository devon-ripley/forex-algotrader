import os.path
import datetime
import json
import neat
import logging
import pickle
from packages.backtest import backtest, backtest_csv
from packages.misc import helpers
from packages.tech import trading


def setup():
    # global declarations
    global start_date, year_lst, currency_pairs, gran, market_reader_obs, \
        profile, min_step, min_step_str, start_balance, end_date
    # add user input
    # setup vars
    start_balance = 10000
    start_date_str = '2011-04-24'

    # setup neat logger
    helpers.set_logger_neat()
    logger = logging.getLogger('neat')
    logger.info('Setting up for neat backtest')
    # system profile load
    if __name__ == '__main__':
        path_parent = os.path.dirname(os.getcwd())
        os.chdir(path_parent)
        path_parent = os.path.dirname(os.getcwd())
        os.chdir(path_parent)
    f = open('data/config.json', 'r')
    profile = json.load(f)
    f.close()
    # load variables
    currency_pairs = profile['currencypairs']
    currency_pairs = list(currency_pairs.split(','))
    gran = profile['gran']
    gran = list(gran.split(','))

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

    end_date = backtest.get_last_date(currency_pairs, gran)
    logger.info(f'Test from {start_date} to {end_date}')
    logger.info(f'Starting Balance of {start_balance}')
    min_step_lst = []
    for x in gran:
        if x[0] == 'M':
            temp_g = int(x.strip('M'))
            min_step_lst.append(datetime.timedelta(minutes=temp_g))
        elif x[0] == 'H':
            temp_g = int(x.strip('H'))
            min_step_lst.append(datetime.timedelta(hours=temp_g))
    min_step = min(min_step_lst)
    min_step_str = backtest.minstr(min_step)

    track_datetime = start_date
    track_year = track_datetime.year


def runner(genomes, config):
    # set up staring vars
    track_datetime = start_date
    track_year = track_datetime.year

    # reset market readers to start
    for year in year_lst:
        for p in currency_pairs:
            for g in gran:
                market_reader_obs[year][p][g].reset()
    # temp length of indicators to pass to neat as inputs
    ind_len = 5
    num_in_out = helpers.num_nodes_rawneat(currency_pairs, gran, ind_len)
    per_gran_num = num_in_out['inputs_per_gran']


    # set up neat vars
    nets = []
    ge = []
    traders = []
    for _, g in genomes:
        # nets setup
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        g.fitness = 0
        ge.append(g)
        # trader setup
        trader = trading.NeatRawPastTrader(False, currency_pairs, gran, profile['maxrisk'], profile['maxuseday'],
                                           profile['marginrate'], profile['periods'], step_str=min_step_str, ind_len=ind_len)
        trader.set_balance(start_balance)
        trader.add_market_readers(market_reader_obs)
        traders.append(trader)

    # trading loop
    running = True
    iteration = 0
    logging.info('Starting Loop')
    while running:
        # start of trading loop
        iteration += 1
        # print(f'{iteration}: {track_datetime.date()}')
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
        # trade if times match with market reader and track_datetime
            for i, t in enumerate(traders):
                inputs = t.tradeinput(track_year)
                if inputs is False:
                    pass
                else:
                    # neat
                    outputs = nets[i].activate(inputs)
                    t.tradeoutput(track_year, outputs)
        # multiprocessing test
            #def neat_run(trade, tk_yr, net):
            #    inputs = trade.tradeinput(tk_yr)
            #    if inputs is False:
            #        return
            #    else:
            #        outputs = net.activate(inputs)
            #        trade.tradeoutput(tk_yr, outputs)
            #processes = []
            #for y, t in enumerate(traders):
            #    info = (t, track_year, nets[y])
            #    pros = Process(target=neat_run, args=info)
            #    pros.start()
            #    processes.append(pros)
            #for pros in processes:
            #    pros.join()


        # next step
        track_datetime = track_datetime + min_step
        # kill traders with low balance and add fitness to other traders
        for i, t in enumerate(traders):
            if t.active_data['balance'] <= 0.05 * start_balance:
                traders.pop(i)
                nets.pop(i)
                ge.pop(i)
            else:
                fitness_change = t.active_data['balance'] - t.last_pass_balance
                ge[i].fitness += fitness_change

        if track_datetime >= end_date:
            running = False
            print('\a')
            # next generation


def raw_indicator_training(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet,
                                neat.DefaultStagnation, config_path)
    p = neat.Population(config)

    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    winner = p.run(runner, 50)
    with open('data/neat/winner_raw.pkl', 'wb') as f:
        pickle.dump(winner, f)
        f.close()


if __name__ == '__main__':
    setup()
    config_path = '/home/devon/Desktop/forex-algotrader/data/neat_raw_config.txt'
    raw_indicator_training(config_path)
