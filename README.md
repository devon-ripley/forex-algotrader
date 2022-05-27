# forex-algotrader
For educational purposes only

Uses Oanda for market data and trading.

Runs on Linux, should work on windows though i will have to test it.

This program does Forex trading, I plan on adding crypto and maybe stocks in the future.

URL in packages/oanda_api/oanda_api.py set to practice account.

Mysql required to run. Set up database for program to use. Set up user with all permissions for that database. User name, password, and database name are put in data/config.json.

Notifications use yagmail python package, gmail account is required to send notifications .

I plan on adding report generation.

TA-lib required. Install info here https://github.com/mrjbq7/ta-lib

NEAT is set up to use raw indicator data to make trading decisions.

I am still working out some bugs and making it fully functional


# Arguments for forexat.py

you@yourpc:~$ python3 forexat.py --help


# GET STARTED

REMOVE TEMPLATE FROM TEMPLATE_TRADE_STRATEGY.PY BEFORE STARTING

REMOVE SAMPLE FROM DATA/SAMPLE_CONFIG.JSON BEFORE STARTING

Run forexat.py to start trading loop

Run forexat.py -b or --backtest to backtest


Put trading strategy in trade_strategy.py, format is:

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

return dictionary, or list of dictionaries, in this format to make a trade


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
    
return None if no trades to make

if not trade:

return None

