import logging

import mysql.connector as mysql
import datetime
from packages.oanda_api import oanda_api
import json


def get_config_info():
    f = open('data/config.json', )
    profile = json.load(f)
    f.close()
    mysql_info = profile['mysql']
    return mysql_info


def setup():
    logger = logging.getLogger('forexlogger')
    mysql_info = get_config_info()
    create_long_table = """
    CREATE TABLE IF NOT EXISTS long_term_active (
        trade_id VARCHAR(100),
        date DATETIME(6),
        currency_pair VARCHAR(100),
        direction VARCHAR(100),
        stop_loss VARCHAR(100),
        take_profit VARCHAR(100),
        status VARCHAR(100)
    )
    """
    create_short_table = """
    CREATE TABLE IF NOT EXISTS short_term_active (
        trade_id VARCHAR(100),
        date DATETIME(6),
        currency_pair VARCHAR(100),
        direction VARCHAR(100),
        stop_loss VARCHAR(100),
        take_profit VARCHAR(100),
        status VARCHAR(100)
    )
    """

    create_complete = """
    CREATE TABLE IF NOT EXISTS complete (
        id INT AUTO_INCREMENT PRIMARY KEY,
        trade_id VARCHAR(100),
        date DATETIME(6),
        currency_pair VARCHAR(100),
        trade_type VARCHAR(100),
        direction VARCHAR(100),
        units VARCHAR(100),
        margin_used VARCHAR(100),
        price VARCHAR(100),
        stop_loss VARCHAR(100),
        take_profit VARCHAR(100),
        profit VARCHAR(100),
        status VARCHAR(100)
    )
    """
    query = [create_short_table, create_long_table, create_complete]
    with mysql.connect(
            host='localhost',
            user=mysql_info['user'],
            password=mysql_info['password'],
            database=mysql_info['database']
    ) as connection:
        logger.info(connection)

        with connection.cursor() as cursor:
            for x in query:
                cursor.execute(x)
                connection.commit()


def add_active_trade(trade_id, date, currency_pair, direction, stop_loss, take_profit, table):
    logger = logging.getLogger('forexlogger')
    mysql_info = get_config_info()
    insert_active = f"""
    INSERT INTO {table}(trade_id, date, currency_pair, direction, stop_loss, take_profit, status)
    VALUES
        ("{trade_id}", "{date}", "{currency_pair}", "{direction}", "{stop_loss}", "{take_profit}", "OPEN")
    """
    insert_complete = f"""
    INSERT INTO complete(trade_id, date, currency_pair, direction, stop_loss, take_profit, status)
    VALUES
        ("{trade_id}", "{date}", "{currency_pair}", "{direction}", "{stop_loss}", "{take_profit}", "OPEN")
    """

    with mysql.connect(
            host='localhost',
            user=mysql_info['user'],
            password=mysql_info['password'],
            database=mysql_info['database']
    ) as connection:
        logger.info(connection)
        with connection.cursor() as cursor:
            cursor.execute(insert_active)
            connection.commit()
            cursor.execute(insert_complete)
            connection.commit()


def update_complete_trade(trade_id, trade_type, units,
                       margin_used, price, profit):
    logger = logging.getLogger('forexlogger')
    mysql_info = get_config_info()

    update_complete = f"""
    UPDATE complete
    SET
    trade_type = '{trade_type}',
    units = '{units}',
    margin_used = '{margin_used}',
    price = '{price}',
    profit = '{profit}',
    status = 'CLOSED'
    WHERE
    trade_id = '{trade_id}'
    """

    with mysql.connect(
            host='localhost',
            user=mysql_info['user'],
            password=mysql_info['password'],
            database=mysql_info['database']
    ) as connection:
        logger.info(connection)
        with connection.cursor() as cursor:
            cursor.execute(update_complete)
            connection.commit()


def all_active_trades():
    mysql_info = get_config_info()
    logger = logging.getLogger('forexlogger')
    long_term = """
    SELECT *
    FROM long_term_active
"""
    short_term = """
    SELECT *
    FROM short_term_active
"""
    results = {'long_term': [], 'short_term': []}
    with mysql.connect(
            host='localhost',
            user=mysql_info['user'],
            password=mysql_info['password'],
            database=mysql_info['database']
    ) as connection:
        logger.info(connection)
        with connection.cursor() as cursor:
            cursor.execute(long_term)
            for line in cursor.fetchall():
                results['long_term'].append(line)
            cursor.execute(short_term)
            for line in cursor.fetchall():
                results['short_term'].append(line)
    return results


def all_complete_trades_from(start_date):
    mysql_info = get_config_info()
    logger = logging.getLogger('forexlogger')
    complete_all = f"""
    SELECT *
    FROM complete
    WHERE `date` BETWEEN '{start_date}' AND CURDATE()
    """
    all_data = []
    with mysql.connect(
            host='localhost',
            user=mysql_info['user'],
            password=mysql_info['password'],
            database=mysql_info['database']
    ) as connection:
        logger.info(connection)
        with connection.cursor() as cursor:
            cursor.execute(complete_all)
            for line in cursor.fetchall():
                all_data.append(line)

    return all_data


def get_trade_info(trade_id, table):
    mysql_info = get_config_info()
    logger = logging.getLogger('forexlogger')
    select_trade = f"""
    SELECT *
    FROM {table}
    WHERE trade_id = {trade_id}
"""

    with mysql.connect(
            host='localhost',
            user=mysql_info['user'],
            password=mysql_info['password'],
            database=mysql_info['database']
    ) as connection:
        logger.info(connection)
        with connection.cursor() as cursor:
            cursor.execute(select_trade)
            row = cursor.fetchone()
            return row


def delete_active_trade(trade_id, table):
    mysql_info = get_config_info()
    logger = logging.getLogger('forexlogger')
    delete_trade = f"""
    DELETE FROM {table}
    WHERE trade_id = {trade_id}
"""

    with mysql.connect(
            host='localhost',
            user=mysql_info['user'],
            password=mysql_info['password'],
            database=mysql_info['database']
    ) as connection:
        logger.info(connection)
        with connection.cursor() as cursor:
            cursor.execute(delete_trade)
            connection.commit()


def drop_all_tables():
    mysql_info = get_config_info()
    logger = logging.getLogger('forexlogger')
    drop_tables = """
    DROP TABLE complete
"""
    short = """
    DROP TABLE short_term_active
    """
    long = """
    DROP TABLE long_term_active
    """

    with mysql.connect(
            host='localhost',
            user=mysql_info['user'],
            password=mysql_info['password'],
            database=mysql_info['database']
    ) as connection:
        logger.info(connection)
        with connection.cursor() as cursor:
            cursor.execute(drop_tables)
            connection.commit()
            cursor.execute(short)
            connection.commit()
            cursor.execute(long)
            connection.commit()


def update_pending_complete(apikey, account_id):
    mysql_info = get_config_info()
    logger = logging.getLogger('forexlogger')
    check_complete = """
        SELECT *
        FROM complete
        WHERE units = 'N/A'
    """
    trade_ids = []
    with mysql.connect(
            host='localhost',
            user=mysql_info['user'],
            password=mysql_info['password'],
            database=mysql_info['database']
    ) as connection:
        logger.info(connection)
        with connection.cursor() as cursor:
            cursor.execute(check_complete)
            for line in cursor.fetchall():
                trade_ids.append(line[1])
    for trade_id in trade_ids:
        trade_info = oanda_api.trade_info(apikey, account_id, trade_id)
        if trade_info is not False:
            closed_trade_info = trade_info['trade']
            update_complete_trade(trade_id, 'SHORT_TERM',
                                            units=closed_trade_info['initialUnits'],
                                            margin_used=closed_trade_info['initialMarginRequired'],
                                            price=closed_trade_info['price'],
                                            profit=closed_trade_info['realizedPL'],
                                            )
        else:
            pass


def close_all_short_term(apikey, account_id):
    all_active = all_active_trades()
    logger = logging.getLogger('forexlogger')
    short_term = all_active['short_term']
    for x in short_term:
        trade_id = x[0]
        oanda_api.close_trade(apikey, account_id, trade_id)
        update_complete_trade(trade_id, 'SHORT_TERM', 'N/A', 'N/A', 'N/A', 'N/A')
        delete_active_trade(trade_id, 'short_term_active')
