import datetime
from packages.output import market_csv
import json


def start_files(currency_pairs, grans, year):
    complete_data = {year: {}}
    for w in range(2):
        for x in currency_pairs:
            complete_data[year][x] = {}
            for t in grans:
                data = market_csv.csv_read_full(x, t, year)
                complete_data[year][x][t] = data

        year += 1
        complete_data[year] = {}
    return complete_data


def index_search(data, start_date, currency_pairs, grans, year):
    index_dict = {}
    print(currency_pairs)

    index_dict[year] = {}
    for pair in currency_pairs:
        index_dict[year][pair] = {}
        for gran in grans:
            cur_list = data[year][pair][gran]
            index_dict[year][pair][gran] = 0
            for line in cur_list:
                file_date = line[2]
                file_date = market_csv.csv_date_convert(file_date)
                dt_file_date = datetime.datetime.strptime(file_date, '%Y-%m-%d %H:%M:%S')
                if dt_file_date >= start_date:
                    start_index = data[year][pair][gran].index(line)
                    index_dict[year][pair][gran] = start_index
                    break

                else:
                    pass
    return index_dict


class BacktestMarketReader:

    def __init__(self, year, pair, gran, start_date):
        self.current_price = None
        self.go = False
        self.year = year
        self.pair = pair
        self.gran = gran
        # datetime covert
        pre_data = market_csv.csv_read_full(pair, gran, year)
        for x in pre_data:
            date = x[2]
            date = market_csv.csv_date_convert(date)
            final_date = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
            x[2] = final_date
        self.data = pre_data
        if self.gran[0] == 'M':
            temp_g = self.gran.strip('M')
            step = datetime.timedelta(minutes=int(temp_g))
        elif self.gran[0] == 'H':
            temp_g = self.gran.strip('H')
            step = datetime.timedelta(hours=int(temp_g))
        self.step = step
        # total length
        self.total_length = len(self.data) - 1
        # find start index
        for line in self.data:
            file_date = line[2]
            # file_date = market_csv.csv_date_convert(file_date)
            # dt_file_date = datetime.datetime.strptime(file_date, '%Y-%m-%d %H:%M:%S')
            if file_date >= start_date:
                self.start_index = self.data.index(line)
                print(self.start_index, self.pair, self.gran, self.year)
                return

            else:
                pass
        self.start_index = 0
        print(self.start_index, self.pair, self.gran, self.year)

    def output_backchunk(self, periods):
        track_index = self.start_index
        data_list = []
        if self.start_index < periods:
            # split year
            return ['split_year', periods - self.start_index]
        for x in range(periods, -1, -1):
            data_list.append(self.data[track_index - x])
        return data_list

    def go_check(self, track_datetime):
        track_date = self.data[self.start_index][2]
        track_date = track_date + self.step
        line = self.data[self.start_index]
        self.current_price = [float(line[4]), float(line[5])]  # high, low

        if track_date <= track_datetime:
            self.go = True
        if track_date + self.step <= track_datetime:
            if self.data[self.start_index][2] > track_datetime + datetime.timedelta(days=1):
                # end of week
                self.go = False
            self.start_index = self.start_index + 1

    def split_year(self, periods_back):
        split_data = []
        for x in range(periods_back):
            if x == 0:
                continue
            split_data.append(self.data[-x])
        return split_data

    def new_year(self, periods):
        split_data = []
        for x in range(periods):
            split_data.append(self.data[x])
        return split_data
