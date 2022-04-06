import datetime
import csv
from packages.output import trade_sql
from pathlib import Path


def end_of_week():
    date = datetime.datetime.now().date()
    start_date = date - datetime.timedelta(days=7)
    start_date_str = str(start_date)
    date_str = str(date)
    path_to_output = 'data/reports/' + date_str + '.csv'
    data = trade_sql.all_complete_trades_from(start_date_str)
    profit = 0
    for x in data:
        profit += float(x[11])
    file = open(path_to_output, 'w')
    file.write(str(profit))
    file.close()


def trade_logic_csv(data):
    date = datetime.datetime.now().date()
    start_of_week = date - datetime.timedelta(days=date.isoweekday())
    print(start_of_week)
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