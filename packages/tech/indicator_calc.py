from packages.tech import indicators
from packages.oanda_api import oanda_api
from packages.output import market_csv
import datetime
from decimal import Decimal
import decimal


def account_limits(apikey, account_id, max_section_use, max_risk, margin_rate):
    decimal.getcontext().prec = 4
    info = oanda_api.account_summary(apikey, account_id)
    info = info['account']
    balance = Decimal(info['balance'])
    max_use = Decimal(max_section_use) * balance
    risk_amount = Decimal(max_risk) * balance
    max_units = max_use * Decimal(margin_rate)
    max_units = round(max_units)
    return {'balance': balance, 'max_use': max_use, 'risk_amount': risk_amount, 'max_units': max_units}


def overnight_range(data):
    format_list = []
    for x in data:
        date = x[2]
        date = market_csv.csv_date_convert(date)
        high = x[4]
        low = x[5]
        format_list.append([date, high, low])
    overnight_list = []
    for x in format_list:
        date = x[0]
        date = datetime.datetime.fromisoformat(date)
        day = int(date.strftime('%w'))
        if day == 0 or day == 5:
            continue
        # if not sunday or friday
        time = date.time()
        if datetime.time(20, 0) <= time <= datetime.time(23, 0):
            overnight_list.append(x)
    count = 0
    temp_list = []
    final = []
    for x in overnight_list:
        date = x[0]
        date_con = datetime.datetime.fromisoformat(date)
        date_con = date_con.date()
        today = datetime.datetime.now()
        if date_con == today.date():
            print('today')
            break
        if count <= 3:
            count += 1
            temp_list.append(float(x[1]))
            temp_list.append(float(x[2]))
        # if end of day, 4 hrs per date
        if count > 3:
            maxnum = max(temp_list)
            print(maxnum)
            minnum = min(temp_list)
            pip_range = maxnum - minnum
            final.append(pip_range)
            # reset

            temp_list = []
            count = 0
    # get average range from pip_range
    total = 0.0
    for x in final:
        total += x
    finish = total / (len(final))
    return finish


def strong_trending(pair, days_back=10):
    # 10 day Ema, 20 day Ema, 50 day Ema, 200 day Ema
    data_10 = indicators.ema_day(10, pair)
    data_20 = indicators.ema_day(20, pair)
    data_50 = indicators.ema_day(50, pair)
    data_200 = indicators.ema_day(200, pair)
    start = data_200[0][0]
    for x in range(len(data_10)):
        if data_10[x][0] == start:
            cut = x
    data_10 = data_10[cut:]

    for x in range(len(data_20)):
        if data_20[x][0] == start:
            cut = x
    data_20 = data_20[cut:]

    for x in range(len(data_50)):
        if data_50[x][0] == start:
            cut = x
    data_50 = data_50[cut:]
    # get price data from csv
    data = market_csv.csv_read_full(pair, 'D', 0)
    price_list = []
    for x in data:
        price_list.append([x[2], float(x[3]), float(x[4]), float(x[5]), float(x[6])])
    for x in range(len(price_list)):
        if price_list[x][0] == start:
            cut = x
    price_list = price_list[cut:]
    days_back_neg = days_back * -1
    # check proper order of emas and price data against emas
    up_check = 0
    down_check = 0
    up_set = False
    down_set = False
    # use more price data for a more picky result.
    for x in range(days_back_neg, 0):
        point_a = data_10[x][1]
        point_b = data_20[x][1]
        point_c = data_50[x][1]
        point_d = data_200[x][1]
        if point_a > point_b > point_c > point_d:
            up_check += 1
        if point_a < point_b < point_c < point_d:
            down_check += 1
        if down_check == days_back:
            down_check = 0
            for y in range(days_back_neg, 0):
                price_point_o = price_list[x][1]
                price_point_h = price_list[x][2]
                price_point_l = price_list[x][3]
                price_point_c = price_list[x][4]
                ema_point = data_10[x][1]
                if price_point_o < ema_point and price_point_l < ema_point and price_point_c < ema_point:
                    down_check += 1
                if down_check == days_back:
                    down_set = True
        if up_check == days_back:
            up_check = 0
            for y in range(days_back_neg, 0):
                price_point_o = price_list[x][1]
                price_point_h = price_list[x][2]
                price_point_c = price_list[x][4]
                ema_point = data_10[x][1]
                if price_point_o > ema_point and price_point_h > ema_point and price_point_c > ema_point:
                    up_check += 1
                if up_check == days_back:
                    up_set = True
    if up_set:
        return ['UP', data_10]
    if down_set:
        return ['DOWN', data_10]
    else:
        return [False, data_10]


def trend_trade(currency_pair, currency_price, risk_amount, max_units):
    #check = trade_csv.check_trade_trend(currency_pair)
    #if check != 0:
        # check if trade still active
        #return 0
    # check for trend
    result = strong_trending(currency_pair)
    ema_10 = result[1]
    if not result[0]:
        return {'currency_pair': currency_pair, 'execute': False}
    if result[0] == 'UP':
        # calculate stoploss using ATR
        atr = indicators.atr_day(currency_pair)
        last_atr = atr[-1][1]
        last_ema = ema_10[-1][1]
        stop_loss = last_ema - (last_atr * 0.5)
        # calculate number of units
        current_price = currency_price[currency_pair]
        dif = current_price - stop_loss
        units = risk_amount / dif
        if units > max_units:
            units = max_units
        trade_info = {'currency_pair': currency_pair, 'execute': True, 'units': units, 'stop_loss': dif,
                      'direction': 'LONG'}
        return trade_info
    if result[0] == 'DOWN':
        # calculate stoploss using ATR
        atr = indicators.atr_day(currency_pair)
        last_atr = atr[-1][1]
        last_ema = ema_10[-1][1]
        stop_loss = last_ema + (last_atr * 0.5)
        # calculate number of units
        current_price = currency_price[currency_pair]
        dif = stop_loss - current_price
        units = risk_amount / dif
        if units > max_units:
            units = max_units
        trade_info = {'currency_pair': currency_pair, 'execute': True, 'units': units, 'stop_loss': dif,
                      'direction': 'SHORT'}
        return trade_info

