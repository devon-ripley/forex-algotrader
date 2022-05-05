# Testing passing the raw indicator numbers to neat
# probably wont work well, but worth a shot!
import talib


def momentum(data):
    m_dict = {}
    macd, macdsignal, macdhist = talib.MACD(data['close'], fastperiod=12, slowperiod=26, signalperiod=9)
    m_dict['macd'] = {'line': macd, 'signal': macdsignal, 'hist': macdhist}

    rsi = talib.RSI(data['close'])
    m_dict['rsi'] = rsi

    return m_dict


def price_points(data):
    pp_dict = {}

    bband_upper, bband_middle, bband_lower = talib.BBANDS(data['close'], timeperiod=5, nbdevup=2, nbdevdn=2, matype=0)
    pp_dict['bband'] = {'upper': bband_upper, 'middle': bband_middle, 'lower': bband_lower}

    ema = talib.EMA(data['close'])
    pp_dict['ema'] = ema

    return pp_dict


def range(data):
    rv_dict = {}
    atr = talib.ATR(data['high'], data['low'], data['close'], timeperiod=14)
    rv_dict['atr'] = atr

    obv = talib.OBV(data['close'], data['volume'])
    rv_dict['obv'] = obv

    return rv_dict


def trade_strategy(currency_pair, gran, data):
    return {'price_point': price_points(data), 'momentum': momentum(data), 'range': range(data),
            'pair': currency_pair, 'gran': gran}
