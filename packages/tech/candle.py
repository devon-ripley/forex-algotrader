import numpy as np
import talib


def candle_ratio_single(price):
    open_point = price[3]
    close_point = price[6]
    high_point = price[4]
    low_point = price[5]
    box = abs(open_point - close_point)
    box_points = [open_point, close_point]
    # print(box_points)
    # print(box)
    handle_start = np.minimum(open_point, close_point)
    handle = handle_start - low_point
    whole_length = high_point - low_point
    top_length = abs(np.maximum(open_point, close_point) - high_point)
    bottom_length = abs(open_point - low_point)
    if whole_length == 0:
        return False
    # ratios
    top_stick_ratio = top_length / whole_length
    # print('top_stick_ratio', top_stick_ratio)
    box_whole_ratio = box / whole_length
    # print('box_whole_ratio', box_whole_ratio)
    bottom_stick_ratio = handle / whole_length
    # print('bottom_stick_ratio', bottom_stick_ratio)
    # body_location
    middle_box = np.maximum(open_point, close_point) - (box / 2)
    location_mult = 100 / whole_length
    middle_box_location = location_mult * (middle_box - low_point)
    # box location
    # print('middle_box_location', middle_box_location)
    ratios = {'bottom_stick_ratio': bottom_stick_ratio, 'top_stick_ratio': top_stick_ratio,
              'box_whole_ratio': box_whole_ratio, 'middle_box_location': middle_box_location}
    return ratios


def candle_ratio_multiple(price):
    # price is list of dicts
    ratios = []
    for x in price:
        ratios.append(candle_ratio_single(x))
    return ratios


# candlestick patterns
def single_candle(data, weights, direction, gran, pair):
    results = []
    price = data[-1]
    date = data[-1][2]
    ratios = candle_ratio_single(price)
    if ratios is False:
        return None
    if ratios['bottom_stick_ratio'] >= 0.6666 and \
            ratios['top_stick_ratio'] <= 0.166 and \
            ratios['middle_box_location'] >= 65.0:
        if direction == 0:
            # Hammer
            # make a function to do all score and advanced math for all single candles!!!!!
            score = 100
            mult = weights['hammer']['weight']
            score = score * mult
            # check from divergence
            dic = {'pattern': 'hammer', 'execute': True, 'score': score,
                   'date': date, 'conformation': weights['hammer']['conformation'],
                   'direction': direction, 'gran': gran, 'pair': pair, 'ratios': ratios}
            results.append(dic)
        if direction == 1:
            # hanging man
            score = 100
            mult = weights['hanging_man']['weight']
            score = score * mult
            dic = {'pattern': 'hanging_man', 'execute': True, 'score': score,
                   'date': date, 'conformation': weights['hanging_man']['conformation'],
                   'direction': direction, 'gran': gran, 'pair': pair, 'ratios': ratios}
            results.append(dic)

    return results


## New candle check


def all_candles(data, weights, direction, gran, pair):
    results = []
    last_line = data[-1]
    # separate data
    date = last_line[2]
    s_candle = np.array([last_line[3], last_line[4], last_line[5], last_line[6]])
    # check candles
    hammer = talib.CDLHAMMER(s_candle)
    hanging_man = talib.CDLHANGINGMAN(s_candle)
    # check directions
    if direction == 0:
        if hammer:
            # Hammer
            # make a function to do all score and advanced math for all single candles!!!!!
            score = 100
            # mult = weights['hammer']['weight']
            # score = score * mult
            # check from divergence
            dic = {'pattern': 'hammer', 'execute': True, 'score': score,
                   'date': date, 'conformation': weights['hammer']['conformation'],
                   'direction': direction, 'gran': gran, 'pair': pair}
            results.append(dic)

    if direction == 1:
        if hanging_man:
            # hanging man
            score = 100
            # mult = weights['hanging_man']['weight']
            # score = score * mult
            dic = {'pattern': 'hanging_man', 'execute': True, 'score': score,
                   'date': date, 'conformation': weights['hanging_man']['conformation'],
                   'direction': direction, 'gran': gran, 'pair': pair}
            results.append(dic)

    if results is not True:
        return None
    return results
