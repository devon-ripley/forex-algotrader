# forex_algotrader
For educational purposes only

Uses Oanda for market data and trading.

Forex trading, I plan on adding crypto and maybe stocks in the future.

URL in packages/oanda_api/oanda_api.py set to practice account.

Mysql required to run. Set up database for program to use. Set up user with all permissions for that database. User name, password, and database name are put in data/config.json.

Notifications use yagmail python package, gmail account is required to send notifications .

I plan on adding report generation, and NEAT machine learning for for fine tuning strategies.

REMOVE TEMPLATE FROM TEMPLATE_TRADE_STRATEGY.PY BEFORE STARTING

# Put trading strategy in trade_strategy.py, format is:

def trade_strategy(currency_pair, gran, data):
length of data is set in weights.json as periods

data is formated as a dictionary of numpy arrays and a list of datetime objects

data = {

['date']: [datetime(2021, 05, 05, 20, 00), datetime(2021, 05, 05, 20, 30)]

['open']: numpy.array([112.55, 112.56])

['high']: numpy.array([112.55, 112.56])

['low']: numpy.array([112.55, 112.56])

['close']: numpy.array([112.55, 112.56])

['volume']: numpy.array([189, 114])
    }

Put trade strategy here

#return dictionary, or list of dictionaries, in this format to make a trade

if trade:
return {

'execute': True,

'score': 100, trade with the highest score gets executed

'date': datetime(2021, 05, 05, 20, 06),

'direction': 1, 0 for short, 1 for long

'stop_loss': 112.05,

'take_profit': 112.77,

'gran': M30,

'pair': USD_JPY

}
    
#return None if no trades to make

if not trade:

return None

