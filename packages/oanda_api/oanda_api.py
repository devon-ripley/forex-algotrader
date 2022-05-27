import requests
import logging
import time
from datetime import datetime
from datetime import timedelta
from decimal import *
logger = logging.getLogger('forexlogger')
# add in better data verification

def account_get_init(apikey):
    logger.info('Running OandaApi initial connection')
    # Connect to oanda api, account get
    url = 'https://api-fxpractice.oanda.com/v3/accounts'
    headers = {'Authorization': apikey}

    req = requests.get(url, headers=headers)
    req.json()

    logger.info(f'Oanda Api Authentication Check: {req.status_code}')
    logger.info(req.json())
    if req.status_code == 200:
        logger.info('Oanda Api connection successful')
        acc_info = req.json()
        account_id = acc_info['accounts']
        account_id = account_id[0]
        account_id = account_id['id']
        return account_id
    # !!!!Error connecting loop 5 times with 5 sec wait
    if req.status_code != 200:
        logger.warning('First attempt at initial Oanda connection failed, retrying')
        for c in range(6):
            time.sleep(5)
            url = 'https://api-fxpractice.oanda.com/v3/accounts'
            headers = {'Authorization': apikey}

            req = requests.get(url, headers=headers)
            req.json()

            logger.info(f'Oanda Api Authentication Check: {req.status_code}')
            if req.status_code == 200:
                logger.info('Oanda Api connection successful')
                return ()
        logger.critical('Unable to connect to Oanda')

        #######################################################################################################################


def instrument_candles(apikey, pair, gran, start, end):
    url = 'https://api-fxpractice.oanda.com/v3/instruments/' + pair + '/candles?' + '&from=' + start + '&to=' + end + '&granularity=' + gran
    headers = {'Authorization': apikey, 'Accept-Datetime-Format': 'RFC3339'}

    ### Add in proper api request info
    req = requests.get(url, headers=headers)
    req.json()
    if req.status_code == 200:
        return req.json()

        # !!!!Error connecting loop 5 times with 5 sec wait
    if req.status_code != 200:
        logger.warning(f'Oanda connection failed, instrument_candles, retrying: {pair} {gran}: {req.status_code}')
        logger.warning(f'url: {url}')
        for c in range(6):
            time.sleep(5)
            req = requests.get(url, headers=headers)
            req.json()
            if req.status_code == 200:
                logger.info('Oanda Api connection successful, instrument_candles')
                return req.json()
        logger.critical('Unable to connect to Oanda: ' + url)


def instrument_candles_current(apikey, pair, gran, start):
    url = 'https://api-fxpractice.oanda.com/v3/instruments/' + pair + '/candles?' + '&from=' + start + '&granularity=' + gran
    headers = {'Authorization': apikey, 'Accept-Datetime-Format': 'RFC3339'}

    ### Add in proper api request info
    try:
        req = requests.get(url, headers=headers)
    except:
        logger.error(f'Oanda api request unsuccessful, url: {url}')
        logger.error('passing complete False and slug data')
        return {'candles': [{'complete': False, 'time': datetime(2000, 1, 1), 'volume': 0, 'mid': {'o': 0, 'h': 0, 'l': 0, 'c': 0}}]}

    if req.status_code == 200:
        return req.json()

        # !!!!Error connecting loop 5 times with 5 sec wait
    if req.status_code != 200:
        logger.warning(
            f'Oanda connection !not! 200, instrument_candles_current, retrying: {pair} {gran}: {req.status_code}')
        logger.warning(f'url: {url}')
        for c in range(6):
            time.sleep(5)
            req = requests.get(url, headers=headers)
            req.json()
            if req.status_code == 200:
                logger.info(f'Oanda Api connection successful, instrument_candles: {pair} {gran}: {req.status_code}')
                return req.json()
        logger.critical('Unable to connect to Oanda: ' + url)


def date_convert(date):
    date = str(date)
    date = date.replace(' ', 'T')
    date = date.replace(':', '%3A')
    date = date + 'Z'
    return date


def current_price(apikey, account_id, currency_pairs):
    formated = ''
    for t in currency_pairs:
        formated += t + '%2C'
    formated = formated.rstrip('%2C')
    url = 'https://api-fxpractice.oanda.com/v3/accounts/' + account_id + '/pricing?instruments=' + formated
    headers = {'Authorization': apikey, 'Accept-Datetime-Format': 'RFC3339'}
    req = requests.get(url, headers=headers)
    logger.info(f'current_price: {req.status_code}')
    return req.json()


######################### Make a order


def market_order_trend(apikey, account_id, units, currency_pair, trailing_stop):
    units = round(units)
    #### Adjust for USD_JPY###########
    trailing_stop = str(trailing_stop)
    units = str(units)
    order_info = {
        "order": {
            "trailingStopLossOnFill": {
                "distance": trailing_stop
            },
            "units": units,
            "instrument": currency_pair,
            "timeInForce": "FOK",
            "type": "MARKET",
            "positionFill": "DEFAULT"
        }
    }

    url = 'https://api-fxpractice.oanda.com/v3/accounts/' + account_id + '/orders'
    headers = {'Authorization': apikey, 'Accept-Datetime-Format': 'RFC3339', 'Content-Type': 'application/json'}
    req = requests.post(url, headers=headers, json=order_info)
    logger.info(f'market order: {req.json()}')
    return req.json()


def market_order(apikey, account_id, units, currency_pair, stop_loss, take_profit='N/A'):
    units = round(units)
    #### Adjust for USD_JPY###########
    context = Context(prec=5, rounding=ROUND_UP)
    stop_loss = context.create_decimal_from_float(stop_loss)
    stop_loss = str(stop_loss)
    if take_profit != 'N/A':
        take_profit = context.create_decimal_from_float(take_profit)
        take_profit = str(take_profit)

    if take_profit == 'N/A':
        order_info = {
            "order": {
                "stopLossOnFill": {
                    "price": stop_loss
                },
                "units": units,
                "instrument": currency_pair,
                "timeInForce": "FOK",  # check on timeinforce types for best
                "type": "MARKET",
                "positionFill": "DEFAULT"
            }
        }
    else:
        order_info = {
            "order": {
                "stopLossOnFill": {
                    "price": stop_loss
                },
                "takeProfitOnFill": {
                    "price": take_profit
                },
                "units": units,
                "instrument": currency_pair,
                "timeInForce": "FOK",
                "type": "MARKET",
                "positionFill": "DEFAULT"
            }
        }

    url = 'https://api-fxpractice.oanda.com/v3/accounts/' + account_id + '/orders'
    headers = {'Authorization': apikey, 'Accept-Datetime-Format': 'RFC3339', 'Content-Type': 'application/json'}
    req = requests.post(url, headers=headers, json=order_info)
    logger.info(f'market order: {req.json()}')
    return req.json()


def stop_order(apikey, account_id, units, currency_pair, price, stop_loss, take_profit, time_in_force):
    today_date = datetime.today()
    date = str(today_date.date())
    date = date + "T21:30:00.00Z"
    units = round(units)
    context = Context(prec=5, rounding=ROUND_UP)
    stop_loss = context.create_decimal_from_float(stop_loss)
    take_profit = context.create_decimal_from_float(take_profit)
    price = context.create_decimal_from_float(price)

    stop_loss = str(stop_loss)
    take_profit = str(take_profit)
    price = str(price)
    if take_profit is not type(float) and time_in_force == 'GTC':
        order_info = {
            "order": {
                "stopLossOnFill": {
                    "price": stop_loss
                },
                "units": units,
                "price": price,
                "instrument": currency_pair,
                "timeInForce": "GTC",
                "type": "STOP",
                "positionFill": "DEFAULT"
            }
        }
    if take_profit is type(float) and time_in_force == 'GTC':
        order_info = {
            "order": {
                "stopLossOnFill": {
                    "price": stop_loss
                },
                "takeProfitOnFill": {
                    "price": take_profit
                },
                "units": units,
                "price": price,
                "instrument": currency_pair,
                "timeInForce": "GTC",
                "type": "STOP",
                "positionFill": "DEFAULT"
            }
        }
    if time_in_force == 'GTD':
        order_info = {
            "order": {
                "stopLossOnFill": {
                    "price": stop_loss
                },
                "takeProfitOnFill": {
                    "price": take_profit
                },
                "units": units,
                "price": price,
                "instrument": currency_pair,
                "timeInForce": "GTD",
                "gtdTime": date,
                "type": "STOP",
                "positionFill": "DEFAULT"
            }
        }
    url = 'https://api-fxpractice.oanda.com/v3/accounts/' + account_id + '/orders'
    headers = {'Authorization': apikey, 'Accept-Datetime-Format': 'RFC3339', 'Content-Type': 'application/json'}
    req = requests.post(url, headers=headers, json=order_info)
    logger.info(f'stop order: {req.json()}')
    return req.json()
    # ADD ERROR HANDLING


def edit_stop_loss(apikey, account_id, order_id, stop_loss):
    context = Context(prec=5, rounding=ROUND_UP)
    stop_loss = context.create_decimal_from_float(stop_loss)
    stop_loss = str(stop_loss)
    edit_info = {"stopLoss": {"price": stop_loss}}
    url = 'https://api-fxpractice.oanda.com/v3/accounts/' + account_id + '/trades/' + order_id + '/orders'
    headers = {'Authorization': apikey, 'Accept-Datetime-Format': 'RFC3339'}
    req = requests.put(url, headers=headers, json=edit_info)
    logger.info(f'edit stop loss: {req.json()}')
    return req.json()


def cancel_order(apikey, account_id, order_id):
    url = 'https://api-fxpractice.oanda.com/v3/accounts/' + account_id + '/orders/' + order_id + '/cancel'
    headers = {'Authorization': apikey, 'Accept-Datetime-Format': 'RFC3339'}
    req = requests.put(url, headers=headers)
    logger.info(f'cancel order: {req.json()}')
    return req.status_code


def close_trade(apikey, account_id, trade_id):
    url = 'https://api-fxpractice.oanda.com/v3/accounts/' + account_id + '/trades/' + trade_id + '/close'
    headers = {'Authorization': apikey, 'Accept-Datetime-Format': 'RFC3339'}
    req = requests.put(url, headers=headers)
    logger.info(f'close trade: {req.json()}')
    return req.status_code


################################### Account info


def order_info(apikey, account_id, order_id):
    url = 'https://api-fxpractice.oanda.com/v3/accounts/' + account_id + '/orders/' + order_id
    headers = {'Authorization': apikey, 'Accept-Datetime-Format': 'RFC3339'}
    req = requests.get(url, headers=headers)
    logger.info(f'order info: {req.json()}')
    return req.json()


def account_summary(apikey, account_id):
    url = 'https://api-fxpractice.oanda.com/v3/accounts/' + account_id + '/summary'
    headers = {'Authorization': apikey, 'Accept-Datetime-Format': 'RFC3339'}
    req = requests.get(url, headers=headers)
    logger.info(f'api call account summary: {req.status_code}')
    return req.json()


def open_trades(apikey, account_id):
    url = 'https://api-fxpractice.oanda.com/v3/accounts/' + account_id + '/openTrades'
    headers = {'Authorization': apikey, 'Accept-Datetime-Format': 'RFC3339'}
    req = requests.get(url, headers=headers)
    logger.info(f'api call open trades: {req.status_code}')
    return req.json()


def trade_info(apikey, account_id, trade_id):
    url = 'https://api-fxpractice.oanda.com/v3/accounts/' + account_id + '/trades/' + trade_id
    headers = {'Authorization': apikey, 'Accept-Datetime-Format': 'RFC3339'}
    req = requests.get(url, headers=headers)
    if req.status_code != 200:
        return False
    logger.info(f'api call trade info: {req.status_code}')
    return req.json()


def all_instrument_info(apikey, account_id):
    url = 'https://api-fxpractice.oanda.com/v3/accounts/' + account_id + '/instruments'
    headers = {'Authorization': apikey, 'Accept-Datetime-Format': 'RFC3339'}
    req = requests.get(url, headers=headers)
    if req.status_code == 404:
        return False
    logger.info(f'all instrument info: {req.json()}')
    return req.json()
