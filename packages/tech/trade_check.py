from packages.output import market_csv
import trade_strategy
import numpy
import talib


def indicators(currency_pair, gran, data):
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
    def back_candles(self, market_reader_obs, track_year, neat_raw=False):
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
            if neat_raw:
                return indicators(self.currency_pair, self.gran, data)
            else:
                return trade_strategy.trade_strategy(self.currency_pair, self.gran, data)
        else:
            data = mr_data['data']
            if neat_raw:
                return indicators(self.currency_pair, self.gran, data)
            else:
                return trade_strategy.trade_strategy(self.currency_pair, self.gran, data)