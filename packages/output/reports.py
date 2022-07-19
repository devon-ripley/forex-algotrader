import datetime
import csv
from packages.output import trade_sql
from pathlib import Path


class WeeklyReport:

    def __init__(self, apikey, account_id):
        self.apikey = apikey
        self.account_id = account_id
        self.year = datetime.datetime.now().year

    def __file_last_date(self):
        path = 'data/reports/report_' + str(self.year) + '.csv'
        with open(path, 'r') as file:
            data = csv.reader(file)
            data = list(data)
        last_line = data[-1]
        return 0

    def __week_save(self, start_date):
        # find friday!!!!
        start_date_str = str(start_date)
        end_date = start_date + datetime.timedelta(days=7)
        year_str = str(self.year)
        path_to_output = 'data/reports/report_' + year_str + '.csv'
        # get all trade info from mysql for this week
        data = trade_sql.all_complete_trades_from(start_date_str)
        # get current balance from oanda_api
        path = Path(path_to_output)
        headers = ['date', 'profit_week', 'trades_week', 'profit_year', 'trades_year', 'balance']

        # calculate total profit for week
        profit_week = 0.0
        trades_week = 0
        # first staring balance off the first trade of the week
        start_week_balance = data[-1][12]
        for x in data:
            if x[11] == 'N/A':
                continue
            profit_week += float(x[11])

            trades_week += 1
        # calculate year profit and number of trades
        total_profit = 0.0
        total_trades = 0
        if path.is_file():
            file = open(path_to_output, 'r')
            lines = file.readlines()
            file.close()
            for i, line in enumerate(lines):
                if i == 0:
                    continue
                else:
                    wk_prof = float(line[1])
                    wk_tra = int(line[2])
                    total_profit = total_profit + wk_prof
                    total_trades = total_trades + wk_tra
            total_profit = total_profit + profit_week
            total_trades = total_trades + trades_week
            report_data = {
                'date': str(end_date),
                'profit_week': profit_week,
                'trades_week': trades_week,
                'profit_year': total_profit,
                'trades_year': total_trades,
                'balance': (start_week_balance + profit_week)
            }
            # add data to file
            with open(path_to_output, 'a', newline='') as f:
                writer_object = csv.DictWriter(f, fieldnames=headers)
                writer_object.writerow(report_data)
                f.close()
        else:
            total_profit = profit_week
            total_trades = total_trades
            file = open(path_to_output, 'w')
            file.writelines(['date,profit_week,trades_week,profit_year,trades_year,balance\n',
                             f'{str(end_date)},{profit_week},{trades_week},{total_profit},{total_trades},{(start_week_balance + profit_week)}\n'])
            file.close()

    def update_report(self):
        current_date = datetime.datetime.now().date()
        last_date = self.__file_last_date()
        self.__week_save(last_date)



# not in use
def trade_logic_csv(data):
    date = datetime.datetime.now().date()
    start_of_week = date - datetime.timedelta(days=date.isoweekday())
    path_to_file = f'data/trade_logic/logic_{start_of_week}.csv'
    path = Path(path_to_file)
    if path.is_file():
        pass
    else:
        file = open(path_to_file, 'w')
        file.write('trade_id,units,price,stop_loss,take_profit,candle_pattern_dict')
        file.close()
    with open(path_to_file, 'a', newline='') as f:
        writer_object = csv.writer(f)
        writer_object.writerow(data)
        f.close()