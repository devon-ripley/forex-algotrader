import json
import logging

def run():
    logger = logging.getLogger('forexlogger')
    input('this will erase your current weights json file')
    f = open('data/config.json', 'r')
    profile = json.load(f)
    f.close()

    # load variables
    currency_pairs = profile['currencypairs']
    currency_pairs = list(currency_pairs.split(','))
    gran = profile['gran']
    gran = list(gran.split(','))
    gran.append('D')
    # set up json
    # edit next line to add candle patterns
    candle_dict = {'candle_single': {'hammer': {'weight': 1, 'conformation': False},
                                     'hanging_man': {'weight': 1, 'conformation': False}}}
    gran_dict = {}
    for x in gran:
        candle_dict.update({'periods': 80})
        gran_dict[x] = candle_dict
    currency_dict = {}
    for x in currency_pairs:
        currency_dict[x] = gran_dict
    json_final = {'currency_pairs': currency_dict}
    with open('data/weights.json', 'w') as fp:
        json.dump(json_final, fp,  indent=4)
    logger.info('weights.json reset')
