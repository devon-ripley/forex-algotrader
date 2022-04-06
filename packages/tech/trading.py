import logging

from packages.oanda_api import oanda_api
from packages.tech import day_trade
from packages.tech import indicator_calc
import time
import datetime
from datetime import datetime as now
from packages.output import trade_sql, notification, market_csv, reports
from decimal import Decimal
import decimal
import json
import os


def regular(apikey, account_id, currency_pairs, grans, max_risk, max_in_use, margin_rate):
    # get account summary
    info = oanda_api.account_summary(apikey, account_id)
    info = info['account']
    balance = float(info['balance'])
    risk_amount = float(max_risk) * balance
    max_use = float(max_in_use) * balance
    max_units = float(margin_rate) * balance
    trade_wait = 300
    # load trading weights json
    print(os.getcwd())
    f = open('data/weights.json', 'r')
    weights = json.load(f)
    f.close()
    # set up trade check objects live
    trade_check_ob = []
    for x in currency_pairs:
        for t in grans:
            trade_check_ob.append(day_trade.Live(x, t))
    first_run = True
    while True:
        active_pairs = []
        # update market csv
        for x in range(len(currency_pairs)):
            for x_gran in range(len(grans)):
                market_csv.current_year_complete(apikey, currency_pairs[x], grans[x_gran])
        # check for active trades
        active_trades_sql = trade_sql.all_active_trades()['short_term']
        active_trades_api = oanda_api.open_trades(apikey, account_id)['trades']
        for trade in active_trades_sql:
            current_id = trade[0]
            check = False
            for api_trade in active_trades_api:
                if current_id == api_trade['id']:
                    active_pairs.append(api_trade['instrument'])
                    check = True  # if true trade is still active

                else:
                    pass
            if not check:
                # trade closed
                closed_trade_info = oanda_api.trade_info(apikey, account_id, current_id)
                if closed_trade_info is not False:
                    # get trade info and update trade_sql
                    closed_trade_info = closed_trade_info['trade']
                    trade_sql.update_complete_trade(current_id, 'SHORT_TERM',
                                                    units=closed_trade_info['initialUnits'],
                                                    margin_used=closed_trade_info['initialMarginRequired'],
                                                    price=closed_trade_info['price'],
                                                    profit=closed_trade_info['realizedPL'],
                                                    )
                else:
                    trade_sql.update_complete_trade(current_id, 'SHORT_TERM',
                                                    units='N/A',
                                                    margin_used='N/A',
                                                    price='N/A',
                                                    profit='N/A')
                # delete from active
                trade_sql.delete_active_trade(current_id, 'short_term_active')
                if not first_run:
                    closed_pair = trade_sql.get_trade_info(current_id, 'complete')
                    try:
                        active_pairs.remove(closed_pair[2])
                    except ValueError:
                        pass
        logging.info('ACTIVE_PAIRS ' + str(active_pairs))
        print(now.now(), 'Currency(s) with open trades ' + str(active_pairs))
        # check for still pending trade info api to trades_sql
        trade_sql.update_pending_complete(apikey, account_id)
        # get current price data from oanda_api
        price_data = oanda_api.current_price(apikey, account_id, currency_pairs)
        price_data = price_data['prices']
        # get account info from oanda_api
        balance = float(info['balance'])
        risk_amount = float(max_risk) * balance
        max_use = float(max_in_use) * balance
        max_units = float(margin_rate) * max_use
        system_time = now.now()
        current_unix = time.time()
        current_hr = int(system_time.strftime("%H"))
        print(datetime.datetime.now(), 'Running regular hours trading')
        # check for possible trades
        check_results = []
        for x in trade_check_ob:
            abort = False
            for pair in active_pairs:
                if x.currency_pair == pair:
                    abort = True
                else:
                    pass
            if not abort:
                res = x.live_candles()
                if res:
                    check_results.append(res)
                else:
                    pass
        if check_results:
            print(now.now(), check_results)
            # nonempty list
            score_list = []
            check_results_com = [j for i in check_results for j in i]
            for y in range(len(check_results_com)):
                print(check_results_com[y])
                score = check_results_com[y]['score']
                score_list.append(score)
            top_index = score_list.index(max(score_list))
            top_trade = check_results_com[top_index]
            # calculate stop_loss, take_profit
            local_trend = {'range': 0}
            for x in trade_check_ob:
                if x.currency_pair == top_trade['pair'] and x.gran == top_trade['gran']:
                    local_trend = x.trend_list
                else:
                    pass
            local_range = local_trend['range']
            for x in price_data:
                if x['instrument'] == top_trade['pair']:
                    current_price = float(x['closeoutAsk'])

            if top_trade['direction'] == 0:
                # short
                stop_loss = current_price + local_range
                take_profit = current_price - local_range
                unit_mult = -1
            else:
                # long
                stop_loss = current_price - local_range
                take_profit = current_price + local_range
                unit_mult = 1
            # calculate units
            units = risk_amount / local_range
            units = units * 100
            if units > max_units:
                units = max_units
            units = units * unit_mult
            # execute trade
            trade_info = oanda_api.market_order(apikey, account_id, units, top_trade['pair'], stop_loss, take_profit)
            if 'orderCancelTransaction' in trade_info:
                reason = trade_info['orderCancelTransaction']['reason']
                logging.error('Error market order regular, ' + reason)
                notification.send('Error market order regular, ' + reason)
                break
            else:
                trade_id = trade_info['orderFillTransaction']['id']
                logging.info('Market order complete' + trade_id)
                notification.send('Market order complete' + trade_id)
                # margin_used = trade_info['orderFillTransaction']['tradeOpened']['initialMarginRequired']
                if units >= 0:
                    direction = 'LONG'
                else:
                    direction = 'SHORT'
                trade_sql.add_active_trade(trade_id, top_trade['date'], top_trade['pair'], direction, stop_loss,
                                           take_profit, 'short_term_active')
                reports.trade_logic_csv(
                    [trade_id, units, current_price, stop_loss, take_profit,
                     top_trade])

        # update current csv oanda_api data file as needed, ???one minute wait????
        print(now.now(), trade_wait)
        time.sleep(trade_wait)
        first_run = False
        if 20 <= current_hr < 23:
            pass


def trend(apikey, account_id, currency_pairs, max_risk, max_use_trend, margin_rate):
    decimal.getcontext().prec = 4
    info = oanda_api.account_summary(apikey, account_id)
    info = info['account']
    balance = float(info['balance'])
    max_use = float(max_use_trend) * balance
    risk_amount = float(max_risk) * balance
    max_units = max_use * float(margin_rate)
    info = indicator_calc.account_limits(apikey, account_id, max_use_trend, max_risk, margin_rate)
    print(info)
    price_data = oanda_api.current_price(apikey, account_id, currency_pairs)
    price_data = price_data['prices']
    currency_price = {}
    for x in price_data:
        pair = x['instrument']
        bids = x['bids']
        bids = Decimal(bids[0]['price'])
        asks = x['asks']
        asks = Decimal(asks[0]['price'])
        price = (bids + asks) / 2
        currency_price[pair] = price
    trade_data = []
    for x in currency_pairs:
        # check for trend trades
        trade_data_x = indicator_calc.trend_trade(x, currency_price, risk_amount, max_units)
        trade_data.append(trade_data_x)
    # find strongest trend
    for x in trade_data:
        print(now.now(), x)
        if x['execute']:
            if x['direction'] == 'LONG':
                units = x['units']
            elif x['direction'] == 'SHORT':
                units = x['units'] * -1.0
            dif = x['stop_loss']
            order_info = oanda_api.market_order_trend(apikey, account_id, units, x, dif)
            order_id = order_info['orderCreateTransaction']['id']
            price = order_info['orderFillTransaction']['price']
            margin_used = order_info['orderFillTransaction']['tradeOpened']['initialMarginRequired']
            notification.send([x, units, margin_used], 'Trend oanda_api order placed')
            # trade_csv.add_trade_trend(order_id, x, 'TREND', x['direction'], 'FILLED', units, margin_used, price, dif)
