import multiprocessing
import os.path
import datetime
import json
import neat
import logging
import pickle
from packages.backtest import backtest, backtest_csv
from packages.misc import helpers
from packages.tech import trading


def setup(s_date, s_balance, mult_p, neat_type):
    # global declarations
    global start_date, year_lst, currency_pairs, gran, market_reader_obs, \
        profile, min_step, min_step_str, start_balance, end_date, mult_pros, training_type
    # add user input
    # setup vars
    # start_balance = 10000
    # start_date_str = '2022-04-24'
    # mult_pros = False
    start_date_str = s_date
    start_balance = s_balance
    mult_pros = bool(mult_p)
    training_type = neat_type

    # setup neat logger
    helpers.set_logger_neat()
    logger = logging.getLogger('neat')
    logger.info('Setting up for neat backtest')
    # system profile load
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


def runner_multi(genome, config):
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
    # neat vars multiproccesing, one genome
    net = neat.nn.FeedForwardNetwork.create(genome, config)
    # trader setup
    if training_type == 0:
        trader = trading.NeatRawPastTrader(False, currency_pairs, gran, profile['maxrisk'], profile['maxuseday'],
                                           profile['marginrate'], profile['periods'], step_str=min_step_str,
                                           ind_len=ind_len, per_gran_num=per_gran_num)
    else:
        trader = trading.NeatStratPastTrader(False, currency_pairs, gran, profile['maxrisk'], profile['maxuseday'],
                                             profile['marginrate'], profile['periods'], step_str=min_step_str)
    trader.set_balance(start_balance)
    trader.add_market_readers(market_reader_obs)
    genome.fitness = 0

    # trading loop
    running = True
    iteration = 0
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
            inputs = trader.tradeinput(track_year)
            if inputs is False:
                pass
            else:
                # neat
                outputs = net.activate(inputs)
                trader.tradeoutput(track_year, outputs)

        # next step
        track_datetime = track_datetime + min_step
        # kill traders with low balance and add fitness to other traders
        if trader.active_data['balance'] <= 0.05 * start_balance:
            genome.fitness = 0
            return genome.fitness
        else:
            fitness_change = trader.active_data['balance'] - trader.last_pass_balance
            genome.fitness += fitness_change
            trader.last_pass_balance = trader.active_data['balance']

        if track_datetime >= end_date:
            return genome.fitness
            # next generation


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
        if training_type == 0:
            trader = trading.NeatRawPastTrader(False, currency_pairs, gran, profile['maxrisk'], profile['maxuseday'],
                                               profile['marginrate'], profile['periods'], step_str=min_step_str,
                                               ind_len=ind_len, per_gran_num=per_gran_num)
        else:
            trader = trading.NeatStratPastTrader(False, currency_pairs, gran, profile['maxrisk'], profile['maxuseday'],
                                                 profile['marginrate'], profile['periods'], step_str=min_step_str)
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

        # next step
        track_datetime = track_datetime + min_step
        # kill traders with low balance and add fitness to other traders
        for i, t in enumerate(traders):
            if t.active_data['balance'] <= 0.05 * start_balance:
                ge[i].fitness = 0
                traders.pop(i)
                nets.pop(i)
                ge.pop(i)
            else:
                fitness_change = t.active_data['balance'] - t.last_pass_balance
                ge[i].fitness += fitness_change
                t.last_pass_balance = t.active_data['balance']

        if track_datetime >= end_date:
            running = False
            print('\a')
            # next generation


def neat_training(config_path, generations):
    logger = logging.getLogger('neat')
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet,
                                neat.DefaultStagnation, config_path)
    p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    # neat multiprocessing
    if mult_pros:
        mp_run = neat.ParallelEvaluator(multiprocessing.cpu_count(), runner_multi)
        winner = p.run(mp_run.evaluate, generations)
    else:
        winner = p.run(runner, generations)
    logger.info(winner.fitness)
    if training_type == 0:
        path = 'data/neat/winner_raw.pkl'
    if training_type == 1:
        path = 'data/neat/winner_strat.pkl'
    with open(path, 'wb') as f:
        pickle.dump(winner, f)
        f.close()


def main():
    json_data = helpers.load_neat_json()
    if json_data is False:
        print('No saved neat config')
    else:
        use_json = input('Last used neat run settings(y) or use new settings(n): ').lower()
        if use_json == 'n':
            json_data = False
        else:
            s_date = json_data['date']
            s_balance = json_data['balance']
            mult_p = json_data['multi']
            generations = json_data['generations']
            neat_type = json_data['neat_type']
    if json_data is False:
        f = open('data/config.json', 'r')
        profile = json.load(f)
        f.close()
        earliest_year = int(profile['csvstart'])
        earliest_year += 1
        print(f'Earliest year allowed: {earliest_year}')
        s_date = input('Enter start date for back test (YYYY-MM-DD): ')
        s_balance = int(input('Enter starting balance, no decimals: '))
        mult_p = int(input('Multiprocessing (0) for no, (1) for yes: '))
        generations = int(input('Enter number of generations to run: '))
        neat_type = int(input('Enter (0) for neat raw indicator training, or (1) for neat strategy training: '))
        helpers.save_neat_json(s_date, s_balance, mult_p, generations, neat_type)

    setup(s_date, s_balance, mult_p, neat_type)
    if neat_type == 0:
        config_path = '/data/neat_raw_config.txt'
    if neat_type == 1:
        config_path = '/data/neat_strat_config.txt'
    config_path_abs = str(os.getcwd()) + config_path
    neat_training(config_path_abs, generations)


if __name__ == '__main__':
    path_parent = os.path.dirname(os.getcwd())
    os.chdir(path_parent)
    path_parent = os.path.dirname(os.getcwd())
    os.chdir(path_parent)
    main()
