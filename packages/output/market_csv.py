# imports
import itertools
import os
import sys

import numpy
from datetime import datetime as now
import csv
import datetime
from packages.oanda_api import oanda_api
from packages.misc import helpers
import logging
import time
from pathlib import Path
# Add in data verification


def current_year_check(currency_pair, gran):
    logger = logging.getLogger('forexlogger')
    # check if files exist
    # get year
    year = str(datetime.datetime.today().year)
    # check for files
    path_to_file = 'data/csv/' + currency_pair + '/' + gran + '/' + currency_pair + gran + '_' + year + '.csv'
    path = Path(path_to_file)
    if path.is_file():
        logger.debug(f'current_year_check, file exists: {path_to_file}')
        return True
    else:
        logger.warning(f'current_year_check, file does not exist: {path_to_file}')
        return False


def current_year_setup(apikey, currency_pair, gran):
    logger = logging.getLogger('forexlogger')
    # set up current year csv file to current time
    year = int(datetime.datetime.today().year)
    current_unix = time.time()
    today_struct = time.localtime(current_unix)
    day = time.strftime('%w', today_struct)
    day = int(day)
    today_date = datetime.date.today()
    today_datetime = datetime.datetime.now()
    yesterday = today_date - datetime.timedelta(days=1)
    # get first sunday of the year
    first_of_year = datetime.date(year=year, month=1, day=1)
    first_of_year_week = first_of_year.weekday()
    while first_of_year_week != 6:
        first_of_year += datetime.timedelta(days=1)
        first_of_year_week = first_of_year.weekday()
    last_of_year = datetime.date(year=year, month=12, day=31)
    last_of_year_week = last_of_year.weekday()
    while last_of_year_week != 6:
        last_of_year -= datetime.timedelta(days=1)
        last_of_year_week = last_of_year.weekday()
    current_year_start = first_of_year
    year_str = str(year)
    csv_file_path = 'data/csv/' + currency_pair + '/' + gran + '/' + currency_pair + gran + '_' + year_str + '.csv'
    # write new file
    csv_file = open(csv_file_path, 'x')
    csv_file.close()
    nextday = current_year_start
    # use for switch to current day update
    yesterday_day = datetime.datetime.weekday(yesterday)
    # find end of week for first week

    check = True
    last_week = False
    spinner = itertools.cycle(['-', '/', '|', '\\'])
    logger.info(f'Setting up market data csv file for {currency_pair}, {gran}, {year}')
    while check:
        sys.stdout.write(next(spinner))
        sys.stdout.flush()
        sys.stdout.write('\b')
        start = nextday
        end = nextday + datetime.timedelta(days=1)
        start_str = str(start)
        end_str = str(end)
        start_str = start_str + 'T00%3A00%3A00.000000000Z'
# match current time - partial candle
        end_str = end_str + 'T00%3A00%3A00.000000000Z'
        day_data = oanda_api.instrument_candles(apikey, currency_pair, gran, start_str, end_str)
        day_data = day_data['candles']
        # build list for each line and add to csv file
        for j in range(len(day_data)):
            day_data_strip = day_data[j]
            day_data_mid = day_data_strip['mid']
            day_data_mid_list = [day_data_mid['o'], day_data_mid['h'], day_data_mid['l'], day_data_mid['c']]
            day_data_list = [day_data_strip['complete'], day_data_strip['volume'],
                             day_data_strip['time']] + day_data_mid_list
            with open(csv_file_path, 'a', newline='') as f:
                writer_object = csv.writer(f)
                writer_object.writerow(day_data_list)
                f.close()
        # check = False if on current day
        if nextday == yesterday:
            check = False
        cur_day = datetime.datetime.weekday(nextday)
        nextday = nextday + datetime.timedelta(days=1)
        if nextday + datetime.timedelta(days=2) >= today_date:
            check = False
        if cur_day == 4:
            if last_week:
                check = False
            nextday += datetime.timedelta(days=1)
        # check = False if on last day of year
        if nextday == last_of_year:
            last_week = True

    # do current day
    if day == 1:
        today_date = today_date - datetime.timedelta(days=1)
    today_str = str(today_date)
    today_start = today_str + 'T00%3A00%3A00.000000000Z'
    today_data = oanda_api.instrument_candles_current(apikey, currency_pair, gran, today_start)
    today_data = today_data['candles']
    for j in range(len(today_data)):
        day_data_strip = today_data[j]
        complete = day_data_strip['complete']
        day_data_mid = day_data_strip['mid']
        day_data_mid_list = [day_data_mid['o'], day_data_mid['h'], day_data_mid['l'], day_data_mid['c']]
        day_data_list = [day_data_strip['complete'], day_data_strip['volume'],
                         day_data_strip['time']] + day_data_mid_list
        if not complete:
            break
        with open(csv_file_path, 'a', newline='') as f:
            writer_object = csv.writer(f)
            writer_object.writerow(day_data_list)
            f.close()
    logger.info(f'current year csv complete: {csv_file_path}')


def current_year_complete(apikey, currency_pair, gran):
    logger = logging.getLogger('forexlogger')
    # complete current week csv file, if needed
    year = int(datetime.datetime.today().year)
    year_str = str(year)
    week_day = int(datetime.datetime.now().weekday())
    current_datetime = now.now()
    today_date = datetime.date.today()
    yesterday = today_date - datetime.timedelta(days=1)
    csv_file_path = 'data/csv/' + currency_pair + '/' + gran + '/' + currency_pair + gran + '_' + year_str + '.csv'
# get last date in file
    file = open(csv_file_path, "r")
    line_count = 0
    for line in file:
        if line != "\n":
            line_count += 1
    file.close()
    count = 0
    final = None
    last_of_year = datetime.date(year=year, month=12, day=31)
    last_of_year_week = last_of_year.weekday()
    while last_of_year_week != 6:
        last_of_year -= datetime.timedelta(days=1)
        last_of_year_week = last_of_year.weekday()
    with open(csv_file_path, newline='') as csv_file:
        data = csv.reader(csv_file)
        for row in data:
            count = count + 1
            if count == line_count:
                final = row
                final = final[2]
    if final is None:
        day = current_datetime.date()
        final = str(day) + 'T00:00:00.000Z'
    final = str(final)
# convert final to datetime format
    frm_end = final.replace('T', ' ')
    frm_end = frm_end.split('.', 1)
    frm_end = frm_end[0]
    frm_end = datetime.datetime.strptime(frm_end, '%Y-%m-%d %H:%M:%S')
    last_file_time = frm_end
    if gran[0] == 'M':
        # seperate number from letter
        gran_num = gran.replace('M', '')
        gran_num = int(gran_num)
        gran_time = datetime.timedelta(minutes=gran_num)
    if gran[0] == 'H':
        # seperate number from letter
        gran_num = gran.replace('H', '')
        gran_num = int(gran_num)
        gran_time = datetime.timedelta(hours=gran_num)
    start = frm_end + gran_time
    nextday = start
    start_rfc = oanda_api.date_convert(start)
# check if current week file is up to date
    last_time_current = last_file_time + gran_time + gran_time
    if current_datetime < last_time_current:
        logger.debug(f'Current year csv file is up to date: {currency_pair, gran}')
        return
# if final is within 24 hrs of current time, run oanda_api.instrument_candles_current, add to csv file
    end_tom = last_file_time + datetime.timedelta(days=1)
    if end_tom >= current_datetime or week_day == 6:
        logger.debug(f'Current year csv file is within 24 hrs of current time, {currency_pair, gran}')
        today_data = oanda_api.instrument_candles_current(apikey, currency_pair, gran, start_rfc)
        today_data = today_data['candles']
        for j in range(len(today_data)):
            day_data_strip = today_data[j]
            complete = day_data_strip['complete']
            day_data_mid = day_data_strip['mid']
            day_data_mid_list = [day_data_mid['o'], day_data_mid['h'], day_data_mid['l'], day_data_mid['c']]
            day_data_list = [day_data_strip['complete'], day_data_strip['volume'],
                             day_data_strip['time']] + day_data_mid_list
            if not complete:
                break
            with open(csv_file_path, 'a', newline='') as f:
                writer_object = csv.writer(f)
                writer_object.writerow(day_data_list)
                f.close()
        return
# if final is more then 24 hrs in the past
# run oanda_api.instrument_candles in 24hr increments until within 24 hrs of current time
    if end_tom < current_datetime:
        logger.debug(f'Current year csv file is more then 24 hrs of current time, {currency_pair, gran}')
    check = True
    last_week = False
    while check:
        start = nextday
        end = nextday + datetime.timedelta(days=1)
        start_str = str(start)
        end_str = str(end)
        start_str = start_str + 'T00%3A00%3A00.000000000Z'
# match current time - partial candle
        end_str = end_str + 'T00%3A00%3A00.000000000Z'
        day_data = oanda_api.instrument_candles(apikey, currency_pair, gran, start_str, end_str)
        day_data = day_data['candles']
        # build list for each line and add to csv file
        for j in range(len(day_data)):
            day_data_strip = day_data[j]
            day_data_mid = day_data_strip['mid']
            day_data_mid_list = [day_data_mid['o'], day_data_mid['h'], day_data_mid['l'], day_data_mid['c']]
            day_data_list = [day_data_strip['complete'], day_data_strip['volume'],
                             day_data_strip['time']] + day_data_mid_list
            with open(csv_file_path, 'a', newline='') as f:
                writer_object = csv.writer(f)
                writer_object.writerow(day_data_list)
                f.close()
        # check = False if on current day
        end_check = end + datetime.timedelta(days=1) # added a day???
        if end_check >= current_datetime:
            check = False
        cur_day = datetime.datetime.weekday(nextday)
        nextday = nextday + datetime.timedelta(days=1)
        if cur_day == 4:
            if last_week:
                check = False
            nextday += datetime.timedelta(days=1)
        # check = False if on last day of year
        if nextday == last_of_year:
            last_week = True

    # do current day
    today_str = str(today_date)
    today_start = today_str + 'T00%3A00%3A00.000000000Z'
    today_data = oanda_api.instrument_candles_current(apikey, currency_pair, gran, today_start)
    today_data = today_data['candles']
    for j in range(len(today_data)):
        day_data_strip = today_data[j]
        complete = day_data_strip['complete']
        day_data_mid = day_data_strip['mid']
        day_data_mid_list = [day_data_mid['o'], day_data_mid['h'], day_data_mid['l'], day_data_mid['c']]
        day_data_list = [day_data_strip['complete'], day_data_strip['volume'],
                         day_data_strip['time']] + day_data_mid_list
        if not complete:
            break
        with open(csv_file_path, 'a', newline='') as f:
            writer_object = csv.writer(f)
            writer_object.writerow(day_data_list)
            f.close()

## years back check and setup


def past_years_check(apikey, currency_pair, gran, start_year):
    logger = logging.getLogger('forexlogger')
    # fix last sunday of year
    year = int(datetime.datetime.today().year)
    dif = year - start_year
    for x in range(dif):######????????
        year_str = str(start_year)
        csv_file_path = 'data/csv/' + currency_pair + '/' + gran + '/' + currency_pair + gran + '_' + year_str + '.csv'
        path = Path(csv_file_path)
        if path.is_file():
            logger.debug(f'past_years, file exists for: {csv_file_path}')
            start_year += 1
            continue
        else:
            logger.warning(f'past_years, file does not exist for: {csv_file_path}, setting up file')
            # set up file
            first_of_year = datetime.date(year=start_year, month=1, day=1)
            first_of_year_week = first_of_year.weekday()
            while first_of_year_week != 6:
                first_of_year += datetime.timedelta(days=1)
                first_of_year_week = first_of_year.weekday()
            last_of_year = datetime.date(year=start_year, month=12, day=31)
            last_of_year_week = last_of_year.weekday()
            while last_of_year_week !=6:
                last_of_year -= datetime.timedelta(days=1)
                last_of_year_week = last_of_year.weekday()
            current_year_start = first_of_year
            csv_file = open(csv_file_path, 'x')
            csv_file.close()
            nextday = current_year_start
            # find end of week for first week
            check = True
            last_week = False
            spinner = itertools.cycle(['-', '/', '|', '\\'])
            logger.info(f'Setting up market data csv file for {currency_pair}, {gran}, {start_year}')
            while check:
                sys.stdout.write(next(spinner))
                sys.stdout.flush()
                sys.stdout.write('\b')

                start = nextday
                end = nextday + datetime.timedelta(days=1)
                start_str = str(start)
                end_str = str(end)
                start_str = start_str + 'T00%3A00%3A00.000000000Z'
                # match current time - partial candle
                end_str = end_str + 'T00%3A00%3A00.000000000Z'
                day_data = oanda_api.instrument_candles(apikey, currency_pair, gran, start_str, end_str)
                day_data = day_data['candles']
                # build list for each line and add to csv file
                for j in range(len(day_data)):
                    day_data_strip = day_data[j]
                    day_data_mid = day_data_strip['mid']
                    day_data_mid_list = [day_data_mid['o'], day_data_mid['h'], day_data_mid['l'], day_data_mid['c']]
                    day_data_list = [day_data_strip['complete'], day_data_strip['volume'],
                                     day_data_strip['time']] + day_data_mid_list
                    with open(csv_file_path, 'a', newline='') as f:
                        writer_object = csv.writer(f)
                        writer_object.writerow(day_data_list)
                        f.close()
                cur_day = datetime.datetime.weekday(nextday)
                nextday = nextday + datetime.timedelta(days=1)
                if cur_day == 4:
                    if last_week:
                        check = False
                    nextday += datetime.timedelta(days=1)
                # check = False if on last day of year
                if nextday == last_of_year:
                    last_week = True
            start_year += 1
        logger.info(f'{csv_file_path} is setup')

def daily_check(currency_pair, year):
    logger = logging.getLogger('forexlogger')
    year_str = str(year)
    #check for files
    path_to_file = 'data/csv/' + currency_pair + '/D/' + currency_pair + 'D' + '_' + year_str + '.csv'
    path = Path(path_to_file)
    if path.is_file():
        logger.debug(f'D1 file exists: {path_to_file}')
        return True
    else:
        logger.warning(f'D1 file does not exist: {path_to_file}')
        return False


def daily_setup(apikey, currency_pair, year):
    logger = logging.getLogger('forexlogger')
    current_year = datetime.datetime.now().year
    year_str = str(year)
    csv_file_path = 'data/csv/' + currency_pair + '/D/' + currency_pair + 'D' + '_' + year_str + '.csv'
    start = year_str + '-01-01T00%3A00%3A00Z'
    if current_year == year:
        day_data = oanda_api.instrument_candles_current(apikey, currency_pair, 'D', start)
    else:
        day_data = oanda_api.instrument_candles(apikey, currency_pair, 'D', start, str(year+1)+'-01-01T00%3A00%3A00Z')
    day_data = day_data['candles']
    # build list for each line and add to csv file
    complete = True
    spinner = itertools.cycle(['-', '/', '|', '\\'])
    logger.info(f'Setting up market data csv file for {currency_pair}, D, {year}')
    for j in range(len(day_data)):
        sys.stdout.write(next(spinner))
        sys.stdout.flush()
        sys.stdout.write('\b')
        day_data_strip = day_data[j]
        complete = day_data_strip['complete']
        day_data_mid = day_data_strip['mid']
        day_data_mid_list = [day_data_mid['o'], day_data_mid['h'], day_data_mid['l'], day_data_mid['c']]
        day_data_list = [day_data_strip['complete'], day_data_strip['volume'],
                         day_data_strip['time']] + day_data_mid_list
        if not complete:
            return
        with open(csv_file_path, 'a', newline='') as f:
            writer_object = csv.writer(f)
            writer_object.writerow(day_data_list)
            f.close()
    logger.info(f'current day file complete: {csv_file_path}')


def daily_current(apikey, currency_pair, year):
    logger = logging.getLogger('forexlogger')
    current_day = now.now()
    year_str = str(year)
    csv_file_path = 'data/csv/' + currency_pair + '/D/' + currency_pair + 'D' + '_' + year_str + '.csv'
    # get last date in file
    file = open(csv_file_path, "r")
    line_count = 0
    for line in file:
        if line != "\n":
            line_count += 1
    file.close()
    count = 0
    final = None
    with open(csv_file_path, newline='') as csv_file:
        data = csv.reader(csv_file)
        for row in data:
            count = count + 1
            if count == line_count:
                final = row
                final = final[2]
    frm_end = final.replace('T', ' ')
    frm_end = frm_end.split('.', 1)
    frm_end = frm_end[0]
    frm_end = datetime.datetime.strptime(frm_end, '%Y-%m-%d %H:%M:%S')
    start = frm_end + datetime.timedelta(days=1)
    start_rfc = oanda_api.date_convert(start)
    if start.year > year:
        return

    if current_day.year == year:
        logger.debug(f'Current year file updating, {currency_pair}, D')
        today_data = oanda_api.instrument_candles_current(apikey, currency_pair, 'D', start_rfc)
    else:
        today_data = oanda_api.instrument_candles(apikey, currency_pair, 'D',
                                                  start_rfc, str(year+1)+'-01-01T00%3A00%3A00Z')
    today_data = today_data['candles']
    for j in range(len(today_data)):
        day_data_strip = today_data[j]
        complete = day_data_strip['complete']
        day_data_mid = day_data_strip['mid']
        day_data_mid_list = [day_data_mid['o'], day_data_mid['h'], day_data_mid['l'], day_data_mid['c']]
        day_data_list = [day_data_strip['complete'], day_data_strip['volume'],
                         day_data_strip['time']] + day_data_mid_list
        if not complete:
            break
        with open(csv_file_path, 'a', newline='') as f:
            writer_object = csv.writer(f)
            writer_object.writerow(day_data_list)
            f.close()
    return
# read

def csv_read_full(currency_pair, gran, year):

    year_str = str(year)
    csv_file_path = 'data/csv/' + currency_pair + '/' + gran + '/' + currency_pair + gran + '_' + year_str + '.csv'
    with open(csv_file_path, newline='') as f:
        reader = csv.reader(f)
        data = list(reader)

    result_dict = {'date': []}

    length = len(data)
    open_lst = []
    high_lst = []
    low_lst = []
    close_lst = []
    volume_lst = []
    for idx, x in enumerate(data):# add in type checking
        open_lst.append(float(x[3]))
        high_lst.append(float(x[4]))
        low_lst.append(float(x[5]))
        close_lst.append(float(x[6]))
        volume_lst.append(int(x[1]))
        date = x[2]
        date = date.replace('T', ' ')
        date = date.split('.')
        date = date[0]
        date_ob = datetime.datetime.fromisoformat(date)
        result_dict['date'].append(date_ob)
    result_dict['open'] = numpy.array(open_lst)
    result_dict['high'] = numpy.array(high_lst)
    result_dict['low'] = numpy.array(low_lst)
    result_dict['close'] = numpy.array(close_lst)
    result_dict['volume'] = numpy.array(volume_lst)
    return result_dict


def csv_read_recent(currency_pair, gran, periods):
    year_str = str(datetime.datetime.now().year)
    csv_file_path = 'data/csv/' + currency_pair + '/' + gran + '/' + currency_pair + gran + '_' + year_str + '.csv'
    with open(csv_file_path, newline='') as f:
        reader = csv.reader(f)
        data = list(reader)

    start = len(data) - periods
    current = data[start:len(data)]
    result_dict = {
            'date': [],
            'open': numpy.array([]),
            'high': numpy.array([]),
            'low': numpy.array([]),
            'close': numpy.array([]),
            'volume': numpy.array([])
        }
    for x in current: # add in type checking
        result_dict['open'] = numpy.append(result_dict['open'], float(x[3]))
        result_dict['high'] = numpy.append(result_dict['high'], float(x[4]))
        result_dict['low'] = numpy.append(result_dict['low'], float(x[5]))
        result_dict['close'] = numpy.append(result_dict['close'], float(x[6]))
        result_dict['volume'] = numpy.append(result_dict['volume'], int(x[1]))
        date = x[2]
        date = date.replace('T', ' ')
        date = date.split('.')
        date = date[0]
        date_ob = datetime.datetime.fromisoformat(date)
        result_dict['date'].append(date_ob)
    return result_dict


def csv_date_convert(date):
    date = date.replace('T', ' ')
    date = date.split('.')
    date = date[0]
    return date
