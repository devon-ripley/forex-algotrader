from packages.output import market_csv
from packages.tech import candle
import json
import numpy as np


def current_trend(prices):
    combined = []
    stripped = []
    for x in range(len(prices)):
        combined.append([prices[x][2], (prices[x][6] + prices[x][3]) / 2])
        stripped.append((prices[x][6] + prices[x][3]) / 2)

    final = []
    recent_start = combined[0][1]
    local_limits = np.diff(np.sign(np.diff(stripped)))
    local_limits = np.insert(local_limits, 0, 1)
    local_limits = np.append(local_limits, 3)
    candles = 0
    for x in range(len(combined)):
        limit_point = local_limits[x]
        if limit_point == 1:
            pass
        elif limit_point == -2:
            # peak
            change = (combined[x][1] - recent_start) / recent_start * 100
            final.append({'type': 'peak', 'date': combined[x][0], 'price': combined[x][1],
                          'candles': candles, 'increase': change})
            candles = 0
            recent_start = combined[x][1]
        elif limit_point == 2:
            # valley
            change = (combined[x][1] - recent_start) / recent_start * 100
            final.append({'type': 'valley', 'date': combined[x][0], 'price': combined[x][1],
                          'candles': candles, 'increase': change})
            candles = 0
            recent_start = combined[x][1]
        elif limit_point == 0:
            candles += 1
        elif limit_point == 3:
            # end
            change = (combined[x][1] - recent_start) / recent_start * 100
            final.append({'type': 'end', 'date': combined[x][0], 'price': combined[x][1],
                          'candles': candles, 'increase': change})

    overview_dict = {'candles': final}
    # find range of prices
    range_list = []
    for x in combined:
        range_list.append(x[1])
    overview_dict['range'] = max(range_list) - min(range_list)
    # increase average
    unit_inc = 0.0
    for x in final:
        unit_temp = x['increase']
        unit_inc += unit_temp
    increase_average = unit_inc / len(final)
    overview_dict['increase_average'] = increase_average
    # find increase
    start = combined[0][1]
    end = combined[-1][1]
    increase = (end - start) / start * 100
    overview_dict['increase_overall'] = increase
    return overview_dict


class TradeCheck():
    def __init__(self, currency_pair, gran):
        self.currency_pair = currency_pair
        self.gran = gran
        # get weights and ratios for just current currency_pair and gran
        f = open('data/weights.json', 'r')
        weights = json.load(f)
        f.close()
        weights = weights['currency_pairs'][currency_pair][gran]
        self.weights = weights
        # candle vars
        self.wait_confirmation = []
        self.trend_list = []
    def indicator_setup(self):
        pass

    def candle_check(self, data, periods):
        # set up candle single weights
        candle_single_dict_weights = self.weights['candle_single']
        # check local trend
        self.trend_list = current_trend(data)
        # check for past confirmations needed
        price = data[-1]
        current_date = price[2]
        con_result = []
        for x in self.wait_confirmation:
            if current_date > x['date']:
                # check if candle is confirmed
                if x['direction'] == 1:
                    # check for going up
                    if price[3] - price[6] < 0:
                        x['conformation'] = False
                        con_result.append(x)
                else:
                    # check for going down
                    if price[3] - price[6] > 0:
                        x['conformation'] = False

        if self.trend_list['candles'][-1]['increase'] > 0:
            direction = 0
        else:
            direction = 1
        # compare candles on latest complete candle
        results = candle.single_candle(data, candle_single_dict_weights, direction, self.gran, self.currency_pair)
        if not results:
            return None
        for x in results:
            trend_list_mot = dict(self.trend_list)
            last = trend_list_mot['candles'][-1]
            del trend_list_mot['candles']
            trend_list_mot['candle'] = last
            x['last_trend'] = trend_list_mot
            if x['execute']:
                if x['conformation']:
                    self.wait_confirmation.append(x)
        if con_result:
            results = results + con_result
        else:
            pass
        if results:
            return results
        if not results:
            pass


class Live(TradeCheck):
    def live_candles(self):
        # get period amount from weights
        periods = self.weights['periods']
        # load most recent candles from csv
        data = market_csv.csv_read_recent(currency_pair=self.currency_pair, gran=self.gran, periods=periods)
        return self.candle_check(data=data, periods=periods)
