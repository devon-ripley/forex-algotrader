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


def indicators_compare(indicators):
    # price_point
    return assesment


def stoploss_takeprofit_calc(indicators):
    # aclculate base stoploss and


def trade_strategy(currency_pair, gran, data):
    indicator_dict = {'price_point': price_points(data), 'momentum': momentum(data), 'range': range(data)}
    compair_dict = indicators_compare(indicator_dict)
    stop_take = stoploss_takeprofit_calc(indicator_dict)
    results = compair_dict + stop_take
    return results
