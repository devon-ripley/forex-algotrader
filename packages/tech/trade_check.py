import neat_trade_strategy
from packages.output import market_csv
import trade_strategy
import numpy
import talib


def all_indicators(currency_pair, gran, data):
    m_dict = {}
    macd, macdsignal, macdhist = talib.MACD(data['close'], fastperiod=12, slowperiod=26, signalperiod=9)
    m_dict['macd'] = {'line': macd, 'signal': macdsignal, 'hist': macdhist}

    rsi = talib.RSI(data['close'])
    m_dict['rsi'] = rsi

    # Price point indicators
    bband_upper, bband_middle, bband_lower = talib.BBANDS(data['close'], timeperiod=5, nbdevup=2, nbdevdn=2, matype=0)
    m_dict['bband'] = {'upper': bband_upper, 'middle': bband_middle, 'lower': bband_lower}

    ema = talib.EMA(data['close'], timeperiod=30)
    m_dict['ema'] = ema


    # range indicators
    atr = talib.ATR(data['high'], data['low'], data['close'], timeperiod=14)
    m_dict['atr'] = atr

    # local min, max
    # smooth data



    # volume indicators
     #obv = talib.OBV(data['close'], data['volume'])
     #m_dict['obv'] = obv

    return m_dict


def neat_raw_indicators(currency_pair, gran, data):
    # Momentum indicators
    m_dict = {}
    macd, macdsignal, macdhist = talib.MACD(data['close'], fastperiod=12, slowperiod=26, signalperiod=9)
    m_dict['macd'] = {'line': macd, 'signal': macdsignal, 'hist': macdhist}

    rsi = talib.RSI(data['close'])
    m_dict['rsi'] = rsi

    # Price point indicators
    #bband_upper, bband_middle, bband_lower = talib.BBANDS(data['close'], timeperiod=5, nbdevup=2, nbdevdn=2, matype=0)
    #m_dict['bband'] = {'upper': bband_upper, 'middle': bband_middle, 'lower': bband_lower}

    #ema = talib.EMA(data['close'])
    #m_dict['ema'] = ema


    # range indicators
    atr = talib.ATR(data['high'], data['low'], data['close'], timeperiod=14)
    m_dict['atr'] = atr

    # volume indicators
    # obv = talib.OBV(data['close'], data['volume'])
    # m_dict['obv'] = obv

    return {'indicators': m_dict,
            'pair': currency_pair, 'gran': gran}


class TradeCheck:
    def __init__(self, currency_pair, gran, periods):
        self.trend = None
        self.currency_pair = currency_pair
        self.gran = gran
        self.data_periods = periods

    def trend_set(self, data):
        if self.gran == 'D':
            start = data['close'][0]
            end = data['close'][-1]
            if end >= start:
                self.trend = 'UP'
            else:
                self.trend = 'DOWN'


class Live(TradeCheck):
    def live_candles(self, neat_raw=False, neat_strat=False):
        # load most recent candles from csv
        data = market_csv.csv_read_recent(currency_pair=self.currency_pair, gran=self.gran, periods=self.data_periods)
        self.trend_set(data)
        if neat_raw:
            return neat_raw_indicators(self.currency_pair, self.gran, data)
        if neat_strat:
            strat = neat_trade_strategy.TradeStrategy(self.currency_pair, self.gran)
            results = strat.run_trade_strategy(data)
            return {'inputs': results, 'range': strat.last_range}
        else:
            return trade_strategy.trade_strategy(self.currency_pair, self.gran, data)


class Past(TradeCheck):
    def back_candles(self, market_reader_obs, track_year, neat_raw=False, neat_strat=False):
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
            # axis = None?
            data_dict['open'] = numpy.concatenate((past_year_data['open'], current_year_data['open']))
            data_dict['high'] = numpy.concatenate((past_year_data['high'], current_year_data['high']))
            data_dict['low'] = numpy.concatenate((past_year_data['low'], current_year_data['low']))
            data_dict['close'] = numpy.concatenate((past_year_data['close'], current_year_data['close']))
            data_dict['volume'] = numpy.concatenate((past_year_data['volume'], current_year_data['volume']))
            data = data_dict
            self.trend_set(data)
            if neat_raw:
                return neat_raw_indicators(self.currency_pair, self.gran, data)
            if neat_strat:
                strat = neat_trade_strategy.TradeStrategy(self.currency_pair, self.gran)
                results = strat.run_trade_strategy(data)
                return {'inputs': results, 'range': strat.last_range}
            else:
                return trade_strategy.trade_strategy(self.currency_pair, self.gran, data)
        else:
            data = mr_data['data']
            self.trend_set(data)
            if neat_raw:
                return neat_raw_indicators(self.currency_pair, self.gran, data)
            if neat_strat:
                strat = neat_trade_strategy.TradeStrategy(self.currency_pair, self.gran)
                results = strat.run_trade_strategy(data)
                return {'inputs': results, 'range': strat.last_range}
            else:
                return trade_strategy.trade_strategy(self.currency_pair, self.gran, data)