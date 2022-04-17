from packages.output import market_csv
import trade_strategy
import numpy


class TradeCheck:
    def __init__(self, currency_pair, gran, periods):
        self.trend_list = None
        self.currency_pair = currency_pair
        self.gran = gran
        self.data_periods = periods


class Live(TradeCheck):
    def live_candles(self):
        # load most recent candles from csv
        data = market_csv.csv_read_recent(currency_pair=self.currency_pair, gran=self.gran, periods=self.data_periods)

        return trade_strategy.trade_strategy(self.currency_pair, self.gran, data)

class Past(TradeCheck):
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
            data = data_dict

            return trade_strategy.trade_strategy(self.currency_pair, self.gran, data)
        else:
            data = mr_data['data']
            return trade_strategy.trade_strategy(self.currency_pair, self.gran, data)
