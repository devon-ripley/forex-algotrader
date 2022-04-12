import os
import logging
import json

# set up folder org if not setup


def folder_setup(currency_pairs, grans):
    for x in currency_pairs:
        try:
            os.makedirs('data/csv/' + x + '/D')
        except FileExistsError:
            pass
        for t in grans:
            try:
                os.makedirs('data/csv/' + x + '/' + t)
            except FileExistsError:
                pass
    try:
        os.makedirs('log')
    except FileExistsError:
        pass
    try:
        os.makedirs('data/reports')
    except FileExistsError:
        pass
    try:
        os.makedirs('data/trade_logic')
    except FileExistsError:
        pass


def set_logger():
    logger = logging.getLogger('forexlogger')
    logger.setLevel(logging.DEBUG)

    logger.propagate = False
    formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
    file_handler = logging.FileHandler('log/out.log')
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)


def get_config():
    # system profile load
    f = open('data/config.json', 'r')
    profile = json.load(f)
    f.close()

