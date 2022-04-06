# sma, ema, bollinger bands, standard deviation, fibonotchi, average true range(atr)
# resistance, support
from packages.output.market_csv import csv_read, csv_read_full
from decimal import Decimal
import decimal


def sma(frame, period, currency_pair, gran, week_back):
    decimal.getcontext().prec = 4
    data = csv_read(frame, currency_pair, gran, week_back)
    result = []
    count = 0
    s1 = 0
    for t in range(frame - period):
        for x in range(count, period + count):
            s1 += Decimal(data[x][6])
        data_point = s1 / period
        s1 = 0

        result.append([data[x][2], data_point])### should be t????
        count += 1
    return result


def ema(data, period):
    sma_result = []
    count = 0
    s1 = 0
    frame = len(data)
    # get sma for first calc
    for t in range(frame - period):
        for x in range(count, period + count):
            s1 += float(data[x][6])
        data_point = s1 / period
        s1 = 0

        sma_result.append([data[t][2], data_point])
        count += 1
    # get ema
    ema_start = sma_result[0][1]
    data_ema = data[period:len(data)]
    ema_result = []
    days = 0
    multi = (2 / (1 + period))
    for x in range(len(data_ema)):
        past = ema_start * (1 - multi)
        data_point = (float(data_ema.iloc[x][6]) * multi) + past
        ema_result.append([data_ema[x][2], data_point])
        days += 1
        ema_start = data_point
    return ema_result


def ema_day(period, currency_pair):
    decimal.getcontext().prec = 4
    data = csv_read_full(currency_pair, 'D')
    sma_result = []
    count = 0
    s1 = 0
    frame = len(data)
    # get sma for first calc
    for t in range(frame - period):
        for x in range(count, period + count):
            s1 += float(data[x][6])
        data_point = s1 / period
        s1 = 0

        sma_result.append([data[x][2], data_point])# should it be t?????
        count += 1
    # get ema
    ema_start = sma_result[0][1]
    data_ema = data[period:]
    ema_result = []
    days = 0
    multi = (2 / (1 + period))
    for x in data_ema:
        past = ema_start * (1 - multi)
        data_point = (float(x[6]) * multi) + past
        ema_result.append([x[2], data_point])
        days += 1
        ema_start = data_point
    return ema_result


def atr_day(currency_pair, period=14):
    data = csv_read_full(currency_pair, 'D')
    temp_result = []
    atr_result = []

    def tr(hight, lowt, last_closed):
        temp_list = [hight - lowt, abs(hight - last_closed), abs(lowt - last_closed)]
        cur_trg = max(temp_list)
        return cur_trg

    for x in range(len(data)):
        date = data[x][2]
        high = float(data[x][4])
        low = float(data[x][5])
        last_close = float(data[x - 1][6])
        if x == 0:
            # first day atr calc
            data_point = high - low
            temp_result.append(data_point)
            continue
        if x == period - 1:
            cur_tr = tr(high, low, last_close)
            temp_result.append(cur_tr)
            atr_first = sum(temp_result) / len(temp_result)
            atr_result.append([data[x][2], atr_first])
        if x >= period:
            cur_tr = tr(high, low, last_close)
            cur_atr = (atr_result[x - period][1] * (period - 1) + cur_tr) / period
            atr_result.append([data[x][2], cur_atr])
        else:
            cur_tr = tr(high, low, last_close)
            temp_result.append(cur_tr)
    return atr_result


def resnsup(frame, currency_pair, gran, week_back):  # IN PROGRESS
    data = csv_read(frame, currency_pair, gran, week_back)
    start_price = data[0][6]
    end_price = data[frame - 1][6]
    price_list = []
    support = 0
    resistance = 0
    # make a list of all candle close prices
    for x in range(frame - 1):
        price_list.append(data[x][6])

    input()
    for t in range(len(price_list)):
        # initial setup
        if t == 0:
            if price_list[t] >= price_list[t + 1]:
                resistance = price_list[t]
            elif price_list[t] < price_list[t + 1]:
                support = price_list[t]
        # hill
        # breakout
        if price_list[t] >= resistance:
            support = price_list[t]

        if price_list[t] < support:
            resistance = price_list[t]
        print(t)
    print(data)
    print(start_price, end_price)
    print(price_list)
