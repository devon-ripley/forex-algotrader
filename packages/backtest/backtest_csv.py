import datetime
from packages.backtest import backtest
import numpy

from packages.output import market_csv
import json


class BacktestMarketReader:

    def __init__(self, year, pair, gran, start_date, initial_year):
        self.last_index = -1
        self.current_price = None
        self.go = False
        self.year = year
        self.pair = pair
        self.gran = gran
        self.initial_year = initial_year
        self.first = False
        self.data = market_csv.csv_read_full(pair, gran, year)
        self.date_list = self.data['date']
        if self.gran[0] == 'M':
            temp_g = self.gran.strip('M')
            step = datetime.timedelta(minutes=int(temp_g))
        elif self.gran[0] == 'H':
            temp_g = self.gran.strip('H')
            step = datetime.timedelta(hours=int(temp_g))
        elif self.gran == 'D':
            step = datetime.timedelta(days=1)
        self.step = step
        # total length
        self.total_length = len(self.data['date']) - 1
        # find start index
        for x, dt in enumerate(self.date_list):
            # file_date = market_csv.csv_date_convert(file_date)
            # dt_file_date = datetime.datetime.strptime(file_date, '%Y-%m-%d %H:%M:%S')
            if dt >= start_date:
                self.initial_index = x
                self.start_index = x
                return

            else:
                pass
        self.initial_index = 0
        self.start_index = 0
        self.first = False

    def reset(self):
        self.last_index = -1
        self.current_price = None
        self.go = False
        self.first = False
        self.start_index = self.initial_index

    def get_current_price(self):
        self.current_price = [self.data['high'][self.start_index], self.data['low'][self.start_index]]  # high, low
        return self.current_price

    def output_backchunk(self, periods):
        track_index = self.start_index
        if self.start_index < periods:
            # split year
            return {'complete': False, 'back': (periods - self.start_index)}
        else:
            cut_data_dict = {}
            start = track_index - periods
            end = track_index + 1 # ??????
            cut_data_dict['date'] = self.data['date'][start:end]
            cut_data_dict['open'] = self.data['open'][start:end]
            cut_data_dict['high'] = self.data['high'][start:end]
            cut_data_dict['low'] = self.data['low'][start:end]
            cut_data_dict['close'] = self.data['close'][start:end]
            cut_data_dict['volume'] = self.data['volume'][start:end]
            return {'complete': True, 'data': cut_data_dict}

    def go_check(self, backtest_datetime):
        self.backtest_datetime = backtest_datetime
        track_date = self.data['date'][self.start_index]
        track_date = track_date + self.step
        self.current_price = [self.data['high'][self.start_index], self.data['low'][self.start_index]]  # high, low

        if track_date <= backtest_datetime:
            self.go = True

        if self.data['date'][self.start_index] > backtest_datetime + datetime.timedelta(days=1):
            # end of week, change to own if statment, non nested???
            self.go = False

        if track_date + self.step <= backtest_datetime:
            #if self.data['date'][self.start_index] > backtest_datetime + datetime.timedelta(days=1):
                # end of week, change to own if statment, non nested???
                #print('go=False!!!!!')
                #self.go = False
            self.last_index = self.start_index
            self.start_index = self.start_index + 1


    def split_year(self, periods_back):
        cut_data_dict = {}
        length = len(self.data['date'])
        cut_data_dict['date'] = self.data['date'][length-periods_back:]
        cut_data_dict['open'] = self.data['open'][length-periods_back:]
        cut_data_dict['high'] = self.data['high'][length-periods_back:]
        cut_data_dict['low'] = self.data['low'][length-periods_back:]
        cut_data_dict['close'] = self.data['close'][length-periods_back:]
        cut_data_dict['volume'] = self.data['volume'][length-periods_back:]
        return cut_data_dict

    def new_year(self, periods):
        cut_data_dict = {}
        periods += 1

        cut_data_dict['date'] = self.data['date'][:periods]
        cut_data_dict['open'] = self.data['open'][:periods]
        cut_data_dict['high'] = self.data['high'][:periods]
        cut_data_dict['low'] = self.data['low'][:periods]
        cut_data_dict['close'] = self.data['close'][:periods]
        cut_data_dict['volume'] = self.data['volume'][:periods]

        return cut_data_dict
