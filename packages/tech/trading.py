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
import talib


class Trader:
    def __init__(self, live, currency_pairs, gran, max_risk, max_use_day,
                 margin_rate, weights, apikey=None, account_id=None):
        if live:
            self.live = True
            self.apikey = apikey
            self.account_id = account_id
            trade_check_ob = []
            for x in currency_pairs:
                for t in gran:
                    trade_check_ob.append(day_trade.Live(x, t))
            self.trade_check_ob = trade_check_ob

        if not live:
            self.live = False
            trade_check_ob = []
            for x in currency_pairs:
                for t in gran:
                    trade_check_ob.append(day_trade.Past(x, t))
            self.trade_check_ob = trade_check_ob

        self.currency_pairs = currency_pairs
        self.grans = gran
        self.max_risk = max_risk
        self.max_use_day = max_use_day
        self.margin_rate = margin_rate
        self.weights = weights

    def unit_calc(self, current_price, stop_loss, unit_mult, risk_amount, max_units, margin_used, margin_rate, max_use_day):
        # calculate units
        units = risk_amount / abs(current_price - stop_loss)
        trade_margin_used = units / margin_rate
        if trade_margin_used + margin_used >= max_use_day:
            return False
        if units > max_units / 2:
            units = max_units / 2
        units = units * unit_mult
        return units

    def regular(self, price_data, active_pairs, market_reader_obs=None, track_year=None):

        # check for possible trades
        # trade ob check and run
        check_results = []
        if self.live:
            logger = logging.getLogger('forex_logger')
        for x in self.trade_check_ob:
            abort = False
            for pair in active_pairs:
                if x.currency_pair == pair:
                    abort = True
                else:
                    pass
            if not abort:
                if self.live:
                    res = x.live_candles()
                else:
                    res = x.back_candles(market_reader_obs, track_year)
                if res:
                    check_results.append(res)
                else:
                    pass
        # check results from trade ob run
        if check_results:
            # nonempty list
            score_list = []
            check_results_com = [j for i in check_results for j in i]
            for y in range(len(check_results_com)):
                score = check_results_com[y]['score']
                score_list.append(score)
            top_index = score_list.index(max(score_list))
            top_trade = check_results_com[top_index]
            # calculate stop_loss, take_profit
            local_trend = {'range': 0}
            for x in self.trade_check_ob:
                if x.currency_pair == top_trade['pair'] and x.gran == top_trade['gran']:
                    local_trend = x.trend_list
                else:
                    pass
            local_range = local_trend['range']
            current_price = 0
            for x in price_data:
                if x['instrument'] == top_trade['pair']:
                    if self.live:
                        current_price = float(x['closeoutAsk'])
                    elif not self.live:
                        current_price = x[top_trade['pair']]
            # no price info error
            if current_price == 0 and self.live:
                logger.error('price data not obtained from api')
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
            return {'current_price': current_price, 'stop_loss': stop_loss, 'take_profit': take_profit,
                    'unit_mult': unit_mult, 'local_range': local_range, 'top_trade': top_trade}
        return False


class LiveTrader(Trader):

    def trade(self, first_run):
        # live data run
        if self.live:
            logger = logging.getLogger('forexlogger')
            # get account info from oanda_api
            info = oanda_api.account_summary(self.apikey, self.account_id)
            info = info['account']
            margin_used = float(info['marginUsed'])
            balance = float(info['balance'])
            risk_amount = float(self.max_risk) * balance
            max_use_day = float(self.max_use_day) * balance
            max_units = float(self.margin_rate) * max_use_day
            margin_rate = self.margin_rate

            active_pairs = []

            # check for active trades
            active_trades_sql = trade_sql.all_active_trades()['short_term']
            active_trades_api = oanda_api.open_trades(self.apikey, self.account_id)['trades']
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
                    closed_trade_info = oanda_api.trade_info(self.apikey, self.account_id, current_id)
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
            logger.info('Currency(s) with open trades ' + str(active_pairs))
            # check for still pending trade info api to trades_sql
            trade_sql.update_pending_complete(self.apikey, self.account_id)
            # get current price data from oanda_api
            price_data = oanda_api.current_price(self.apikey, self.account_id, self.currency_pairs)
            price_data = price_data['prices']
            system_time = now.now()
            current_unix = time.time()
            current_hr = int(system_time.strftime("%H"))
            # check for trades
            run_info = self.regular(price_data, active_pairs)
            if run_info is False:
                return True
            # calculate units

            units = self.unit_calc(run_info['current_price'], run_info['stop_loss'],
                                   run_info['unit_mult'], risk_amount, max_units, margin_used, margin_rate, max_use_day)
            if units is not False:
                # execute trade
                trade_info = oanda_api.market_order(self.apikey, self.account_id, units,
                                                    run_info['top_trade']['pair'],
                                                    run_info['stop_loss'], run_info['take_profit'])
                if 'orderCancelTransaction' in trade_info:
                    reason = trade_info['orderCancelTransaction']['reason']
                    logger.error('Error market order, ' + reason)
                    notification.send('Error market order, ' + reason)
                    pass
                else:
                    trade_id = trade_info['orderFillTransaction']['id']
                    logging.info('Market order complete' + trade_id)
                    notification.send('Market order complete' + trade_id)
                    # margin_used = trade_info['orderFillTransaction']['tradeOpened']['initialMarginRequired']
                    if units >= 0:
                        direction = 'LONG'
                    else:
                        direction = 'SHORT'
                    trade_sql.add_active_trade(trade_id, run_info['top_trade']['date'],
                                               run_info['top_trade']['pair'], direction, run_info['stop_loss'],
                                               run_info['take_profit'], 'short_term_active')
                    reports.trade_logic_csv(
                        [trade_id, units, run_info['current_price'], run_info['stop_loss'], run_info['take_profit'],
                         run_info['top_trade']])
            return True

    def trend(self, apikey, account_id, currency_pairs, max_risk, max_use_trend, margin_rate):
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


class PastTrader(Trader):

    def __init__(self, live, currency_pairs, gran, max_risk, max_use_day,
                 margin_rate, weights, apikey=None, account_id=None):
        super().__init__(live, currency_pairs, gran, max_risk, max_use_day, margin_rate, weights, apikey, account_id)
        self.market_reader_obs = None
        self.active_trades = []
        self.active_pairs = []
        self.active_data = {'balance': 0, 'margin_used': 0}

    def add_market_readers(self, market_reader_obs):
        self.market_reader_obs = market_reader_obs

    def calc_profit(self, profit, units):
        profit = profit * units
        return profit

    def active_trade_check(self, track_year, price_data):
        for x in self.active_trades:
            price = self.market_reader_obs[track_year][x['pair']]['M1'].current_price
            profit = None
            if x['units'] > 0:
                # long
                if price[0] >= x['take_profit']:
                    # profit
                    profit = price[0] - x['price']
                elif price[1] <= x['stop_loss']:
                    # loss
                    profit = price[1] - x['price']
            elif x['units'] < 0:
                # short
                if price[1] <= x['take_profit']:
                    # profit
                    profit = x['price'] - price[1]
                elif price[0] >= x['stop_loss']:
                    # loss
                    profit = price[0] - x['price']
            if profit is not None:
                self.active_data['margin_used'] -= x['margin_used']
                apply_profit = self.calc_profit(profit, x['units'])
                self.active_data['balance'] += apply_profit
                self.active_pairs.remove(x['pair'])
                self.active_trades.remove(x)

    def trade_past(self, track_year, track_datetime):
        # logger = logging.getLogger('backtestlogger')
        balance = self.active_data['balance']
        risk_amount = float(self.max_risk) * balance
        max_use_day = float(self.max_use_day) * balance
        max_units = float(self.margin_rate) * max_use_day
        price_data = []
        # get track price
        for p in self.currency_pairs:
            price = self.market_reader_obs[track_year][p]['M1'].current_price
            if price is None:
                continue
            price_data.append({'instrument': p, p: (price[0] + price[1]) / 2})
        # check active trades
        self.active_trade_check(track_year, price_data)

        # run regular
        run_info = self.regular(price_data, self.active_pairs, self.market_reader_obs, track_year)
        if run_info is False:
            return True
        # calculate units
        units = self.unit_calc(run_info['current_price'], run_info['stop_loss'],
                               run_info['unit_mult'], risk_amount, max_units, self.active_data['margin_used'], self.margin_rate, max_use_day)
        # execute trade
        top_trade_price = self.market_reader_obs[track_year][run_info['top_trade']['pair']]['M1'].current_price
        top_trade_price = (top_trade_price[0] + top_trade_price[1]) / 2
        margin_used_trade = units / self.margin_rate
        self.active_data['margin_used'] += margin_used_trade
        self.active_trades.append(
            {'price': top_trade_price, 'units': units, 'margin_used': margin_used_trade, 'pair': run_info['top_trade']['pair'],
             'stop_loss': run_info['stop_loss'], 'take_profit': run_info['take_profit']})
        self.active_pairs.append(run_info['top_trade']['pair'])
