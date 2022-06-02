import numpy as np
from packages.tech import trade_check


class TradeStrategy:

    def __init__(self, currency_pair, gran):
        self.currency_pair = currency_pair
        self.gran = gran
        self.indicator_dict = {}
        self.market_data = None
        self.last_range = 0

    def pt_analysis(self, data):
        # only pass in presmoothed data
        # find peaks and troughs
        periods = len(data)
        local_min = (np.diff(np.sign(np.diff(data))) > 0).nonzero()[0] + 1  # local min
        local_max = (np.diff(np.sign(np.diff(data))) < 0).nonzero()[0] + 1  # local max
        # find support, resistance
        price_point_min = []
        for point in local_min:
            price_point_min.append(data[point])
        # normalize y-axis(price)
        low_min = min(price_point_min)
        high_min = max(price_point_min)
        norm_pp = []
        for x in price_point_min:
            norm_pp.append((x - low_min) / (high_min - low_min) * periods)

        pp_min = np.array(norm_pp)
        combined_min_norm = np.vstack((local_min, pp_min)).T
        # get slopes
        min_slopes = []
        for x in range(len(pp_min) - 1):
            min_slopes.append([local_min[x], (combined_min_norm[x][1] - combined_min_norm[x + 1][1]) /
                               (combined_min_norm[x][0] - combined_min_norm[x + 1][0])])

        price_point_max = []
        for point in local_max:
            price_point_max.append(data[point])
        # normalize y-axis(price)
        low_max = min(price_point_max)
        high_max = max(price_point_max)
        norm_pp = []
        for x in price_point_max:
            norm_pp.append((x - low_max) / (high_max - low_max) * periods)
        pp_max = np.array(norm_pp)
        combined_max_norm = np.vstack((local_max, pp_max)).T
        # get slopes
        max_slopes = []
        for x in range(len(pp_max) - 1):
            max_slopes.append([local_max[x], (combined_max_norm[x][1] - combined_max_norm[x + 1][1]) /
                               (combined_max_norm[x][0] - combined_max_norm[x + 1][0])])
        return {'max_slopes': max_slopes, 'min_slopes': min_slopes}

    def _strat1(self):
        # RSI, BBands. Overbought, oversold
        points = 0
        BBannd = self.indicator_dict['bband']
        b_up = BBannd['upper']
        b_mid = BBannd['middle']
        b_low = BBannd['lower']
        rsi = self.indicator_dict['rsi']
        periods = len(rsi)
        rsi_slopes = self.pt_analysis(rsi)
        avr_market_data = (self.market_data['open'] + self.market_data['close']) / 2
        price_slopes = self.pt_analysis(avr_market_data)
        min_start = rsi_slopes['min_slopes'][-1][0]
        max_start = (periods - rsi_slopes['max_slopes'][-1][0]) + 1
        scope_min = rsi[min_start:]
        buy_go = map(lambda x: True if (x <= 30) else False, scope_min)
        scope_max = rsi[max_start:]
        sell_go = map(lambda x: True if (x >= 70) else False, scope_max)
        if True in buy_go:
            # buy, rsi under 30
            points += 1
            if avr_market_data[-1] <= b_low[-1] + (b_low[-1] * 0.05):
                # price under lower bband
                points += 1
            # if rsi pt slope is inverse of price pt slope, points += 1
            if rsi_slopes['min_slopes'][-1][1] > 0 > price_slopes['min_slopes'][-1][1]:
                points += 1

        elif True in sell_go:
            # sell
            points -= 1
            if avr_market_data[-1] >= b_up[-1] + (b_up[-1] * 0.05):
                # price over upper bband
                points -= 1
            if rsi_slopes['max_slopes'][-1][1] < 0 < price_slopes['max_slopes'][-1][1]:
                points -= 1
        return points

    def _strat2(self):
        return self.indicator_dict

    def _strat3(self):
        return self.indicator_dict

    def _strat4(self):
        return self.indicator_dict

    def _strat5(self):
        return self.indicator_dict

    def run_trade_strategy(self, data):
        self.indicator_dict = trade_check.all_indicators(self.currency_pair, self.gran, data)
        self.market_data = data
        self.pt_analysis((data['close'] + data['high']) / 2)
        self.last_range = self.indicator_dict['atr'][-1]

        return [self._strat1()]
