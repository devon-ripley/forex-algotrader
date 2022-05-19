import numpy as np
from packages.tech import trade_check


class TradeStrategy:

    def __init__(self, currency_pair, gran):
        self.currency_pair = currency_pair
        self.gran = gran
        self.indicator_dict = {}
        self.market_data = []
        self.last_range = 0

    def pt_analysis(self, data):
        # only pass in presmoothed data
        # find peaks and troughs
        local_min = (np.diff(np.sign(np.diff(data))) > 0).nonzero()[0] + 1  # local min
        local_max = (np.diff(np.sign(np.diff(data))) < 0).nonzero()[0] + 1  # local max
        # find support, resistance
        price = []
        for point in local_min:
            price.append(data[point])
        p = np.array(price)
        com_min = np.vstack((local_min, p)).T

        price = []
        for point in local_max:
            price.append(data[point])
        p = np.array(price)
        com_max = np.vstack((local_max, p)).T


    def _strat1(self):
        # RSI, BBands. Overbought, oversold
        BBannd = self.indicator_dict['bband']
        b_up = BBannd['upper']
        b_mid = BBannd['middle']
        b_low = BBannd['lower']
        rsi = self.indicator_dict['rsi']
        if rsi[-1] <= 30:
            # buy
            if self.market_data[-1] <= b_low[-1]:
                pass
        if rsi[-1] >= 70:
            #sell
            if self.market_data[-1] >= b_up[-1]:
                pass
        return self.indicator_dict

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

        return [self._strat1(), self._strat2(), self._strat3(), self._strat4(), self._strat5()]
