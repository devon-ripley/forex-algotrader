import datetime
import csv
from packages.output import trade_sql
from pathlib import Path


def end_of_week():
    date = datetime.datetime.now().date()
    year = date.year
    start_date = date - datetime.timedelta(days=7)
    start_date_str = str(start_date)
    year_str = str(year)
    path_to_output = 'data/reports/report_' + str(date) + '.csv'
    # get all trade info from mysql for this week
    data = trade_sql.all_complete_trades_from(start_date_str)

    path = Path(path_to_output)
    headers = ['date', 'profit_week', 'trades_week', 'profit_year', 'trades_year']

    # calculate total profit for week
    profit_week = 0.0
    trades_week = len(data)
    for x in data:
        profit_week += float(x[11])
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
            'date': str(date),
            'profit_week': profit_week,
            'trades_week': trades_week,
            'profit_year': total_profit,
            'trades_year': total_trades
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
        file.writelines(['date,profit_week,trades_week,profit_year,trades_year\n',
                         f'{str(date)},{profit_week},{trades_week},{total_profit},{total_trades}\n'])
        file.close()


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