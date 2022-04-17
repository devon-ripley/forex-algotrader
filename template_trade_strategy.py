# REMOVE TEMPLATE FROM FILE NAME
def trade_strategy(currency_pair, gran, data):
    pass
# length of data is set in weights.json as periods

# data is formated as a dictionary of numpy arrays and a list of datetime objects
# {
# ['date'] = [datetime(2021, 05, 05, 20, 00), datetime(2021, 05, 05, 20, 30)]
# ['open'] = numpy.array([112.55, 112.56])
# ['high'] = numpy.array([112.55, 112.56])
# ['low'] = numpy.array([112.55, 112.56])
# ['close'] = numpy.array([112.55, 112.56])
# ['volume'] = numpy.array([189, 114])
# }


# return dictionary, or list of dictionaries, in this format to make a trade
# {'execute': True,
# 'score': 100, trade with the highest score gets executed
# 'date': datetime(2021, 05, 05, 20, 06),
# 'direction': 1, 0 for short, 1 for long
# 'stop_loss': 112.05,
# 'take_profit': 112.77,
# 'gran': M30,
# 'pair': USD_JPY}

# return None if no trades to make
