import logging
from packages.oanda_api import oanda_api
from packages.tech import trade_check, ai_neat
import time
from datetime import datetime as now
from packages.output import trade_sql, notification, market_csv, reports
from decimal import Decimal
import decimal


class Trader:
    def __init__(self, live, currency_pairs, gran, max_risk, max_use_day,
                 margin_rate, periods, apikey=None, account_id=None):
        trade_check_ob = {}
        if live:
            self.live = True
            self.apikey = apikey
            self.account_id = account_id
            for x in currency_pairs:
                trade_check_ob[x] = {}
                for t in gran:
                    trade_check_ob[x][t] = trade_check.Live(x, t, periods)
            self.trade_check_ob = trade_check_ob

        if not live:
            self.live = False
            trade_check_ob = {}
            for x in currency_pairs:
                trade_check_ob[x] = {}
                for t in gran:
                    trade_check_ob[x][t] = trade_check.Past(x, t, periods)
            self.trade_check_ob = trade_check_ob

        self.currency_pairs = currency_pairs
        self.grans = gran
        self.max_risk = max_risk
        self.max_use_day = max_use_day
        self.margin_rate = margin_rate

    def unit_calc(self, current_price, stop_loss, unit_mult, risk_amount, max_units, margin_used, margin_rate,
                  max_use_day):
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
        for pair in self.currency_pairs:
            if pair in active_pairs:
                continue
            for g in self.grans:
                if self.live:
                    res = self.trade_check_ob[pair][g].live_candles()
                else:
                    res = self.trade_check_ob[pair][g].back_candles(market_reader_obs, track_year)
                if res is not None:
                    check_results.append(res)
                else:
                    pass
        # check results from trade ob run
        if check_results:
            # nonempty list
            score_list = []
            for pos_trade in check_results:
                score_list.append(pos_trade['score'])

            top_index = score_list.index(max(score_list))
            top_trade = check_results[top_index]
            # calculate stop_loss, take_profit
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
                unit_mult = -1
            else:
                # long
                unit_mult = 1
            return {'current_price': current_price, 'stop_loss': top_trade['stop_loss'],
                    'take_profit': top_trade['take_profit'],
                    'unit_mult': unit_mult, 'top_trade': top_trade}
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

                elif 'orderRejectTransaction' in trade_info:
                    reason = trade_info['orderRejectTransaction']['rejectReason']
                    logger.error('Error market order, ' + reason)
                    notification.send('Error market order, ' + reason)

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


class PastTrader(Trader):

    def __init__(self, live, currency_pairs, gran, max_risk, max_use_day,
                 margin_rate, weights, step_str, apikey=None, account_id=None):
        super().__init__(live, currency_pairs, gran, max_risk, max_use_day, margin_rate, weights, apikey, account_id)
        self.market_reader_obs = None
        self.active_trades = []
        self.active_pairs = []
        self.active_data = {'balance': 0, 'margin_used': 0, 'total_trades': 0}
        self.step_str = step_str

    def add_market_readers(self, market_reader_obs):
        self.market_reader_obs = market_reader_obs

    def calc_profit(self, profit, units):
        profit = profit * abs(units)
        return profit

    def active_trade_check(self, track_year, price_data):
        for x in self.active_trades:
            price_current = self.market_reader_obs[track_year][x['pair']][self.step_str].current_price
            profit = None
            if x['units'] > 0:
                # long
                if price_current[0] >= x['take_profit']:
                    # profit
                    profit = x['take_profit'] - x['price']
                elif price_current[1] <= x['stop_loss']:
                    # loss
                    profit = x['stop_loss'] - x['price']
            elif x['units'] < 0:
                # short
                if price_current[1] <= x['take_profit']:
                    # profit
                    profit = x['price'] - x['take_profit']
                elif price_current[0] >= x['stop_loss']:
                    # loss
                    profit = x['price'] - x['stop_loss']
            if profit is not None:
                self.active_data['margin_used'] -= x['margin_used']
                apply_profit = self.calc_profit(profit, x['units'])
                self.active_data['balance'] = round(self.active_data['balance'] + apply_profit)
                self.active_pairs.remove(x['pair'])
                self.active_trades.remove(x)
                self.active_data['total_trades'] += 1

    def trade_past(self, track_year, track_datetime):
        # logger = logging.getLogger('backtestlogger')
        balance = self.active_data['balance']
        risk_amount = float(self.max_risk) * balance
        max_use_day = float(self.max_use_day) * balance
        max_units = float(self.margin_rate) * max_use_day
        price_data = []
        # get track price
        for p in self.currency_pairs:
            price = self.market_reader_obs[track_year][p][self.step_str].current_price
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
                               run_info['unit_mult'], risk_amount, max_units, self.active_data['margin_used'],
                               self.margin_rate, max_use_day)
        # execute trade
        top_trade_price = self.market_reader_obs[track_year][run_info['top_trade']['pair']][self.step_str].current_price
        top_trade_price = (top_trade_price[0] + top_trade_price[1]) / 2
        margin_used_trade = units / self.margin_rate
        self.active_data['margin_used'] += margin_used_trade
        self.active_trades.append(
            {'price': top_trade_price, 'units': units, 'margin_used': margin_used_trade,
             'pair': run_info['top_trade']['pair'],
             'stop_loss': run_info['stop_loss'], 'take_profit': run_info['take_profit']})
        self.active_pairs.append(run_info['top_trade']['pair'])


class NeatRawPastTrader(PastTrader):
    def __init__(self, live, currency_pairs, gran, max_risk, max_use_day,
                 margin_rate, weights, step_str):
        super(NeatRawPastTrader, self).__init__(self, live, currency_pairs, gran, max_risk, max_use_day,
                                                margin_rate, weights, step_str)
        self.last_pass_balance = self.active_data['balance']
        self.range_dict = {}

    def reset(self, balance):
        self.active_trades = []
        self.active_pairs = []
        self.active_data = {'balance': balance, 'margin_used': 0, 'total_trades': 0}
        self.last_pass_balance = balance
        self.range_dict = {}

    def price_data(self, track_year):
        price_data = []
        for p in self.currency_pairs:
            price = self.market_reader_obs[track_year][p][self.step_str].current_price
            if price is None:
                continue
            price_data.append({'instrument': p, p: (price[0] + price[1]) / 2})
        return price_data

    def calc_stop_take(self, pair,price, direction):
        range = self.range_dict[pair]
        if direction == 0:
            # short
            stop_loss = price + range
            take_profit = price - range
        else:
            # long
            stop_loss = price - range
            take_profit = price + range

        return stop_loss, take_profit

    def format_results(self,data, ind_len):
        indicator_res = []
        for k in data.keys():
            if type(data[k]) == type(dict):
                for under_k in data[k].keys():
                    temp_data = data[k][under_k]
                    cut = temp_data[-ind_len:]
                    indicator_res = indicator_res + cut
            else:
                temp_data = data[k]
                cut = temp_data[-ind_len:]
                indicator_res = indicator_res + cut
        return indicator_res

    def format_neat_outputs(self, outputs, track_year):
        trade_results = {}
        for x, pair in enumerate(self.currency_pairs):
            price = self.market_reader_obs[track_year][pair][self.step_str].current_price
            price = (price[0] + price[1]) / 2
            if outputs[x] > 0.5:
                # long
                stop, take = self.calc_stop_take(pair, price, direction=1)
                trade_results[pair] = {'execute': True, 'price': price, 'unit_mult': 1, 'stop_loss': stop, 'take_profit': take}
            elif outputs[x] < -0.5:
                # short
                stop, take = self.calc_stop_take(pair, price, direction=0)
                trade_results[pair] = {'execute': True, 'price': price, 'unit_mult': -1, 'stop_loss': stop, 'take_profit': take}
            else:
                # No trade
                trade_results[pair] = {'execute': False}
        return trade_results

    def NEAT_raw_indicators(self, price_data, active_pairs, market_reader_obs, track_year, per_gran_num, ind_len):
        indicator_results = []
        # get indicators for only pairs with non-active trades
        for pair in self.currency_pairs:
            for g in self.grans:
                #if pair in active_pairs:
                #    indicator_results.append(0 for i in per_gran_num)

                res = self.trade_check_ob[pair][g].back_candles(self.market_reader_obs, track_year)
                ind = res['indicators']
                if g == self.grans[-1]:
                    self.range_dict[pair] = float(ind['atr'][-1])
                # format results
                formatted = self.format_results(ind, ind_len)
                indicator_results = indicator_results + formatted
        return indicator_results

    def tradeinput(self, track_year, per_gran_num, ind_len):
        balance = self.active_data['balance']
        self.last_pass_balance = self.active_data['balance']
        risk_amount = float(self.max_risk) * balance
        max_use_day = float(self.max_use_day) * balance
        max_units = float(self.margin_rate) * max_use_day
        price_data = []
        # get track price
        for p in self.currency_pairs:
            price = self.market_reader_obs[track_year][p][self.step_str].current_price
            if price is None:
                continue
            price_data.append({'instrument': p, p: (price[0] + price[1]) / 2})
        # check active trades
        self.active_trade_check(track_year, price_data)

        # return inputs for neat, raw indicator data
        return self.NEAT_raw_indicators(price_data, self.active_pairs, self.market_reader_obs,
                                        track_year, per_gran_num, ind_len)

    def tradeoutput(self, track_year, neat_outputs):
        balance = self.active_data['balance']
        risk_amount = float(self.max_risk) * balance
        max_use_day = float(self.max_use_day) * balance
        max_units = float(self.margin_rate) * max_use_day
        # Turn neat_outputs into run_info
        runs_info = self.format_neat_outputs(neat_outputs, track_year)
        for x, pair in enumerate(self.currency_pairs):
            if runs_info[pair]['execute'] is False or pair in self.active_pairs:
                continue
            run_info = runs_info[pair]

            units = self.unit_calc(run_info['price'], run_info['stop_loss'],
                                   run_info['unit_mult'], risk_amount, max_units, self.active_data['margin_used'],
                                   self.margin_rate, max_use_day)
            # execute trade
            margin_used_trade = units / self.margin_rate
            self.active_data['margin_used'] += margin_used_trade
            self.active_trades.append(
                {'price': run_info['price'], 'units': units, 'margin_used': margin_used_trade,
                 'pair': pair,
                 'stop_loss': run_info['stop_loss'], 'take_profit': run_info['take_profit']})
            self.active_pairs.append(pair)
