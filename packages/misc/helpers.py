import os
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
