import os.path
import datetime
import json
import neat
from packages.backtest import backtest, backtest_csv
from packages.misc import helpers
from packages.tech import trading


# setup vars
start_balance = 10000
start_date_str = '2022-04-24'
# setup backtest logger
#helpers.set_logger_backtest()
#logger = logging.getLogger('backtest')
# system profile load
path_parent = os.path.dirname(os.getcwd())
os.chdir(path_parent)
path_parent = os.path.dirname(os.getcwd())
os.chdir(path_parent)
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
            print(f'Loading market data for {x}, {pair}, {g}...')
            market_reader_obs[x][pair][g] = (backtest_csv.BacktestMarketReader(x, pair, g, start_date, False))
            if x == start_date.year:
                market_reader_obs[x][pair][g] = (backtest_csv.BacktestMarketReader(x, pair, g, start_date, True))

end_date = backtest.get_last_date(currency_pairs, gran)

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
        trader = trading.NeatRawPastTrader(False, currency_pairs, gran, max_risk, max_use_day,
                                           margin_rate, periods, step_str=min_step_str)
        trader.set_balance(start_balance)
        trader.add_market_readers(market_reader_obs)
        traders.append(trader)

    # trading loop
    running = True
    iteration = 0
    while running:
        # start of trading loop
        iteration += 1
        print(f'{iteration}: {track_datetime}')
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
                inputs = t.tradeinput(track_year, per_gran_num, ind_len)
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
                traders.pop(i)
                nets.pop(i)
                ge.pop(i)
            else:
                fitness_change = t.active_data['balance'] - t.last_pass_balance
                ge[i].fitness += fitness_change

        if track_datetime >= end_date:
            running = False
            # next generation?


def raw_indicator_training(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet,
                                neat.DefaultStagnation, config_path)
    p = neat.Population(config)

    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    winner = p.run(runner, 50)
    print(winner)


config_path = '/home/devon/Desktop/forex-algotrader/data/neat_raw_config.txt'
raw_indicator_training(config_path)