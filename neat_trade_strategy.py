import talib
from packages.tech import trade_check


class TradeStrategy:

    def __init__(self, currency_pair, gran):
        self.currency_pair = currency_pair
        self.gran = gran
        self.indicator_dict = {}
        self.last_range = 0



    def _strat1(self):
        # RSI, BBands. Overbought, oversold
        BBannd = self.indicator_dict['bband']
        b_up = BBannd['upper']
        b_mid = BBannd['middle']
        b_low = BBannd['lower']
        rsi = self.indicator_dict['rsi']
        if rsi[-1] <= 20:
            #buy
        if rsi[-1] >= 80:
            #sell
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

        return [self._strat1(), self._strat2(), self._strat3(), self._strat4(), self._strat5()]
