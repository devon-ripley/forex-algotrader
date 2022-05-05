import neat
from packages.backtest import backtest


def runner(track_datetime, track_year, currency_pairs, gran,
           market_reader_obs, traders, min_step, min_step_str, end_date):

    # RESET BALANCE AND MARKET READERS WITH NEW GENERATIONS
    starting_balance = traders[0].active_data['balance']
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

            for t in traders:
                inputs = t.tradeinput(track_year)
                if inputs is False:
                    continue
                else:
###################################################### Integration with neat
                    # outputs = neatstuff(inputs)
                    # t.NEATout(outputs)
                    pass
        # next step
        track_datetime = track_datetime + min_step
        for t in traders:
            if t.active_data['balance'] <= 0.05 * starting_balance:
                # kill t
                pass
            else:
                fitness_change = t.active_data['balance'] - t.last_pass_balance

        if track_datetime >= end_date:
            running = False
            # next generation?


def raw_indicator_training():
    rv = backtest.setup(neat_training_run=True)
    runner(rv[0], rv[1], rv[2], rv[3], rv[4], rv[5], rv[6], rv[7], rv[8])



if __name__ == 'main':
    raw_indicator_training()