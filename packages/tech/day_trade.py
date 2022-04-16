import time

from packages.output import market_csv
from packages.tech import candle
import json
import numpy
import talib


class TradeCheck:
    def __init__(self, currency_pair, gran):
        self.currency_pair = currency_pair
        self.gran = gran
        self.first = True
        # get weights and ratios for just current currency_pair and gran
        f = open('data/weights.json', 'r')
        weights = json.load(f)
        f.close()
        self.data_periods = weights['currency_pairs'][currency_pair][gran]['periods']
        self.weights = weights['currency_pairs'][currency_pair][gran]
        # indicator vars
        self.wait_confirmation = []
        self.indicator_dict = {}
        self.data = {}

    def indicator_check(self):

        macd, macdsignal, macdhist = talib.MACD(self.data['close'], fastperiod=12, slowperiod=26, signalperiod=9)
        self.indicator_dict['macd'] = [macd, macdsignal, macdhist]
        real = talib.ATR(self.data['high'], self.data['low'], self.data['close'], timeperiod=14)
        results = {'range': real[-1], 'candles': [{'increase': macd[-1]}]}
        return results

    def indicator_trade_check(self, direction):
        # macd check TEMP!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        macd_ind = self.indicator_dict['macd']
        macd_line = macd_ind[0]
        macd_li = macd_line[len(macd_line) - 7:]
        macd_signal = macd_ind[1][len(macd_line) - 7:]
        macd_hist = macd_ind[2][len(macd_line) - 7:]
        above = None
        below = None
        for ite, m_line in enumerate(macd_li):


            if m_line >= macd_signal[ite]:
                # mline above
                above = True
                if below:
                    return {'execute': True, 'score': 100,
                            'date': self.data['date'][-1],
                            'direction': direction, 'gran': self.gran, 'pair': self.currency_pair}
            if m_line <= macd_signal[ite]:
                # mline below
                below = True
                if above:
                    return {'execute': True, 'score': 100,
                            'date': self.data['date'][-1],
                            'direction': direction, 'gran': self.gran, 'pair': self.currency_pair}
        return False

    def make_trade_check(self):
        # set up candle single weights
        # self.data.append(data[-1])
        candle_single_dict_weights = self.weights['candle_single']
        # check indicators
        self.trend_list = self.indicator_check()
        # check for past confirmations needed
        current_date = self.data['date'][-1]
        con_result = []
        for x in self.wait_confirmation:
            if current_date > x['date']:
                # check if candle is confirmed
                if x['direction'] == 1:
                    # check for going up
                    if self.data['open'][-1] - self.data['close'][-1] < 0:
                        x['conformation'] = False
                        con_result.append(x)
                else:
                    # check for going down
                    if self.data['open'][-1] - self.data['close'][-1] > 0:
                        x['conformation'] = False

        if self.trend_list['candles'][-1]['increase'] > 0:
            direction = 0
        else:
            direction = 1
        # compare candles on latest complete candle
        length = len(self.data['date'])
        last_candle = {'date': self.data['date'][length - 3:], 'open': self.data['open'][length - 3:],
                       'high': self.data['high'][length - 3:],
                       'low': self.data['low'][length - 3:], 'close': self.data['close'][length - 3:],
                       'volume': self.data['volume'][length - 3:]}
        #results = candle.all_candles(last_candle, candle_single_dict_weights, direction, self.gran, self.currency_pair)
        #if not results:
        #    return None
        #for x in results:
        #    print(x)
        #    trend_list_mot = dict(self.trend_list)
        #    last = trend_list_mot['candles'][-1]
        #    del trend_list_mot['candles']
        #    trend_list_mot['candle'] = last
        #    x['last_trend'] = trend_list_mot
        #    if x['execute']:
        #        if x['conformation']:
        #            self.wait_confirmation.append(x)
        #if con_result:
        #    results = results + con_result
        #else:
        #    pass
        # Add indicator check results into results
        ind_results = self.indicator_trade_check(direction)
        results = ind_results
        if results:
            return results
        if not results:
            return None


class Live(TradeCheck):
    def live_candles(self):
        # load most recent candles from csv
        data = market_csv.csv_read_recent(currency_pair=self.currency_pair, gran=self.gran, periods=self.data_periods)
        self.data = data

        return self.make_trade_check()


class Past(TradeCheck):  ## inharit from backtest_csv???

    def back_candles(self, market_reader_obs, track_year):
        market_read = market_reader_obs[track_year][self.currency_pair][self.gran]
        if not market_read.go:
            return None
        data_dict = {}
        mr_data = market_read.output_backchunk(self.data_periods)
        if mr_data['complete'] is False:
            past_market_read = market_reader_obs[track_year - 1][self.currency_pair][self.gran]
            past_year_data = past_market_read.split_year(mr_data['back'])
            current_year_data = market_read.new_year(self.data_periods - mr_data['back'])
            # add together dicts
            data_dict['date'] = past_year_data['date'] + current_year_data['date']
            data_dict['open'] = numpy.concatenate((past_year_data['open'], current_year_data['open']))
            data_dict['high'] = numpy.concatenate((past_year_data['high'], current_year_data['high']))
            data_dict['low'] = numpy.concatenate((past_year_data['low'], current_year_data['low']))
            data_dict['close'] = numpy.concatenate((past_year_data['close'], current_year_data['close']))
            data_dict['volume'] = numpy.concatenate((past_year_data['volume'], current_year_data['volume']))
            self.data = data_dict
            return self.make_trade_check()
        else:
            self.data = mr_data['data']
            return self.make_trade_check()
