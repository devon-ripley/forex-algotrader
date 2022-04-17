import talib


def trend_check(data):
    macd, macdsignal, macdhist = talib.MACD(data['close'], fastperiod=12, slowperiod=26, signalperiod=9)
    indicator_dict = {
        'macd': [macd, macdsignal, macdhist]
    }
    real = talib.ATR(data['high'], data['low'], data['close'], timeperiod=14)
    results = {'range': real[-1], 'indicator_dict': indicator_dict, 'candles': [{'increase': macd[-1]}]}
    return results


def make_trade_check(currency_pair, gran, data, trend_list):
    direction = trend_list['direction']
    # macd check TEMP!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    macd_ind = trend_list['indicator_dict']['macd']
    macd_line = macd_ind[0]
    macd_li = macd_line[len(macd_line) - 7:]
    macd_signal = macd_ind[1][len(macd_line) - 7:]
    macd_hist = macd_ind[2][len(macd_line) - 7:]
    above = None
    below = None
    if direction == 0:
        # short
        stop_loss = ((data['close'][-1]+ data['open'][-1])/2) + trend_list['range'] + 1
        take_profit = ((data['close'][-1]+ data['open'][-1])/2) - trend_list['range'] - 1
    else:
        # long
        stop_loss = ((data['close'][-1]+ data['open'][-1])/2) - trend_list['range'] - 1
        take_profit = ((data['close'][-1]+ data['open'][-1])/2) + trend_list['range'] + 1
    for ite, m_line in enumerate(macd_li):

        if m_line >= macd_signal[ite]:
            # mline above
            above = True
            if below:
                return {'execute': True, 'score': 100,
                        'date': data['date'][-1],
                        'direction': direction, 'stop_loss': stop_loss, 'take_profit': take_profit, 'gran': gran, 'pair': currency_pair}
        if m_line <= macd_signal[ite]:
            # mline below
            below = True
            if above:
                return {'execute': True, 'score': 100,
                        'date': data['date'][-1],
                        'direction': direction, 'stop_loss': stop_loss, 'take_profit': take_profit, 'gran': gran, 'pair': currency_pair}
    return False


def trade_strategy(currency_pair, gran, data):
    trend_list = trend_check(data)

    if trend_list['candles'][-1]['increase'] > 0:
        trend_list['direction'] = 0
    else:
        trend_list['direction'] = 1

    trade_strategy_results = make_trade_check(currency_pair, gran, data, trend_list)
    if trade_strategy_results:
        return trade_strategy_results
    if not trade_strategy_results:
        return None
