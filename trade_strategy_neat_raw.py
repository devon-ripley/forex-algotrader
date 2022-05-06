# Testing passing the raw indicator numbers to neat
# probably wont work well, but worth a shot!
import talib


def indicators(data):
    # Momentum indicators
    m_dict = {}
    macd, macdsignal, macdhist = talib.MACD(data['close'], fastperiod=12, slowperiod=26, signalperiod=9)
    m_dict['macd'] = {'line': macd, 'signal': macdsignal, 'hist': macdhist}

    rsi = talib.RSI(data['close'])
    m_dict['rsi'] = rsi

    # Price point indicators
    bband_upper, bband_middle, bband_lower = talib.BBANDS(data['close'], timeperiod=5, nbdevup=2, nbdevdn=2, matype=0)
    m_dict['bband'] = {'upper': bband_upper, 'middle': bband_middle, 'lower': bband_lower}

    ema = talib.EMA(data['close'])
    m_dict['ema'] = ema


    # range indicators
    atr = talib.ATR(data['high'], data['low'], data['close'], timeperiod=14)
    m_dict['atr'] = atr

    # volume indicators
    # obv = talib.OBV(data['close'], data['volume'])
    # m_dict['obv'] = obv

    return m_dict


def trade_strategy(currency_pair, gran, data):
    return {'indicators': indicators(data),
            'pair': currency_pair, 'gran': gran}
