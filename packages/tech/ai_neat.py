import neat
from packages.backtest import backtest
from packages.misc import helpers


def runner(track_datetime, track_year, currency_pairs, gran,
           market_reader_obs, traders, min_step, min_step_str, end_date, yr_lst):

    starting_balance = traders[0].active_data['balance']
    start_year = track_year
    start_datetime = track_datetime
    ind_len = 5
    num_in_out = helpers.num_nodes_rawneat(currency_pairs, gran, ind_len)
    per_gran_num = num_in_out['inputs_per_gran']
    running = True
    iteration = 0
    reset = False
    while running:
        # reset objects
        if reset:
            track_year = start_year
            track_datetime = start_datetime
            iteration = 0
            for t in traders:
                t.reset(starting_balance)
            for year in yr_lst:
                for p in currency_pairs:
                    for g in gran:
                        market_reader_obs[year][p][g].reset()
            reset = False
        # start of trading loop
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
        # trade if times match with market reader and track_datetime
            for t in traders:
                inputs = t.tradeinput(track_year, per_gran_num, ind_len)
                if inputs is False:
                    continue
                else:
                    # neat
                    outputs = [0, 1, 0]
                    # t.NEATout(outputs)
                    pass
        # next step
        track_datetime = track_datetime + min_step
        # kill traders with low balance and add fitness to other traders
        for t in traders:
            if t.active_data['balance'] <= 0.05 * starting_balance:
                # kill t
                pass
            else:
                fitness_change = t.active_data['balance'] - t.last_pass_balance

        if track_datetime >= end_date:
            reset = True
            # next generation?


def raw_indicator_training():
    rv = backtest.setup(neat_training_run=True)
    runner(rv[0], rv[1], rv[2], rv[3], rv[4], rv[5], rv[6], rv[7], rv[8], rv[9])



if __name__ == 'main':
    raw_indicator_training()