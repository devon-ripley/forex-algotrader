import yagmail
import logging
import json


def get_config_info():
    f = open('data/config.json', 'r')
    profile = json.load(f)
    f.close()
    notifications_info = profile['notifications']
    return notifications_info


def send(message, subject='Forex Notification'):
    notifications_info = get_config_info()
    if notifications_info['receive_phone_num'] == '' or notifications_info['sender_email'] == '':
        return
    receiver = notifications_info['receive_phone_num']

    yag = yagmail.SMTP(notifications_info['sender_email'], password=notifications_info['sender_email_pass'])
    try:
        yag.send(
            to=receiver,
            subject=subject,
            contents=message
        )
    except:
        logging.exception('Notification "' + message + '" Failed to send')


def send_att(message, filename, subject='Forex Report'):
    notifications_info = get_config_info()
    if notifications_info['receive_email'] == '' or notifications_info['sender_email'] == '':
        return
    receiver = notifications_info['receive_email']

    yag = yagmail.SMTP(notifications_info['sender_email'], password=notifications_info['sender_email_pass'])
    try:
        yag.send(
            to=receiver,
            subject=subject,
            contents=message,
            attachments=filename,
        )
    except:
        logging.exception('Report "' + message + '" Failed to send. File: ' + filename)
